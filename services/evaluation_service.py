"""可复现的诊断评估：支持 JSONL 测试集，默认提供 smoke 指标。"""
import json
import uuid
from datetime import datetime
from pathlib import Path

from config import REPORTS_DIR
from services.diagnosis_service import diagnose
from models.schemas import DiagnosisRequest


async def evaluate(dataset_path: str | None = None) -> dict:
    path = Path(dataset_path) if dataset_path else Path("tests/data/diagnosis.jsonl")
    cases = []
    if path.exists():
        cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    failures = []
    hits = 0
    for case in cases:
        result = await diagnose(DiagnosisRequest(symptom=case["symptom"], top_k=5))
        names = " ".join(c["cause"] for c in result["causes"])
        ok = any(term.lower() in names.lower() for term in case.get("expected", []))
        hits += int(ok)
        if not ok:
            failures.append({"symptom": case["symptom"], "expected": case.get("expected", []), "actual": names[:500]})
    metrics = {"case_count": float(len(cases)), "diagnosis_recall": hits / len(cases) if cases else 0.0,
               "evidence_grounding": sum(bool(c.get("evidence")) for c in (result.get("causes", []) if cases else [])) / max(1, len(result.get("causes", [])) if cases else 1)}
    report = {"evaluation_id": str(uuid.uuid4()), "metrics": metrics, "failures": failures,
              "recommendations": ["为失败案例补充手册证据或同义词"] if failures else [], "created_at": datetime.now().isoformat()}
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"evaluation-{report['evaluation_id']}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
