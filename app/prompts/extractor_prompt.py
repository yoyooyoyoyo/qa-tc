from __future__ import annotations


def build_requirement_extraction_prompt(document_text: str) -> str:
    return f"""
너는 숙련된 QA 요구사항 분석가다.

입력 문서에서 테스트 가능한 기능 요구사항만 구조화해서 추출하라.

목표:
1. 기능 단위를 식별한다.
2. 사용자 액션, 시스템 반응, 상태값, 정책, 조건부 노출, 예외 처리, 권한 조건을 추출한다.
3. 테스트케이스 작성에 필요한 사전조건과 의존 요소를 정리한다.
4. 문서에 없는 추정은 금지한다.
5. 애매한 부분은 open_questions로 분리한다.
6. 각 요구사항마다 source_quote, evidence, confidence를 반드시 채운다.
7. 반드시 JSON만 반환한다. 설명 문장은 쓰지 않는다.

반드시 아래 스키마의 JSON 배열 또는 JSON 객체로 응답하라.

배열 예시:
[
  {{
    "feature_id": "REQ-001",
    "feature_name": "예약 가능 병원 리스트 조회",
    "platform": ["WEB", "APP"],
    "actor": "사용자",
    "entry_point": "메인 > 종합검진",
    "preconditions": ["로그인 상태"],
    "business_rules": ["예약 가능 병원만 노출"],
    "states": ["예약가능", "예약불가"],
    "dependencies": ["병원 목록 조회 API"],
    "open_questions": [],
    "source_section": "3.2 병원 리스트",
    "source_quote": "예약 가능 병원만 노출",
    "confidence": 0.92,
    "evidence": ["예약 가능 병원만 노출", "병원 목록 조회 API"]
  }}
]

객체 예시:
{{
  "requirements": [
    {{
      "feature_id": "REQ-001",
      "feature_name": "예약 가능 병원 리스트 조회",
      "platform": ["WEB", "APP"],
      "actor": "사용자",
      "entry_point": "메인 > 종합검진",
      "preconditions": ["로그인 상태"],
      "business_rules": ["예약 가능 병원만 노출"],
      "states": ["예약가능", "예약불가"],
      "dependencies": ["병원 목록 조회 API"],
      "open_questions": [],
      "source_section": "3.2 병원 리스트",
      "source_quote": "예약 가능 병원만 노출",
      "confidence": 0.92,
      "evidence": ["예약 가능 병원만 노출", "병원 목록 조회 API"]
    }}
  ]
}}

아래 문서를 분석하라.

[DOCUMENT START]
{document_text}
[DOCUMENT END]
""".strip()
