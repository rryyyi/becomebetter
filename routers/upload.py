"""上传接口：流式写入 + 计算 hash + 后台解析"""
import hashlib
import uuid
from datetime import datetime

import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException

from config import ORIGINALS_DIR
from models.schemas import UploadResponse
from services import storage_service as store
from services.parse_service import run_parse_pipeline

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])


@router.post("/", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    device_id: str = Form("QC-01"),
    doc_type: str = Form("manual"),
):
    """
    上传文件：
    1. 流式写入磁盘，同步计算 SHA256
    2. 生成 document_id / task_id
    3. 后台启动解析任务
    4. 立即返回
    """
    if not file.filename:
        raise HTTPException(400, "文件名为空")

    document_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    # 保存路径：storage/originals/{document_id}/{原始文件名}
    save_dir = ORIGINALS_DIR / document_id
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / file.filename

    # 流式写入，同时计算 hash（避免二次读盘）
    file_hash = hashlib.sha256()
    file_size = 0
    async with aiofiles.open(save_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):   # 1MB 分片
            file_hash.update(chunk)
            file_size += len(chunk)
            await f.write(chunk)

    # 保存元数据
    meta = {
        "document_id": document_id,
        "file_name": file.filename,
        "file_size": file_size,
        "file_hash": file_hash.hexdigest(),
        "device_id": device_id,
        "doc_type": doc_type,
        "uploaded_at": datetime.now().isoformat(),
        "parse_status": "pending",
        "original_path": str(save_path),
    }
    store.save_meta(document_id, meta)

    # 初始化任务状态
    store.save_task(task_id, {
        "task_id": task_id,
        "document_id": document_id,
        "status": "pending",
        "stage": "queued",
        "progress": 0.0,
        "message": "已入队，等待解析",
        "artifacts": {},
        "updated_at": datetime.now().isoformat(),
    })

    # 后台执行解析
    background_tasks.add_task(
        run_parse_pipeline, document_id, task_id, str(save_path), file.filename
    )

    return UploadResponse(
        document_id=document_id,
        file_name=file.filename,
        file_size=file_size,
        file_hash=file_hash.hexdigest(),
        parse_task_id=task_id,
        duplicate=False,
    )