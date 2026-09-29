"""
存储服务：所有落盘操作的唯一入口。
其他模块不直接操作文件系统，统一走这里，保证目录结构一致。
"""
import json
from pathlib import Path
from typing import Any, Optional

from config import (
    ORIGINALS_DIR, PARSED_DIR, EXTRACTED_DIR,
    GRAPH_DIR, META_DIR, TASKS_DIR,
)


# ── 通用读写 ──
def _write_json(path: Path, data: Any) -> str:
    """写入 JSON，自动创建父目录，返回绝对路径字符串"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return str(path)


def _read_json(path: Path) -> Optional[Any]:
    """读取 JSON，不存在返回 None"""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 原始文件 ──
def save_original(document_id: str, filename: str, data: bytes) -> str:
    """保存原始上传文件到 storage/originals/{document_id}/"""
    path = ORIGINALS_DIR / document_id / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return str(path)


# ── 文档元数据 ──
def save_meta(document_id: str, meta: dict) -> str:
    return _write_json(META_DIR / f"{document_id}.json", meta)


def load_meta(document_id: str) -> Optional[dict]:
    return _read_json(META_DIR / f"{document_id}.json")


def list_all_meta() -> list:
    """列出所有文档元数据，按上传时间倒序"""
    result = []
    for f in META_DIR.glob("*.json"):
        m = _read_json(f)
        if m:
            result.append(m)
    return sorted(result, key=lambda x: x.get("uploaded_at", ""), reverse=True)


# ── 任务状态 ──
def save_task(task_id: str, task: dict) -> str:
    return _write_json(TASKS_DIR / f"{task_id}.json", task)


def load_task(task_id: str) -> Optional[dict]:
    return _read_json(TASKS_DIR / f"{task_id}.json")


# ── Document IR（解析中间结果）──
def save_ir(document_id: str, ir: dict) -> str:
    """保存完整 IR（blocks + images + metadata）"""
    return _write_json(PARSED_DIR / document_id / "ir.json", ir)


def load_ir(document_id: str) -> Optional[dict]:
    return _read_json(PARSED_DIR / document_id / "ir.json")


def save_blocks(document_id: str, blocks: list) -> str:
    """单独保存文本块，方便按需读取"""
    return _write_json(PARSED_DIR / document_id / "blocks.json", blocks)


def save_images(document_id: str, images: list) -> str:
    """单独保存图像信息（含 OCR 文本）"""
    return _write_json(PARSED_DIR / document_id / "images.json", images)


def save_ocr_text(document_id: str, ocr_text: str) -> str:
    """保存所有图像 OCR 文本的汇总"""
    path = PARSED_DIR / document_id / "ocr.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ocr_text, encoding="utf-8")
    return str(path)


# ── STE / SGE 抽取结果 ──
def save_ste(document_id: str, ste: dict) -> str:
    return _write_json(EXTRACTED_DIR / document_id / "ste.json", ste)


def load_ste(document_id: str) -> Optional[dict]:
    return _read_json(EXTRACTED_DIR / document_id / "ste.json")


def save_sge(document_id: str, sge: dict) -> str:
    return _write_json(EXTRACTED_DIR / document_id / "sge.json", sge)


def load_sge(document_id: str) -> Optional[dict]:
    return _read_json(EXTRACTED_DIR / document_id / "sge.json")


# ── 知识图谱 ──
def save_graph(document_id: str, graph: dict) -> str:
    return _write_json(GRAPH_DIR / document_id / "graph.json", graph)


def load_graph(document_id: str) -> Optional[dict]:
    return _read_json(GRAPH_DIR / document_id / "graph.json")


# ── 产物清单 ──
def list_artifacts(document_id: str) -> dict:
    """
    列出某文档的所有已落盘产物路径。
    前端展示"磁盘产物"用这个。
    """
    checks = {
        "original_dir":  ORIGINALS_DIR / document_id,
        "ir":            PARSED_DIR / document_id / "ir.json",
        "blocks":        PARSED_DIR / document_id / "blocks.json",
        "images":        PARSED_DIR / document_id / "images.json",
        "ocr_text":      PARSED_DIR / document_id / "ocr.txt",
        "ste":           EXTRACTED_DIR / document_id / "ste.json",
        "sge":           EXTRACTED_DIR / document_id / "sge.json",
        "graph":         GRAPH_DIR / document_id / "graph.json",
        "meta":          META_DIR / f"{document_id}.json",
    }
    artifacts = {}
    for k, v in checks.items():
        if v.exists():
            artifacts[k] = str(v)
    return artifacts