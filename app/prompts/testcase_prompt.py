from __future__ import annotations

import json

from app.schemas.analysis import RequirementAnalysisResult
from app.schemas.requirement import Requirement


def build_testcase_generation_prompt(
    requirements: list[Requirement],
    perspectives: list[str],
    analysis: RequirementAnalysisResult | None = None,
    figma_context: str = "",
    policy_context: str = "",
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
2. 정책 컨텍스트를 기존 회사/서비스 기준으로 참고한다.
3. 현재 요구사항과 기존 정책이 충돌하면 현재 요구사항을 우선하고 notes 또는 quality_warnings에 확인 필요를 남긴다.
4. 모든 세부 UI를 나열하지 말고 핵심 리스크 영역을 깊게 검증한다.
5. 핵심 리스크는 상태 전이, 권한/사용자 유형, 과금/금액, 주요 액션, 데이터 저장/연동, 실패/재시도 흐름이다.
6. 정상, 예외, 경계값, 상태 전이, 권한, 의존 API/데이터 리스크를 고려하되 조합 폭발은 피한다.
7. 단순 문구/색상/간격/아이콘 위치/반복 컬럼은 정책 판단이나 사용자 행동에 직접 영향을 줄 때만 TC로 작성한다.
8. 같은 검증 의도를 화면명만 바꿔 반복하지 말고 대표 케이스와 차이가 있는 엣지케이스만 분리한다.
9. 각 테스트케이스는 한 가지 검증 의도만 가진다.
10. 동일한 title/steps/expected_result 조합을 반복하지 않는다.
11. 요구사항의 source_quote/evidence와 관련 정책 파일명을 traceability와 source_policy에 반영한다.
12. analysis.requirement_focus의 recommended_depth가 deep이면 core-deep 범위로 생성한다.
13. analysis.requirement_focus의 recommended_depth가 smoke이면 smoke-only 범위로 생성한다.
14. analysis.requirement_focus의 recommended_depth가 omit이면 원칙적으로 생성하지 않는다.
15. 비핵심 기능을 축약 생성하면 omit_reason에 축약 사유를 남긴다.
16. 추정이 필요한 내용은 notes와 quality_warnings에 확인 필요로 남긴다.
17. Figma 컨텍스트가 있으면 test_screen에는 가장 가까운 화면 경로를 사용한다.
18. Figma 텍스트 레이어의 버튼명/라벨/문구는 steps와 expected_result 작성에 참고한다.
19. 반드시 JSON만 반환한다. 설명 문장은 쓰지 않는다.

TC 선별 우선순위:
1. 상태 전이 실패 또는 잘못된 상태 노출
2. 권한/사용자 유형별 노출 오류
3. 과금/금액/지원금/쿠폰/환불 관련 오류
4. 발송/예약/결제/확정 같은 주요 액션 실패
5. 외부 연동/API 실패와 재시도
6. 경계값: 0원, 1원 이상, N명, 수량 소진, 기간 시작/종료일
7. 정책 충돌 또는 Figma/기획서/기존 정책 불일치
8. 사용자 안내 문구가 행동 판단에 직접 영향을 주는 경우

관점:
{json.dumps(perspectives, ensure_ascii=False)}

사전 분석 결과:
{json.dumps(analysis_payload, ensure_ascii=False, indent=2)}

Figma 화면/디자인 컨텍스트:
{figma_context or "제공된 Figma 컨텍스트 없음"}

정책 컨텍스트:
{policy_context or "제공된 정책 컨텍스트 없음"}

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
      "source_policy": ["docs/policies/domain/domain_terms.md"],
      "related_policy": ["예약 가능 상태 기준"],
      "generation_scope": "core-deep",
      "risk_basis": ["business", "state"],
      "omit_reason": "",
      "quality_warnings": []
    }}
  ]
}}

요구사항 JSON:
{json.dumps(requirement_payload, ensure_ascii=False, indent=2)}
""".strip()
