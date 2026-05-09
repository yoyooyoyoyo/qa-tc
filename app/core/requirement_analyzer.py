from __future__ import annotations

import json
import re
from typing import Any

from app.core.llm_client import BaseLLMClient, get_llm_client
from app.core.policy_loader import load_policy_context
from app.prompts.analysis_prompt import build_requirement_analysis_prompt
from app.schemas.analysis import RequirementAnalysisResult
from app.schemas.requirement import Requirement


def analyze_requirements(
    requirements: list[Requirement],
    policy_context: str = "",
    llm_client: BaseLLMClient | None = None,
) -> RequirementAnalysisResult:
    if not requirements:
        raise ValueError("requirements is required.")

    resolved_policy_context = policy_context or load_policy_context(
        json.dumps([requirement.model_dump(mode="json") for requirement in requirements], ensure_ascii=False)
    ).text
    prompt = build_requirement_analysis_prompt(
        requirements,
        policy_context=resolved_policy_context,
    )
    client = llm_client or get_llm_client()
    raw_output = client.analyze_requirements(requirements=requirements, prompt=prompt)
    return RequirementAnalysisResult.model_validate(_normalize_llm_output(raw_output))


def _normalize_llm_output(raw_output: Any) -> dict[str, Any]:
    if isinstance(raw_output, dict):
        return raw_output

    if isinstance(raw_output, str):
        return _parse_json_string(raw_output)

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
