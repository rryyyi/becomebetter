"""持久化混合索引：轻量 token 检索 + 图关系 + 实时数据适配器。"""
import json
import math
import re
from collections import Counter
from datetime import datetime
from typing import Any

from config import INDEX_DIR

INDEX_FILE = INDEX_DIR / "chunks.json"
RUNTIME_FILE = INDEX_DIR / "runtime.json"


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_.:-]+|[\u4e00-\u9fff]", (text or "").lower())


def _read(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def index_document(document_id: str, ir: dict) -> int:
    items = [x for x in _read(INDEX_FILE, []) if x.get("document_id") != document_id]
    for i, block in enumerate(ir.get("blocks", [])):
        text = block.get("text", "").strip()
        if not text:
            continue
        items.append({
            "chunk_id": f"{document_id}:text:{i}", "document_id": document_id,
            "text": text, "tokens": _tokens(text), "source_type": "document",
            "page": block.get("page"), "bbox": block.get("bbox"),
        })
    for i, image in enumerate(ir.get("images", [])):
        text = image.get("ocr_text", "").strip()
        if text:
            items.append({
                "chunk_id": f"{document_id}:image:{i}", "document_id": document_id,
                "text": text, "tokens": _tokens(text), "source_type": "ocr",
                "page": image.get("page"), "bbox": image.get("bbox"),
            })
    _write(INDEX_FILE, items)
    return len(items)


def search(query: str, top_k: int = 12) -> list[dict]:
    docs = _read(INDEX_FILE, [])
    q = _tokens(query)
    if not q or not docs:
        return []
    df = Counter(t for d in docs for t in set(d.get("tokens", [])))
    scored = []
    n = len(docs)
    for d in docs:
        counts = Counter(d.get("tokens", []))
        score = 0.0
        for token in q:
            if token in counts:
                idf = math.log((n + 1) / (df[token] + 1)) + 1
                score += idf * (counts[token] / max(1, len(d.get("tokens", []))))
        if score:
            item = dict(d)
            item["score"] = round(score, 6)
            scored.append(item)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]


def save_runtime(device_id: str, points: dict[str, Any]) -> None:
    runtime = _read(RUNTIME_FILE, {})
    runtime[device_id] = {"points": points, "updated_at": datetime.now().isoformat()}
    _write(RUNTIME_FILE, runtime)


def get_runtime(device_id: str | None) -> dict[str, Any]:
    if not device_id:
        return {}
    return _read(RUNTIME_FILE, {}).get(device_id, {}).get("points", {})
