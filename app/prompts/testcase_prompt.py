from __future__ import annotations

import json

from app.schemas.requirement import Requirement


def build_testcase_generation_prompt(
    requirements: list[Requirement],
    perspectives: list[str],
) -> str:
    requirement_payload = [
        requirement.model_dump(mode="json") for requirement in requirements
    ]

    return f"""
너는 숙련된 QA 리드다.

입력된 요구사항 JSON을 바탕으로 기획자(PM), 개발자(DEV), QA 관점의 테스트케이스를 작성하라.

원칙:
1. 요구사항에 근거한 테스트케이스만 작성한다.
2. 정상, 예외, 경계값, 상태 전이, 권한, 의존 API/데이터 리스크를 고려한다.
3. 각 요구사항마다 관점별로 최소 1개 이상의 테스트케이스를 작성한다.
4. 추정이 필요한 내용은 notes에 확인 필요로 남긴다.
5. 반드시 JSON만 반환한다. 설명 문장은 쓰지 않는다.

관점:
{json.dumps(perspectives, ensure_ascii=False)}

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
      "preconditions": ["로그인 상태"],
      "steps": ["종합검진 메뉴 진입", "병원 리스트 확인"],
      "test_data": "예약 가능 병원 데이터",
      "expected_result": "예약 가능 병원만 리스트에 노출된다.",
      "notes": ""
    }}
  ]
}}

요구사항 JSON:
{json.dumps(requirement_payload, ensure_ascii=False, indent=2)}
""".strip()
