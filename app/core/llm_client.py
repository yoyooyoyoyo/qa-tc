from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any

import requests

from app.schemas.analysis import RequirementAnalysisResult
from app.schemas.requirement import Requirement


class BaseLLMClient(ABC):
    @abstractmethod
    def extract_requirements(self, *, document_text: str, prompt: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def analyze_requirements(
        self,
        *,
        requirements: list[Requirement],
        prompt: str,
    ) -> Any:
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

    def analyze_requirements(
        self,
        *,
        requirements: list[Requirement],
        prompt: str,
    ) -> Any:
        return _rule_based_requirement_analysis(requirements)

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

    def analyze_requirements(
        self,
        *,
        requirements: list[Requirement],
        prompt: str,
    ) -> Any:
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

    def analyze_requirements(
        self,
        *,
        requirements: list[Requirement],
        prompt: str,
    ) -> Any:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "너는 PM, DEV, QA 관점으로 요구사항을 검토하는 리뷰어다. "
                        "반드시 JSON 스키마를 준수한다."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "requirement_analysis_result",
                    "strict": True,
                    "schema": REQUIREMENT_ANALYSIS_JSON_SCHEMA,
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
                    "source_quote": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
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
                    "source_quote",
                    "confidence",
                    "evidence",
                ],
            },
        }
    },
    "required": ["requirements"],
}


REQUIREMENT_ANALYSIS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "analyses": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "perspective": {"type": "string"},
                    "findings": {"type": "array", "items": {"type": "string"}},
                    "risks": {"type": "array", "items": {"type": "string"}},
                    "open_questions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["perspective", "findings", "risks", "open_questions"],
            },
        },
        "requirement_focus": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "requirement_id": {"type": "string"},
                    "is_core": {"type": "boolean"},
                    "focus_score": {"type": "integer"},
                    "focus_reason": {"type": "array", "items": {"type": "string"}},
                    "recommended_depth": {"type": "string"},
                },
                "required": [
                    "requirement_id",
                    "is_core",
                    "focus_score",
                    "focus_reason",
                    "recommended_depth",
                ],
            },
        },
        "scenario_gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "requirement_id": {"type": "string"},
                    "gap_type": {"type": "string"},
                    "area": {"type": "string"},
                    "scenario": {"type": "string"},
                    "issue": {"type": "string"},
                    "missing_detail": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "risk": {"type": "string"},
                    "question": {"type": "string"},
                    "suggested_test": {"type": "string"},
                    "severity": {"type": "string"},
                },
                "required": [
                    "requirement_id",
                    "gap_type",
                    "area",
                    "scenario",
                    "issue",
                    "missing_detail",
                    "why_it_matters",
                    "risk",
                    "question",
                    "suggested_test",
                    "severity",
                ],
            },
        },
        "gap_report": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "requirement_id": {"type": "string"},
                    "gap_type": {"type": "string"},
                    "area": {"type": "string"},
                    "scenario": {"type": "string"},
                    "issue": {"type": "string"},
                    "missing_detail": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "risk": {"type": "string"},
                    "question": {"type": "string"},
                    "suggested_test": {"type": "string"},
                    "severity": {"type": "string"},
                },
                "required": [
                    "requirement_id",
                    "gap_type",
                    "area",
                    "scenario",
                    "issue",
                    "missing_detail",
                    "why_it_matters",
                    "risk",
                    "question",
                    "suggested_test",
                    "severity",
                ],
            },
        },
        "questions_for_pm": {"type": "array", "items": {"type": "string"}},
        "policy_conflicts": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "inferred_test_candidates": {"type": "array", "items": {"type": "string"}},
        "contradictions": {"type": "array", "items": {"type": "string"}},
        "missing_policies": {"type": "array", "items": {"type": "string"}},
        "untestable_items": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "analyses",
        "requirement_focus",
        "scenario_gaps",
        "gap_report",
        "questions_for_pm",
        "policy_conflicts",
        "assumptions",
        "inferred_test_candidates",
        "contradictions",
        "missing_policies",
        "untestable_items",
    ],
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
                    "test_screen": {"type": "string"},
                    "preconditions": {"type": "array", "items": {"type": "string"}},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "test_data": {"type": "string"},
                    "expected_result": {"type": "string"},
                    "notes": {"type": "string"},
                    "category": {"type": "string"},
                    "severity": {"type": "string"},
                    "automation_candidate": {"type": "boolean"},
                    "related_risks": {"type": "array", "items": {"type": "string"}},
                    "traceability": {"type": "array", "items": {"type": "string"}},
                    "source_quote": {"type": "string"},
                    "source_policy": {"type": "array", "items": {"type": "string"}},
                    "related_policy": {"type": "array", "items": {"type": "string"}},
                    "generation_scope": {"type": "string"},
                    "risk_basis": {"type": "array", "items": {"type": "string"}},
                    "omit_reason": {"type": "string"},
                    "quality_warnings": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "testcase_id",
                    "requirement_id",
                    "perspective",
                    "priority",
                    "test_type",
                    "title",
                    "test_screen",
                    "preconditions",
                    "steps",
                    "test_data",
                    "expected_result",
                    "notes",
                    "category",
                    "severity",
                    "automation_candidate",
                    "related_risks",
                    "traceability",
                    "source_quote",
                    "source_policy",
                    "related_policy",
                    "generation_scope",
                    "risk_basis",
                    "omit_reason",
                    "quality_warnings",
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
                "source_quote": feature_name,
                "confidence": 0.55,
                "evidence": [feature_name],
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


