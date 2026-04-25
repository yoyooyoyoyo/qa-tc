from __future__ import annotations

import json

from app.schemas.analysis import RequirementAnalysisResult
from app.schemas.requirement import Requirement


def build_testcase_generation_prompt(
    requirements: list[Requirement],
    perspectives: list[str],
    analysis: RequirementAnalysisResult | None = None,
    figma_context: str = "",
) -> str:
    requirement_payload = [
        requirement.model_dump(mode="json") for requirement in requirements
    ]

    analysis_payload = (
        analysis.model_dump(mode="json") if analysis else RequirementAnalysisResult().model_dump(mode="json")
    )

    return f"""
너는 숙련된 QA 리드다.

입력된 요구사항 JSON과 사전 분석 결과를 바탕으로 기획자(PM), 개발자(DEV), QA 관점의 테스트케이스를 작성하라.

원칙:
1. 요구사항에 근거한 테스트케이스만 작성한다.
2. 정상, 예외, 경계값, 상태 전이, 권한, 의존 API/데이터 리스크를 고려한다.
3. 각 테스트케이스는 한 가지 검증 의도만 가진다.
4. 동일한 title/steps/expected_result 조합을 반복하지 않는다.
5. 요구사항의 source_quote/evidence를 traceability와 source_quote에 반영한다.
6. 추정이 필요한 내용은 notes와 quality_warnings에 확인 필요로 남긴다.
7. Figma 컨텍스트가 있으면 test_screen에는 가장 가까운 화면 경로를 사용한다.
8. Figma 텍스트 레이어의 버튼명/라벨/문구는 steps와 expected_result 작성에 참고한다.
9. 반드시 JSON만 반환한다. 설명 문장은 쓰지 않는다.

관점:
{json.dumps(perspectives, ensure_ascii=False)}

사전 분석 결과:
{json.dumps(analysis_payload, ensure_ascii=False, indent=2)}

Figma 화면/디자인 컨텍스트:
{figma_context or "제공된 Figma 컨텍스트 없음"}

반환 JSON 스키마:
{{
  "testcases": [
    {{
      "testcase_id": "TC-001",
      "requirement_id": "REQ-001",
      "perspective": "QA",
      "priority": "High",
      "test_type": "Functional",
      "title": "예약 가능 병원 리스트가 정상 노출되는지 확인",
      "test_screen": "메인 > 종합검진",
      "preconditions": ["로그인 상태"],
      "steps": ["종합검진 메뉴 진입", "병원 리스트 확인"],
      "test_data": "예약 가능 병원 데이터",
      "expected_result": "예약 가능 병원만 리스트에 노출된다.",
      "notes": "",
      "category": "정상",
      "severity": "Major",
      "automation_candidate": true,
      "related_risks": ["예약불가 병원 노출 리스크"],
      "traceability": ["REQ-001", "예약 가능 병원만 노출"],
      "source_quote": "예약 가능 병원만 노출",
      "quality_warnings": []
    }}
  ]
}}

요구사항 JSON:
{json.dumps(requirement_payload, ensure_ascii=False, indent=2)}
""".strip()
