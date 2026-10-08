from fastapi import APIRouter
from models.schemas import EvaluationRequest, EvaluationResponse
from services.evaluation_service import evaluate

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation(request: EvaluationRequest):
    return await evaluate(request.dataset_path)
