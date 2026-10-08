"""
解析主流程：每个阶段完成后立即落盘，最后更新任务状态。
流程：文件识别 → Document IR → STE → SGE → 知识图谱
"""
import traceback
from datetime import datetime

from services import storage_service as store
from services.extractor_pdf import extract_pdf
from services.extractor_image import extract_image
from services.ste_service import extract_text_semantics
from services.sge_service import extract_graphical_semantics
from services.graph_builder import build_graph
from services.index_service import index_document
from services.extractor_structured import extract_docx, extract_xlsx, extract_archive


async def run_parse_pipeline(document_id: str, task_id: str,
                              file_path: str, filename: str):
    """异步解析流水线。所有中间产物落盘到 storage/ 对应目录。"""

    def _update(status, stage, progress, message="", error=None):
        """更新任务状态并落盘"""
        task = {
            "task_id": task_id,
            "document_id": document_id,
            "status": status,
            "stage": stage,
            "progress": progress,
            "message": message,
            "error": error,
            "artifacts": store.list_artifacts(document_id),
            "updated_at": datetime.now().isoformat(),
        }
        store.save_task(task_id, task)

    try:
        ext = filename.rsplit(".", 1)[-1].lower()

        # ── 阶段 1：文件识别 ──
        _update("parsing", "file_type_detect", 0.05, f"识别文件类型: {ext}")

        # ── 阶段 2：Document IR 提取 ──
        _update("parsing", "text_extract", 0.15, "提取文本和图像")
        if ext == "pdf":
            ir = extract_pdf(file_path)
        elif ext in ("png", "jpg", "jpeg", "tiff", "bmp"):
            ir = extract_image(file_path)
        elif ext == "docx":
            ir = extract_docx(file_path)
        elif ext in ("xlsx", "xlsm"):
            ir = extract_xlsx(file_path)
        elif ext in ("zip", "eplan", "tia"):
            ir = extract_archive(file_path) if ext == "zip" else extract_archive(file_path)
        else:
            raise ValueError(f"暂不支持的文件类型: {ext}")

        # 落盘 IR
        store.save_ir(document_id, ir)
        store.save_blocks(document_id, ir["blocks"])
        store.save_images(document_id, ir["images"])
        index_document(document_id, ir)

        # 汇总 OCR 文本落盘
        ocr_text = "\n".join(img.get("ocr_text", "") for img in ir["images"])
        if ocr_text.strip():
            store.save_ocr_text(document_id, ocr_text)

        _update("parsing", "text_extract", 0.30,
                f"提取完成: {len(ir['blocks'])} 文本块, {len(ir['images'])} 图像")

        # ── 阶段 3：STE 文本语义引擎 ──
        _update("extracting", "ste", 0.40, "STE 文本语义抽取中")
        full_text = "\n".join(b["text"] for b in ir["blocks"] if b.get("text"))
        ste_result = await extract_text_semantics(full_text)
        store.save_ste(document_id, ste_result)   # 立即落盘

        _update("extracting", "ste", 0.60,
                f"STE 完成: {len(ste_result.get('entities', []))} 实体")

        # ── 阶段 4：SGE 图形语义引擎 ──
        _update("extracting", "sge", 0.65, "SGE 图形语义抽取中")
        sge_results = []
        for img in ir["images"]:
            if img.get("ocr_text", "").strip():
                r = await extract_graphical_semantics(
                    img["ocr_text"], context=full_text[:1500]
                )
                sge_results.append(r)

        # 合并所有图像的 SGE 结果
        sge_merged = {
            "entities": [e for r in sge_results for e in r.get("entities", [])],
            "relations": [e for r in sge_results for e in r.get("relations", [])],
        }
        store.save_sge(document_id, sge_merged)   # 落盘

        _update("extracting", "sge", 0.85,
                f"SGE 完成: {len(sge_merged['entities'])} 实体")

        # ── 阶段 5：知识图谱构建 ──
        _update("extracting", "graph_build", 0.90, "构建知识图谱")
        graph = build_graph(document_id, ste_result, sge_merged)
        store.save_graph(document_id, graph)      # 落盘

        # 更新元数据中的解析状态
        meta = store.load_meta(document_id) or {}
        meta["parse_status"] = "completed"
        store.save_meta(document_id, meta)

        # ── 完成 ──
        _update("completed", "done", 1.0,
                f"完成: {graph['stats']['entity_count']} 实体, "
                f"{graph['stats']['relation_count']} 关系")

    except Exception:
        # 出错时记录完整堆栈，更新元数据状态
        meta = store.load_meta(document_id) or {}
        meta["parse_status"] = "failed"
        store.save_meta(document_id, meta)
        _update("failed", "error", 0.0, "解析失败", error=traceback.format_exc())
