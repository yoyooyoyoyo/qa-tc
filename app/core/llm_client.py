from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any

import requests

from app.schemas.requirement import Requirement


class BaseLLMClient(ABC):
    @abstractmethod
    def extract_requirements(self, *, document_text: str, prompt: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def generate_testcases(
        self,
        *,
        requirements: list[Requirement],
        perspectives: list[str],
        prompt: str,
    ) -> Any:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    실제 LLM 연결 전 임시로 동작시키는 mock/rule-based 클라이언트.
    문서에서 헤더/키워드를 대충 뽑아서 requirement 형태로 반환한다.
    """

    def extract_requirements(self, *, document_text: str, prompt: str) -> Any:
        return _rule_based_requirement_extraction(document_text)

    def generate_testcases(
        self,
        *,
        requirements: list[Requirement],
        perspectives: list[str],
        prompt: str,
    ) -> Any:
        return _rule_based_testcase_generation(requirements, perspectives)


class ExternalLLMClient(BaseLLMClient):
    """
    실제 LLM 연결용 뼈대.
    나중에 여기서 OpenAI / Azure OpenAI / Anthropic / Gemini 등으로 교체하면 된다.
    """

    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "external")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "")

    def extract_requirements(self, *, document_text: str, prompt: str) -> Any:
        raise NotImplementedError(
            "ExternalLLMClient is a skeleton only. "
            "Replace this method with your actual LLM SDK/API call."
        )

    def generate_testcases(
        self,
        *,
        requirements: list[Requirement],
        perspectives: list[str],
        prompt: str,
    ) -> Any:
        raise NotImplementedError(
            "ExternalLLMClient is a skeleton only. "
            "Replace this method with your actual LLM SDK/API call."
        )


class OpenAILLMClient(BaseLLMClient):
    """
    OpenAI Responses API 연결 클라이언트.
    LLM_PROVIDER=openai, OPENAI_API_KEY, OPENAI_MODEL 환경변수로 활성화한다.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

    def extract_requirements(self, *, document_text: str, prompt: str) -> Any:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "너는 기획자, 개발자, QA 관점으로 기획서를 분석하는 "
                        "요구사항 추출 에이전트다. 반드시 JSON 스키마를 준수한다."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "requirement_extraction_result",
                    "strict": True,
                    "schema": REQUIREMENT_EXTRACTION_JSON_SCHEMA,
                }
            },
        }

        response = requests.post(
            f"{self.base_url.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        return _extract_response_text(response.json())

    def generate_testcases(
        self,
        *,
        requirements: list[Requirement],
        perspectives: list[str],
        prompt: str,
    ) -> Any:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "너는 기획자, 개발자, QA 관점으로 요구사항을 테스트케이스로 "
                        "구조화하는 QA 리드다. 반드시 JSON 스키마를 준수한다."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "testcase_generation_result",
                    "strict": True,
                    "schema": TESTCASE_GENERATION_JSON_SCHEMA,
                }
            },
        }

        response = requests.post(
            f"{self.base_url.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        return _extract_response_text(response.json())


def get_llm_client() -> BaseLLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()

    if provider == "mock":
        return MockLLMClient()

    if provider == "openai":
        return OpenAILLMClient()

    if provider == "external":
        return ExternalLLMClient()

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


REQUIREMENT_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "feature_id": {"type": "string"},
                    "feature_name": {"type": "string"},
                    "platform": {"type": "array", "items": {"type": "string"}},
                    "actor": {"type": "string"},
                    "entry_point": {"type": "string"},
                    "preconditions": {"type": "array", "items": {"type": "string"}},
                    "business_rules": {"type": "array", "items": {"type": "string"}},
                    "states": {"type": "array", "items": {"type": "string"}},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "open_questions": {"type": "array", "items": {"type": "string"}},
                    "source_section": {"type": "string"},
                },
                "required": [
                    "feature_id",
                    "feature_name",
                    "platform",
                    "actor",
                    "entry_point",
                    "preconditions",
                    "business_rules",
                    "states",
                    "dependencies",
                    "open_questions",
                    "source_section",
                ],
            },
        }
    },
    "required": ["requirements"],
}


