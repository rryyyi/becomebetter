"""API 请求/响应数据模型"""
from pydantic import BaseModel
from typing import Optional, Dict, List


class UploadResponse(BaseModel):
    """上传接口返回"""
    document_id: str
    file_name: str
    file_size: int
    file_hash: str
    parse_task_id: str
    duplicate: bool = False


class TaskStatus(BaseModel):
    """解析任务状态"""
    task_id: str
    document_id: str
    status: str          # pending / parsing / extracting / completed / failed
    stage: Optional[str] = None   # file_type_detect / text_extract / ste / sge / graph_build / done
    progress: float = 0.0
    message: Optional[str] = None
    error: Optional[str] = None
    artifacts: Optional[Dict[str, str]] = None   # 产物文件路径清单
    updated_at: Optional[str] = None