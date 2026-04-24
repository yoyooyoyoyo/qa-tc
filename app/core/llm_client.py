from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    @abstractmethod
    def extract_requirements(self, *, document_text: str, prompt: str) -> Any:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    실제 LLM 연결 전 임시로 동작시키는 mock/rule-based 클라이언트.
    문서에서 헤더/키워드를 대충 뽑아서 requirement 형태로 반환한다.
    """

    def extract_requirements(self, *, document_text: str, prompt: str) -> Any:
        return _rule_based_requirement_extraction(document_text)


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


def get_llm_client() -> BaseLLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()

    if provider == "mock":
        return MockLLMClient()

    if provider == "external":
        return ExternalLLMClient()

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


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
