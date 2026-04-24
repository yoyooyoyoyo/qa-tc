from __future__ import annotations

import json
import re
from typing import Any

from app.core.llm_client import BaseLLMClient, get_llm_client
from app.prompts.extractor_prompt import build_requirement_extraction_prompt
from app.schemas.requirement import Requirement

MAX_DOCUMENT_CHARS = 20000


def extract_requirements_from_text(
    document_text: str,
    llm_client: BaseLLMClient | None = None,
) -> list[Requirement]:
    normalized_text = document_text.strip()

    if not normalized_text:
        raise ValueError("Document text is empty.")

    trimmed_text = normalized_text[:MAX_DOCUMENT_CHARS]
    prompt = build_requirement_extraction_prompt(trimmed_text)

    client = llm_client or get_llm_client()
    raw_output = client.extract_requirements(document_text=trimmed_text, prompt=prompt)

    raw_items = _normalize_llm_output(raw_output)
    requirements = [Requirement.model_validate(item) for item in raw_items]

    return requirements


def _normalize_llm_output(raw_output: Any) -> list[dict[str, Any]]:
    if isinstance(raw_output, list):
        return raw_output

    if isinstance(raw_output, dict):
        if "requirements" in raw_output and isinstance(raw_output["requirements"], list):
            return raw_output["requirements"]
        return [raw_output]

    if isinstance(raw_output, str):
        parsed = _parse_json_string(raw_output)
        return _normalize_llm_output(parsed)

    raise ValueError("Unsupported LLM output format.")


def _parse_json_string(raw_text: str) -> Any:
    text = raw_text.strip()

    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM output is not valid JSON: {exc}") from exc
