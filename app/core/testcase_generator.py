from __future__ import annotations

import json
import re
from typing import Any

from app.core.llm_client import BaseLLMClient, get_llm_client
from app.core.quality import improve_testcase_quality
from app.prompts.testcase_prompt import build_testcase_generation_prompt
from app.schemas.analysis import RequirementAnalysisResult
from app.schemas.requirement import Requirement
from app.schemas.testcase import TestCase


def generate_testcases_from_requirements(
    requirements: list[Requirement],
    perspectives: list[str] | None = None,
    analysis: RequirementAnalysisResult | None = None,
    llm_client: BaseLLMClient | None = None,
) -> list[TestCase]:
    if not requirements:
        raise ValueError("requirements is required.")

    selected_perspectives = perspectives or ["PM", "DEV", "QA"]
    prompt = build_testcase_generation_prompt(
        requirements,
        selected_perspectives,
        analysis=analysis,
    )

    client = llm_client or get_llm_client()
    raw_output = client.generate_testcases(
        requirements=requirements,
        perspectives=selected_perspectives,
        prompt=prompt,
    )

    raw_items = _normalize_llm_output(raw_output)
    testcases = [TestCase.model_validate(item) for item in raw_items]
    return improve_testcase_quality(testcases, requirements)


def _normalize_llm_output(raw_output: Any) -> list[dict[str, Any]]:
    if isinstance(raw_output, list):
        return raw_output

    if isinstance(raw_output, dict):
        if "testcases" in raw_output and isinstance(raw_output["testcases"], list):
            return raw_output["testcases"]
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
