from fastapi import APIRouter
from models.schemas import DiagnosisRequest, DiagnosisResponse
from services.diagnosis_service import diagnose

router = APIRouter(prefix="/api/v1/diagnosis", tags=["diagnosis"])


@router.post("/", response_model=DiagnosisResponse)
async def run_diagnosis(request: DiagnosisRequest):
    return await diagnose(request)
