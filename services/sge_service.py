"""
SGE (Semantic Graphical Engine)
把图像 OCR 文本 + 上下文送 Pixtral-12B 做视觉语义理解。
模型未启动时降级 mock。
"""
import json
import re

import httpx

from config import SGE_URL, SGE_MODEL, MODEL_TIMEOUT, ENABLE_MODEL_CALL

PROMPT_TEMPLATE = """你是工业图纸语义理解引擎。以下是工业图纸/表格中识别出的文字。
结合上下文，理解其含义，抽取实体和关系。
输出严格的 JSON 格式：
{{
  "entities": [{{"id": "...", "name": "...", "type": "..."}}],
  "relations": [{{"from": "...", "to": "...", "type": "..."}}]
}}

上下文（文档其他部分）：
{context}

图纸/表格文字：
{ocr_text}
"""


async def extract_graphical_semantics(ocr_text: str, context: str = "") -> dict:
    """对单张图像的 OCR 文本做语义抽取"""
    if not ocr_text.strip():
        return {"entities": [], "relations": [], "empty": True}

    if not ENABLE_MODEL_CALL:
        return _mock_result(ocr_text)

    prompt = PROMPT_TEMPLATE.format(
        context=context[:1500], ocr_text=ocr_text[:2000]
    )
    try:
        async with httpx.AsyncClient(timeout=MODEL_TIMEOUT) as client:
            resp = await client.post(SGE_URL, json={
                "model": SGE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 2048,
            })
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = _parse_json(content)
            parsed["raw_response"] = content
            return parsed
    except Exception as e:
        result = _mock_result(ocr_text)
        result["error"] = str(e)
        return result


def _parse_json(content: str) -> dict:
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    try:
        data = json.loads(content)
        return {
            "entities": data.get("entities", []),
            "relations": data.get("relations", []),
        }
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                return {
                    "entities": data.get("entities", []),
                    "relations": data.get("relations", []),
                }
            except json.JSONDecodeError:
                pass
    return {"entities": [], "relations": [], "parse_error": True}


def _mock_result(ocr_text: str) -> dict:
    """规则 mock：从 OCR 文本里找 PLC 地址和端子编号"""
    entities = []

    # 匹配 PLC 地址，如 I0.1, Q0.2, M10.0
    for i, m in enumerate(re.findall(r"\b([IQM]\d+\.\d+)\b", ocr_text)):
        entities.append({"id": f"mock_addr_{i}", "name": m, "type": "PLC地址"})

    # 匹配端子编号，如 Y12, K12, X1
    for i, m in enumerate(re.findall(r"\b([YKXQ]\d{1,3})\b", ocr_text)):
        entities.append({"id": f"mock_term_{i}", "name": m, "type": "端子"})

    return {"entities": entities, "relations": [], "mock": True}