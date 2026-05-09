from __future__ import annotations

import json

from app.schemas.requirement import Requirement


def build_requirement_analysis_prompt(
    requirements: list[Requirement],
    policy_context: str = "",
) -> str:
    requirement_payload = [
        requirement.model_dump(mode="json") for requirement in requirements
    ]

    return f"""
너는 기획자(PM), 개발자(DEV), QA 리드가 함께 참여하는 요구사항 리뷰어다.

입력된 요구사항 JSON을 검토해 테스트케이스 생성 전에 필요한 분석 결과를 작성하라.

관점:
1. PM: 정책 누락, 사용자 흐름, 노출/미노출 조건, 문구/운영 정책, 모호한 기획을 검토한다.
2. DEV: API, DB, 상태값, 권한, validation, 예외 처리, 연동 의존성을 검토한다.
3. QA: 정상/예외/경계값/권한/상태전이/회귀 테스트 리스크를 검토한다.

원칙:
- 요구사항에 근거한 내용만 작성한다.
- 아래 정책 컨텍스트는 기존 회사/서비스 기준이다.
- 현재 요구사항과 정책이 충돌하면 현재 요구사항을 우선하되 contradictions 또는 open_questions에 남긴다.
- 정책에 있는 조건이 현재 요구사항에 누락되어 있으면 missing_policies에 남긴다.
- focus policy를 기준으로 requirement별 핵심도와 생성 깊이를 requirement_focus에 작성한다.
- 핵심 기능은 저장/수정/삭제/결제/예약/취소/상태전이/API/권한/개인정보/과금/발송/확정/실패/재시도 관련 기능이다.
- 비핵심 기능은 단순 문구/스타일/장식성 UI/반복 variation처럼 사용자 영향이 낮은 항목이다.
- 사용자 시나리오를 정상 흐름, 실패 흐름, 재진입/뒤로가기, 중복 요청, 권한 없음, 데이터 없음, 외부 연동 실패 관점으로 굴려본다.
- 기획서에 누락된 결정 지점, 기획자가 놓쳤을 가능성이 있는 예외, 화면/API/DB 정합성 공백은 scenario_gaps에 작성한다.
- scenario_gaps는 단순 호기심이 아니라 TC 작성 전에 확인해야 할 사용자 영향이 있는 누락만 작성한다.
- gap_report에는 scenario_gaps와 같은 항목을 gap_type, area, issue, why_it_matters, question, suggested_test까지 포함해 리포트 형태로 작성한다.
- questions_for_pm에는 기획자에게 바로 물어볼 질문만 따로 모은다.
- policy_conflicts에는 현재 요구사항과 기존 정책 컨텍스트가 충돌하는 내용을 따로 모은다.
- assumptions에는 TC 후보를 만들기 위해 임시로 둔 가정을 따로 모은다.
- inferred_test_candidates에는 기획서 근거는 부족하지만 리스크상 검토할 가치가 있는 테스트 후보를 작성한다.
- confirmed 내용과 inferred 내용을 섞지 않는다.
- 추정이 필요한 내용은 open_questions 또는 missing_policies로 분리한다.
- 테스트 불가능한 항목은 untestable_items에 작성한다.
- 반드시 JSON만 반환한다.

정책 컨텍스트:
{policy_context or "제공된 정책 컨텍스트 없음"}

반환 JSON 스키마:
{{
  "analyses": [
    {{
      "perspective": "PM",
      "findings": ["..."],
      "risks": ["..."],
      "open_questions": ["..."]
    }}
  ],
  "requirement_focus": [
    {{
      "requirement_id": "REQ-001",
      "is_core": true,
      "focus_score": 85,
      "focus_reason": ["상태 전이", "API 연동", "과금 영향"],
      "recommended_depth": "deep"
    }}
  ],
  "scenario_gaps": [
    {{
      "requirement_id": "REQ-001",
      "gap_type": "missing_state_transition",
      "area": "추적관찰 보고서 발송",
      "scenario": "발송 예약 후 지정일 전에 관리자가 발송을 취소하는 경우",
      "issue": "발송취소 상태의 과금/상태 전이 기준이 없음",
      "missing_detail": "취소 가능 시간, 취소 후 과금 여부, 상태 전이 기준이 명시되어 있지 않음",
      "why_it_matters": "발송취소 상태와 과금 정책이 불일치하면 사용자/운영자 클레임이 발생할 수 있음",
      "risk": "발송취소 상태와 과금 정책이 불일치할 수 있음",
      "question": "발송대기 상태에서 취소 시 과금은 발생하지 않는 것이 맞는가?",
      "suggested_test": "발송대기 상태에서 발송취소 후 상태/과금/이력 노출을 확인",
      "severity": "High"
    }}
  ],
  "gap_report": [
    {{
      "requirement_id": "REQ-001",
      "gap_type": "missing_state_transition",
      "area": "추적관찰 보고서 발송",
      "scenario": "발송 예약 후 지정일 전에 관리자가 발송을 취소하는 경우",
      "issue": "발송취소 상태의 과금/상태 전이 기준이 없음",
      "missing_detail": "취소 가능 시간, 취소 후 과금 여부, 상태 전이 기준이 명시되어 있지 않음",
      "why_it_matters": "발송취소 상태와 과금 정책이 불일치하면 사용자/운영자 클레임이 발생할 수 있음",
      "risk": "발송취소 상태와 과금 정책이 불일치할 수 있음",
      "question": "발송대기 상태에서 취소 시 과금은 발생하지 않는 것이 맞는가?",
      "suggested_test": "발송대기 상태에서 발송취소 후 상태/과금/이력 노출을 확인",
      "severity": "High"
    }}
  ],
  "questions_for_pm": ["발송대기 상태에서 취소 시 과금은 발생하지 않는 것이 맞는가?"],
  "policy_conflicts": [],
  "assumptions": ["발송취소는 발송대기 상태에서만 가능하다고 가정함"],
  "inferred_test_candidates": ["발송대기 상태에서 발송취소 후 상태/과금/이력 노출 확인"],
  "contradictions": [],
  "missing_policies": [],
  "untestable_items": []
}}

요구사항 JSON:
{json.dumps(requirement_payload, ensure_ascii=False, indent=2)}
""".strip()