TESTCASE_GENERATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "testcases": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "testcase_id": {"type": "string"},
                    "requirement_id": {"type": "string"},
                    "perspective": {"type": "string"},
                    "priority": {"type": "string"},
                    "test_type": {"type": "string"},
                    "title": {"type": "string"},
                    "preconditions": {"type": "array", "items": {"type": "string"}},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "test_data": {"type": "string"},
                    "expected_result": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": [
                    "testcase_id",
                    "requirement_id",
                    "perspective",
                    "priority",
                    "test_type",
                    "title",
                    "preconditions",
                    "steps",
                    "test_data",
                    "expected_result",
                    "notes",
                ],
            },
        }
    },
    "required": ["testcases"],
}


def _extract_response_text(response_json: dict[str, Any]) -> str:
    if isinstance(response_json.get("output_text"), str):
        return response_json["output_text"]

    text_parts: list[str] = []
    for output_item in response_json.get("output", []):
        for content_item in output_item.get("content", []):
            if content_item.get("type") == "output_text":
                text_parts.append(content_item.get("text", ""))

    if text_parts:
        return "".join(text_parts)

    raise ValueError("OpenAI response did not include output text.")


def _rule_based_requirement_extraction(document_text: str) -> list[dict[str, Any]]:
    cleaned_lines = [_clean_line(line) for line in document_text.splitlines()]
    lines = [line for line in cleaned_lines if line]

    feature_candidates = _extract_feature_candidates(lines)
    platforms = _detect_platforms(document_text)
    business_rules = _extract_business_rules(lines)
    states = _extract_states(lines)
    dependencies = _extract_dependencies(lines)

    if not feature_candidates:
        feature_candidates = ["문서 전체 기능"]

    requirements: list[dict[str, Any]] = []
    for idx, feature_name in enumerate(feature_candidates[:8], start=1):
        requirements.append(
            {
                "feature_id": f"REQ-{idx:03d}",
                "feature_name": feature_name,
                "platform": platforms,
                "actor": "사용자",
                "entry_point": "",
                "preconditions": [],
                "business_rules": business_rules[:5],
                "states": states[:5],
                "dependencies": dependencies[:5],
                "open_questions": ["세부 정책/예외 케이스 추가 확인 필요"],
                "source_section": feature_name,
            }
        )

    return requirements


def _clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    return line


def _extract_feature_candidates(lines: list[str]) -> list[str]:
    candidates: list[str] = []

    for line in lines:
        normalized = re.sub(r"^[\-\*\d\.\)\s]+", "", line).strip()

        if not normalized:
            continue

        if len(normalized) > 60:
            continue

        if "\t" in normalized or "|" in normalized:
            continue

        if normalized.lower().startswith("[page"):
            continue

        if normalized.lower().startswith("[sheet:"):
            continue

        candidates.append(normalized)

    unique: list[str] = []
    seen: set[str] = set()

    for item in candidates:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)

    return unique[:10]


def _detect_platforms(text: str) -> list[str]:
    upper_text = text.upper()
    platforms: list[str] = []

    mappings = {
        "WEB": ["WEB", "웹"],
        "APP": ["APP", "앱", "모바일"],
        "ADMIN": ["ADMIN", "어드민", "관리자"],
        "CMS": ["CMS"],
        "CRM": ["CRM"],
        "PMS": ["PMS"],
    }

    for platform, keywords in mappings.items():
        if any(keyword in upper_text or keyword in text for keyword in keywords):
            platforms.append(platform)

    return platforms


def _extract_business_rules(lines: list[str]) -> list[str]:
    keywords = ["필수", "불가", "가능", "노출", "제한", "예외", "오류", "중복", "저장", "수정", "삭제"]
    matched: list[str] = []

    for line in lines:
        if any(keyword in line for keyword in keywords):
            matched.append(line)

    return matched[:10]


def _extract_states(lines: list[str]) -> list[str]:
    keywords = ["상태", "대기", "완료", "취소", "실패", "성공", "예약확정", "예약가능", "예약불가"]
    matched: list[str] = []

    for line in lines:
        if any(keyword in line for keyword in keywords):
            matched.append(line)

    return matched[:10]


