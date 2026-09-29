"""文档、产物、图谱查询接口"""
from fastapi import APIRouter, HTTPException

from services import storage_service as store

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.get("/")
async def list_documents():
    """列出所有已上传文档"""
    return store.list_all_meta()


@router.get("/{document_id}")
async def get_document(document_id: str):
    """获取文档元数据 + 产物清单"""
    meta = store.load_meta(document_id)
    if not meta:
        raise HTTPException(404, "文档不存在")
    return {
        "meta": meta,
        "artifacts": store.list_artifacts(document_id),
    }


@router.get("/{document_id}/ir")
async def get_document_ir(document_id: str):
    ir = store.load_ir(document_id)
    if not ir:
        raise HTTPException(404, "IR 不存在")
    return ir


@router.get("/{document_id}/ste")
async def get_ste(document_id: str):
    return store.load_ste(document_id) or {}


@router.get("/{document_id}/sge")
async def get_sge(document_id: str):
    return store.load_sge(document_id) or {}


@router.get("/{document_id}/graph")
async def get_document_graph(document_id: str):
    graph = store.load_graph(document_id)
    if not graph:
        raise HTTPException(404, "图谱不存在")
    return graph