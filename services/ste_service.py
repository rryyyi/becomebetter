"""
STE (Semantic Textual Engine)
调用本地 Mistral-7B（llama.cpp OpenAI 兼容接口）做实体和关系抽取。
模型服务未启动时降级为规则 mock，保证 Demo 能跑通。
"""
import json
import re

import httpx

from config import STE_URL, STE_MODEL, MODEL_TIMEOUT, ENABLE_MODEL_CALL

PROMPT_TEMPLATE = """你是工业文档语义抽取引擎。从下面的工业维护文档中抽取实体和关系。
输出严格的 JSON 格式，不要任何解释：
{{
  "entities": [
    {{"id": "唯一ID", "name": "名称", "type": "设备|部件|故障码|PLC地址|操作步骤|工具"}}
  ],
  "relations": [
    {{"from": "实体ID或名称", "to": "实体ID或名称", "type": "导致|依赖|包含|引用|时序"}}
  ]
}}

文档内容：
{text}
"""


async def extract_text_semantics(text: str, max_chars: int = 4000) -> dict:
    """
    输入：文本内容
    输出：{"entities": [...], "relations": [...], "raw_response": "..."}
    """
    snippet = text[:max_chars]

    # 未启用模型 → 返回 mock，方便本地无 GPU 验证流程
    if not ENABLE_MODEL_CALL:
        return _mock_result(snippet)

    prompt = PROMPT_TEMPLATE.format(text=snippet)
    try:
        async with httpx.AsyncClient(timeout=MODEL_TIMEOUT) as client:
            resp = await client.post(STE_URL, json={
                "model": STE_MODEL,
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
        # 模型不可用 → 降级 mock，记录错误但不阻断流程
        result = _mock_result(snippet)
        result["error"] = str(e)
        return result


def _parse_json(content: str) -> dict:
    """从模型输出中抠出 JSON（兼容 markdown code fence）"""
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
        # 尝试匹配第一个完整 JSON 对象
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


def _mock_result(text: str) -> dict:
    """规则 mock：从文本里提取工业关键词作为实体"""
    keywords = ["制动器", "起升", "PLC", "变频器", "电机",
                "传感器", "反馈信号", "回路", "端子", "液压"]
    entities = []
    for i, kw in enumerate(keywords):
        if kw in text:
            entities.append({
                "id": f"mock_ste_{i}",
                "name": kw,
                "type": "设备" if kw == "PLC" else "部件",
            })
    return {"entities": entities, "relations": [], "mock": True}