"""合并 STE + SGE 结果，构建统一知识图谱"""
from typing import List


def build_graph(document_id: str, ste: dict, sge: dict) -> dict:
    """
    输出：
    {
      "document_id": "...",
      "entities": [{"id", "name", "type", "source"}],
      "relations": [{"from", "to", "type", "source"}],
      "stats": {"entity_count": N, "relation_count": M}
    }
    """
    entity_map = {}          # 用 id/name 做去重键
    relations: List[dict] = []

    # 先合并 STE 实体
    for e in ste.get("entities", []):
        key = e.get("id") or e.get("name")
        if key:
            entity_map[key] = {**e, "source": "ste"}

    # 再合并 SGE 实体，同 key 时标记为双来源
    for e in sge.get("entities", []):
        key = e.get("id") or e.get("name")
        if key:
            if key in entity_map:
                entity_map[key]["source"] = "ste+sge"
            else:
                entity_map[key] = {**e, "source": "sge"}

    # 合并关系
    for r in ste.get("relations", []):
        relations.append({**r, "source": "ste"})
    for r in sge.get("relations", []):
        relations.append({**r, "source": "sge"})

    return {
        "document_id": document_id,
        "entities": list(entity_map.values()),
        "relations": relations,
        "stats": {
            "entity_count": len(entity_map),
            "relation_count": len(relations),
        },
    }