def _rule_based_requirement_analysis(
    requirements: list[Requirement],
) -> dict[str, Any]:
    all_open_questions = []
    dependency_risks = []
    state_risks = []
    requirement_focus = []
    scenario_gaps = []

    for requirement in requirements:
        all_open_questions.extend(requirement.open_questions)
        requirement_focus.append(_build_requirement_focus(requirement))
        scenario_gaps.extend(_build_scenario_gaps(requirement))

        if requirement.dependencies:
            dependency_risks.append(
                f"{requirement.feature_id} {requirement.feature_name}: 의존 요소 연동 확인 필요"
            )

        if requirement.states:
            state_risks.append(
                f"{requirement.feature_id} {requirement.feature_name}: 상태별 전이/표시 확인 필요"
            )

    return {
        "analyses": [
            {
                "perspective": "PM",
                "findings": ["요구사항별 정책과 노출 조건을 테스트 기준으로 검토 필요"],
                "risks": ["세부 정책이 부족하면 기대 결과가 추상화될 수 있음"],
                "open_questions": _dedupe(all_open_questions),
            },
            {
                "perspective": "DEV",
                "findings": ["API, 상태값, 데이터 의존성을 테스트 데이터로 명시 필요"],
                "risks": dependency_risks,
                "open_questions": [],
            },
            {
                "perspective": "QA",
                "findings": ["정상, 예외, 상태 전이 케이스를 분리해 작성 필요"],
                "risks": state_risks,
                "open_questions": [],
            },
        ],
        "requirement_focus": requirement_focus,
        "scenario_gaps": scenario_gaps,
        "gap_report": scenario_gaps,
        "questions_for_pm": _dedupe(
            [gap["question"] for gap in scenario_gaps if gap.get("question")]
        ),
        "policy_conflicts": [],
        "assumptions": _build_assumptions(scenario_gaps),
        "inferred_test_candidates": _dedupe(
            [gap["suggested_test"] for gap in scenario_gaps if gap.get("suggested_test")]
        ),
        "contradictions": [],
        "missing_policies": _dedupe(all_open_questions),
        "untestable_items": [],
    }


def _build_assumptions(scenario_gaps: list[dict[str, Any]]) -> list[str]:
    assumptions: list[str] = []
    for gap in scenario_gaps:
        gap_type = gap.get("gap_type", "")
        area = gap.get("area", "")
        if gap_type:
            assumptions.append(f"{area or '해당 영역'}의 {gap_type}은 확인 전까지 추론 기반으로만 다룸")
    return _dedupe(assumptions)