def _extract_dependencies(lines: list[str]) -> list[str]:
    keywords = ["API", "서버", "DB", "백엔드", "프론트", "배치", "어드민", "외부", "연동"]
    matched: list[str] = []

    for line in lines:
        if any(keyword.lower() in line.lower() for keyword in keywords):
            matched.append(line)

    return matched[:10]


def _rule_based_testcase_generation(
    requirements: list[Requirement],
    perspectives: list[str],
) -> list[dict[str, Any]]:
    testcases: list[dict[str, Any]] = []
    counter = 1

    for requirement in requirements:
        for perspective in perspectives:
            perspective_upper = perspective.upper()
            testcases.append(
                {
                    "testcase_id": f"TC-{counter:03d}",
                    "requirement_id": requirement.feature_id,
                    "perspective": perspective_upper,
                    "priority": _guess_priority(requirement, perspective_upper),
                    "test_type": _guess_test_type(requirement, perspective_upper),
                    "title": _build_testcase_title(requirement, perspective_upper),
                    "preconditions": requirement.preconditions,
                    "steps": _build_test_steps(requirement, perspective_upper),
                    "test_data": _build_test_data(requirement),
                    "expected_result": _build_expected_result(requirement, perspective_upper),
                    "notes": _build_notes(requirement),
                }
            )
            counter += 1

    return testcases


def _guess_priority(requirement: Requirement, perspective: str) -> str:
    high_keywords = ["결제", "로그인", "예약", "삭제", "권한", "인증", "오류"]
    text = f"{requirement.feature_name} {' '.join(requirement.business_rules)}"

    if perspective == "QA" or any(keyword in text for keyword in high_keywords):
        return "High"

    return "Medium"


def _guess_test_type(requirement: Requirement, perspective: str) -> str:
    if perspective == "DEV" and requirement.dependencies:
        return "Integration"

    if perspective == "PM":
        return "Policy"

    if requirement.states:
        return "State"

    return "Functional"


def _build_testcase_title(requirement: Requirement, perspective: str) -> str:
    suffix_by_perspective = {
        "PM": "정책/기획 의도 충족 여부 확인",
        "DEV": "구현 조건 및 의존 요소 정상 동작 확인",
        "QA": "사용자 시나리오 정상/예외 동작 확인",
    }
    suffix = suffix_by_perspective.get(perspective, "동작 확인")
    return f"{requirement.feature_name} - {suffix}"


def _build_test_steps(requirement: Requirement, perspective: str) -> list[str]:
    steps = []

    if requirement.entry_point:
        steps.append(f"{requirement.entry_point} 경로로 진입한다.")
    else:
        steps.append(f"{requirement.feature_name} 기능에 진입한다.")

    if perspective == "PM":
        steps.append("기획서에 정의된 노출/정책/문구 조건을 확인한다.")
    elif perspective == "DEV":
        steps.append("필요한 API, 상태값, 데이터 의존성이 충족된 상태를 준비한다.")
    else:
        steps.append("정상 시나리오와 주요 예외 시나리오를 수행한다.")

    steps.append("화면/응답/상태 변경 결과를 확인한다.")
    return steps


def _build_test_data(requirement: Requirement) -> str:
    parts = []

    if requirement.states:
        parts.append(f"states={', '.join(requirement.states)}")

    if requirement.dependencies:
        parts.append(f"dependencies={', '.join(requirement.dependencies)}")

    return " | ".join(parts)


def _build_expected_result(requirement: Requirement, perspective: str) -> str:
    if requirement.business_rules:
        return " / ".join(requirement.business_rules[:3])

    if perspective == "DEV" and requirement.dependencies:
        return "의존 요소 연동 후 요구사항에 맞는 응답과 상태가 반환된다."

    return f"{requirement.feature_name} 요구사항에 맞게 동작한다."


def _build_notes(requirement: Requirement) -> str:
    if requirement.open_questions:
        return "확인 필요: " + " / ".join(requirement.open_questions)

    return ""
