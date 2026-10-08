"""API 请求/响应数据模型"""
from pydantic import BaseModel
from typing import Optional, Dict, List, Any


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


class Evidence(BaseModel):
    source_type: str
    source_id: str
    quote: str
    page: Optional[int] = None
    location: Optional[Dict[str, Any]] = None
    score: float = 0.0


class DiagnosisRequest(BaseModel):
    symptom: str
    device_id: Optional[str] = None
    context: Dict[str, Any] = {}
    top_k: int = 8


class CandidateCause(BaseModel):
    rank: int
    cause: str
    possibility: float
    status: str = "待验证"
    evidence: List[Evidence] = []
    verification_steps: List[str] = []
    rationale: str = ""


class DiagnosisResponse(BaseModel):
    diagnosis_id: str
    normalized_symptom: str
    query_variants: List[str]
    causes: List[CandidateCause]
    retrieval: Dict[str, Any] = {}
    created_at: str


class EvaluationRequest(BaseModel):
    dataset_path: Optional[str] = None


class EvaluationResponse(BaseModel):
    evaluation_id: str
    metrics: Dict[str, float]
    failures: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    created_at: str