def _build_scenario_gaps(requirement: Requirement) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    text = " ".join(
        [
            requirement.feature_name,
            " ".join(requirement.business_rules),
            " ".join(requirement.states),
            " ".join(requirement.dependencies),
        ]
    )

    if requirement.states and not any(keyword in text for keyword in ["실패", "취소", "재시도", "롤백"]):
        gaps.append(
            {
                "requirement_id": requirement.feature_id,
                "gap_type": "missing_state_transition",
                "area": requirement.feature_name,
                "scenario": "상태 전이 중 실패 또는 취소가 발생하는 경우",
                "issue": "실패/취소/재시도 상태 전이 기준이 없음",
                "missing_detail": "실패/취소/재시도 시 상태 전이와 화면 표시 기준이 명확하지 않음",
                "why_it_matters": "상태 기준이 없으면 화면과 백엔드 상태가 다르게 보일 수 있음",
                "risk": "사용자 화면 상태와 백엔드 상태가 불일치할 수 있음",
                "question": "각 상태에서 실패/취소/재시도 시 최종 상태와 사용자 안내 문구는 무엇인가?",
                "suggested_test": "상태 전이 중 실패/취소/재시도 발생 시 목록/상세 상태와 안내 문구 확인",
                "severity": "High",
            }
        )

    if requirement.dependencies:
        gaps.append(
            {
                "requirement_id": requirement.feature_id,
                "gap_type": "missing_exception_handling",
                "area": requirement.feature_name,
                "scenario": "외부 API 또는 서버 연동이 실패하거나 지연되는 경우",
                "issue": "연동 실패/지연 시 처리 기준이 없음",
                "missing_detail": "연동 실패, timeout, 지연 응답에 대한 사용자 안내와 재시도 정책이 부족함",
                "why_it_matters": "사용자가 처리 결과를 알 수 없으면 중복 요청이나 운영 문의가 발생할 수 있음",
                "risk": "처리 결과를 사용자가 알 수 없거나 중복 요청이 발생할 수 있음",
                "question": "연동 실패/지연 시 화면 표시, 재시도 가능 여부, 데이터 저장 기준은 무엇인가?",
                "suggested_test": "외부 API timeout 또는 실패 응답 시 화면 안내, 재시도, 저장 데이터 정합성 확인",
                "severity": "High",
            }
        )

    if any(keyword in text for keyword in ["과금", "결제", "금액", "환불", "지원금", "쿠폰"]):
        gaps.append(
            {
                "requirement_id": requirement.feature_id,
                "gap_type": "missing_cancel_or_rollback",
                "area": requirement.feature_name,
                "scenario": "금액 또는 과금 처리 후 취소/실패가 발생하는 경우",
                "issue": "과금 후 취소/실패/롤백 기준이 없음",
                "missing_detail": "취소/실패/재처리 시 과금, 환불, 금액 정합성 기준이 명확하지 않음",
                "why_it_matters": "금액 정합성 오류는 사용자 클레임과 정산 문제로 이어질 수 있음",
                "risk": "과금 오류 또는 사용자 클레임으로 이어질 수 있음",
                "question": "처리 실패 또는 취소 시 과금/환불/금액 재계산 기준은 무엇인가?",
                "suggested_test": "과금 처리 후 실패/취소 발생 시 금액, 환불, 이력, 화면 상태 정합성 확인",
                "severity": "High",
            }
        )

    return gaps


