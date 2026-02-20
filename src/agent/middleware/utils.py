import json
from typing import TypedDict


class KnowledgeChunk(TypedDict, total=False):
    document_title: str
    page_number: int


class KnowledgeToolResult(TypedDict):
    chunks: list[KnowledgeChunk]


def parse_json_content(content: str) -> dict | None:
    try:
        data = json.loads(content)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def extract_float_field(data: dict, field_name: str) -> float | None:
    value = data.get(field_name)
    if isinstance(value, int | float):
        return float(value)
    return None
