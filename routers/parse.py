"""任务状态查询接口"""
from fastapi import APIRouter, HTTPException

from models.schemas import TaskStatus
from services import storage_service as store

router = APIRouter(prefix="/api/v1/parse", tags=["parse"])


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    task = store.load_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return TaskStatus(**task)