def _build_requirement_focus(requirement: Requirement) -> dict[str, Any]:
    text = " ".join(
        [
            requirement.feature_name,
            requirement.actor,
            requirement.entry_point,
            " ".join(requirement.business_rules),
            " ".join(requirement.states),
            " ".join(requirement.dependencies),
        ]
    )
    focus_reason: list[str] = []
    score = 20

    criteria = [
        ("business", ["저장", "수정", "삭제", "결제", "예약", "취소", "로그인", "발송", "확정"]),
        ("state", ["상태", "대기", "완료", "실패", "성공", "전이", "확정", "취소"]),
        ("api", ["api", "서버", "db", "백엔드", "연동", "배치", "어드민"]),
        ("auth", ["권한", "인증", "개인정보", "동의"]),
        ("money", ["과금", "금액", "결제", "부가세", "환불", "지원금", "쿠폰"]),
    ]

    lowered = text.lower()
    for reason, keywords in criteria:
        if any(keyword.lower() in lowered for keyword in keywords):
            focus_reason.append(reason)
            score += 15

    if requirement.states:
        score += 10
    if requirement.dependencies:
        score += 10

    score = min(score, 100)
    is_core = score >= 50

    return {
        "requirement_id": requirement.feature_id,
        "is_core": is_core,
        "focus_score": score,
        "focus_reason": focus_reason or ["low-impact-ui"],
        "recommended_depth": "deep" if is_core else "smoke",
    }


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
            focus = _build_requirement_focus(requirement)
            testcases.append(
                {
                    "testcase_id": f"TC-{counter:03d}",
                    "requirement_id": requirement.feature_id,
                    "perspective": perspective_upper,
                    "priority": _guess_priority(requirement, perspective_upper),
                    "test_type": _guess_test_type(requirement, perspective_upper),
                    "title": _build_testcase_title(requirement, perspective_upper),
                    "test_screen": _build_test_screen(requirement),
                    "preconditions": requirement.preconditions,
                    "steps": _build_test_steps(requirement, perspective_upper),
                    "test_data": _build_test_data(requirement),
                    "expected_result": _build_expected_result(requirement, perspective_upper),
                    "notes": _build_notes(requirement),
                    "category": _guess_category(requirement, perspective_upper),
                    "severity": _guess_severity(requirement),
                    "automation_candidate": perspective_upper in {"DEV", "QA"},
                    "related_risks": _build_related_risks(requirement, perspective_upper),
                    "traceability": _build_traceability(requirement),
                    "source_quote": requirement.source_quote,
                    "source_policy": [],
                    "related_policy": [],
                    "generation_scope": "core-deep" if focus["is_core"] else "smoke-only",
                    "risk_basis": focus["focus_reason"],
                    "omit_reason": "" if focus["is_core"] else "비핵심 기능으로 판단되어 smoke 범위로 축약 생성",
                    "quality_warnings": [],
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


def _guess_category(requirement: Requirement, perspective: str) -> str:
    if perspective == "PM":
        return "정책"

    if "권한" in requirement.feature_name or any("권한" in rule for rule in requirement.business_rules):
        return "권한"

    if requirement.states:
        return "상태전이"

    if requirement.dependencies and perspective == "DEV":
        return "API"

    return "정상/예외"


def _guess_severity(requirement: Requirement) -> str:
    critical_keywords = ["결제", "인증", "권한", "삭제"]
    major_keywords = ["로그인", "예약", "저장", "수정", "오류"]
    text = f"{requirement.feature_name} {' '.join(requirement.business_rules)}"

    if any(keyword in text for keyword in critical_keywords):
        return "Critical"

    if any(keyword in text for keyword in major_keywords):
        return "Major"

    return "Medium"


def _build_testcase_title(requirement: Requirement, perspective: str) -> str:
    suffix_by_perspective = {
        "PM": "정책/기획 의도 충족 여부 확인",
        "DEV": "구현 조건 및 의존 요소 정상 동작 확인",
        "QA": "사용자 시나리오 정상/예외 동작 확인",
    }
    suffix = suffix_by_perspective.get(perspective, "동작 확인")
    return f"{requirement.feature_name} - {suffix}"


def _build_test_screen(requirement: Requirement) -> str:
    if requirement.entry_point:
        return requirement.entry_point

    if requirement.source_section:
        return requirement.source_section

    return requirement.feature_name


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


def _build_related_risks(requirement: Requirement, perspective: str) -> list[str]:
    risks = []

    if requirement.dependencies:
        risks.append("의존 API/데이터 불일치 리스크")

    if requirement.states:
        risks.append("상태값별 노출/처리 누락 리스크")

    if perspective == "PM" and requirement.open_questions:
        risks.append("정책 미확정으로 기대 결과가 변경될 리스크")

    return risks


def _build_traceability(requirement: Requirement) -> list[str]:
    values = [requirement.feature_id]
    values.extend(requirement.evidence[:3])
    return _dedupe(values)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)

    return deduped
