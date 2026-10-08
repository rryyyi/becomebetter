"""诊断型 RAG：查询标准化、混合召回、证据绑定、规则排除和本地模型生成。"""
import json
import re
import uuid
from datetime import datetime

import httpx

from config import ENABLE_MODEL_CALL, STE_URL, STE_MODEL, MODEL_TIMEOUT, REPORTS_DIR
from services import index_service as index
from services import storage_service as store


def _normalize(symptom: str) -> tuple[str, list[str]]:
    text = re.sub(r"\s+", " ", symptom.strip())
    variants = [text]
    replacements = {"不转": "无法启动", "不动": "无法动作", "异响": "异常噪声",
                    "发热": "温升过高", "跳闸": "保护动作", "报警": "故障报警"}
    for source, target in replacements.items():
        if source in text:
            variants.append(text.replace(source, target))
    return text, list(dict.fromkeys(variants))


def _runtime_status(text: str, runtime: dict) -> str:
    for key, value in runtime.items():
        if str(key).lower() in text.lower() and str(value).lower() in {"0", "false", "正常", "ok"}:
            return "已排除"
    return "待验证"


async def _model_candidates(query: str, evidence: list[dict]) -> list[dict]:
    if not ENABLE_MODEL_CALL:
        return []
    context = "\n".join(f"[{e['chunk_id']}] {e['text']}" for e in evidence[:8])
    prompt = ("根据工业故障现象和证据，输出严格JSON数组。每项包含 cause, possibility(0到1), "
              "rationale, verification_steps。只能使用证据支持的原因。\n现象：" + query + "\n证据：" + context)
    try:
        async with httpx.AsyncClient(timeout=MODEL_TIMEOUT) as client:
            response = await client.post(STE_URL, json={"model": STE_MODEL,
                "messages": [{"role": "user", "content": prompt}], "temperature": 0.1,
                "max_tokens": 1600})
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            match = re.search(r"\[.*\]", content, re.S)
            return json.loads(match.group(0)) if match else []
    except Exception:
        return []


async def diagnose(request) -> dict:
    normalized, variants = _normalize(request.symptom)
    hits = []
    for variant in variants:
        hits.extend(index.search(variant, top_k=8))
    dedup = {h["chunk_id"]: h for h in hits}
    evidence = sorted(dedup.values(), key=lambda x: x.get("score", 0), reverse=True)
    runtime = index.get_runtime(request.device_id)
    candidates = await _model_candidates(normalized, evidence)
    if not candidates:
        for hit in evidence[:request.top_k]:
            sentence = hit["text"].split("\n")[0][:180]
            candidates.append({"cause": sentence, "possibility": min(0.95, 0.35 + hit["score"]),
                               "rationale": "检索证据与症状存在术语匹配", "verification_steps": [
                               "核对对应设备点位/报警记录", "按手册步骤进行隔离验证"]})
    if not candidates:
        candidates.append({"cause": "当前知识库没有足够证据支持具体原因", "possibility": 0.0,
                           "rationale": "请先上传相关设备手册、报警表或维修记录，再重新诊断。",
                           "verification_steps": ["确认设备型号和故障现象", "上传对应手册或现场记录"]})
    causes = []
    for rank, item in enumerate(sorted(candidates, key=lambda x: x.get("possibility", 0), reverse=True)[:request.top_k], 1):
        text = item.get("cause", "未知原因")
        bound = [e for e in evidence if any(t in e["text"] for t in re.findall(r"[\u4e00-\u9fffA-Za-z0-9_.:-]{2,}", text)[:4])][:3]
        causes.append({"rank": rank, "cause": text, "possibility": round(float(item.get("possibility", 0)), 3),
                       "status": _runtime_status(text, runtime), "rationale": item.get("rationale", ""),
                       "verification_steps": item.get("verification_steps", []), "evidence": [
                           {"source_type": e.get("source_type", "document"), "source_id": e["chunk_id"],
                            "quote": e["text"][:300], "page": e.get("page"), "location": {"bbox": e.get("bbox")},
                            "score": e.get("score", 0)} for e in bound]})
    result = {"diagnosis_id": str(uuid.uuid4()), "normalized_symptom": normalized,
              "query_variants": variants, "causes": causes,
              "retrieval": {"evidence_count": len(evidence), "runtime_points": runtime},
              "created_at": datetime.now().isoformat()}
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"diagnosis-{result['diagnosis_id']}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
