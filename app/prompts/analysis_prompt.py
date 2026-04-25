from __future__ import annotations

import json

from app.schemas.requirement import Requirement


def build_requirement_analysis_prompt(requirements: list[Requirement]) -> str:
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
- 추정이 필요한 내용은 open_questions 또는 missing_policies로 분리한다.
- 테스트 불가능한 항목은 untestable_items에 작성한다.
- 반드시 JSON만 반환한다.

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
  "contradictions": [],
  "missing_policies": [],
  "untestable_items": []
}}

요구사항 JSON:
{json.dumps(requirement_payload, ensure_ascii=False, indent=2)}
""".strip()
