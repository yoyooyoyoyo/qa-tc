# qa-tc-agent

기획서/정책서/API 명세를 분석해 PM/DEV/QA 관점의 testcase를 생성하는 AI agent 프로젝트

## Requirement extraction API

`POST /extract-requirements`

Swagger에서 파일 또는 텍스트를 넣으면 테스트케이스 생성 전 단계로 사용할 요구사항 JSON을 반환한다.

- `file`: txt, md, pdf, docx, xlsx, xls 기획서 파일
- `text`: 파일 대신 바로 분석할 기획서 텍스트

응답 구조:

```json
{
  "message": "Requirements extracted successfully",
  "filename": "inline-text",
  "text_length": 120,
  "requirement_count": 1,
  "requirements": [
    {
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
      "evidence": ["예약 가능 병원만 노출"]
    }
  ]
}
```

기본값은 `LLM_PROVIDER=mock`이라 API 키 없이도 동작한다.

OpenAI 연결:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=...
export OPENAI_MODEL=gpt-4o-mini
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

Figma 연결:

```bash
export FIGMA_ACCESS_TOKEN=...
```

Figma token은 repo에 커밋하지 말고 환경변수 또는 `.env`로만 관리한다.

## Figma Context API

`POST /extract-figma-context`

Figma file/frame URL을 넣으면 화면명, frame 경로, 텍스트 레이어를 추출한다.

- `figma_url`: Figma file/frame URL
- `include_images`: frame 이미지 URL 포함 여부
- `max_screens`: 추출할 최대 화면 수

Figma URL은 다음 정보를 포함할 수 있다.

```text
https://www.figma.com/design/{file_key}/{file_name}?node-id=1-2
```

`/generate-testcases-from-document`, `/export-testcases-from-document-tsv`, `/export-testcases-from-document-xlsx`에서도 선택값으로 `figma_url`을 넣을 수 있다. 이 경우 Figma의 화면명/텍스트 레이어가 `test_screen`, `steps`, `expected result` 생성에 참고된다.

Figma MCP를 사용하는 경우에는 Figma API token 없이도 MCP가 추출한 화면 정보를 `figma_context` 필드에 직접 넣을 수 있다.

예시:

```text
Figma file: 기업검진

Screens:
- 기업검진 > 종합검진 목록
  texts: 종합검진 / 예약하기 / 검진기관 / 필터
- 기업검진 > 종합검진 상세
  texts: 검진 항목 / 병원 정보 / 예약 신청
```

이 값을 `/generate-testcases-from-document` 또는 `/export-testcases-from-document-xlsx`의 `figma_context`에 넣으면 `테스트 진행 화면`, `steps`, `expected result` 생성에 참고된다.

## Company Policy Context

회사 QA 정책과 테스트케이스 작성 규칙은 `docs/policies`에 Markdown으로 관리한다.
정책은 레이어별로 나뉘며, TC 생성 시 `app/core/policy_loader.py`가 공통 정책과 관련 기능 정책을 자동으로 읽어 프롬프트에 주입한다.

- `docs/policies/global/qa_policy.md`: QA 범위, 테스트 유형, 우선순위 기준
- `docs/policies/global/focus_policy.md`: 핵심 기능 선별, 비핵심 축약, 엣지케이스 확장 기준
- `docs/policies/global/testcase_style_guide.md`: title, precondition, steps, expected result 작성 규칙
- `docs/policies/global/defect_policy.md`: pass/fail/blocked/fixed 및 이슈 등록 기준
- `docs/policies/global/release_checklist.md`: 배포 전 smoke/regression 체크 기준
- `docs/policies/domain/domain_terms.md`: 서비스 용어, 화면 경로, 상태값 정의
- `docs/policies/domain/coupon_policy.md`: 쿠폰 노출, 사용, 실패, 어드민 상태 정책
- `docs/policies/domain/booking_policy.md`: 예약 상태, 예약/결제 화면 구성, 예약 변경/취소 정책
- `docs/policies/domain/payment_policy.md`: 결제금액, 가격 산식, 0원 결제, B2B 지원금 정책
- `docs/policies/domain/booking_history_policy.md`: 예약내역 카드/상세, 영수증/확인서, 버튼 정책
- `docs/policies/feature/*.md`: 쿠폰, 예약내역 등 기능별 누적 정책

정책 충돌 시 우선순위는 현재 기획서, 기능/도메인 정책, 회사 공통 QA 정책, 도메인 용어/관례, 추론 순서다.

최신 기획서는 그대로 누적하지 않고, 확정된 정책만 별도 정책 문서로 승격한다. TC 작성 전 정책 업데이트 절차는 `docs/skills/tc_policy_update_workflow.md`를 따른다.

## Testcase generation API

`POST /generate-testcases`

`/extract-requirements` 응답의 `requirements` 배열을 넣으면 PM/DEV/QA 분석 후 테스트케이스를 생성한다.

```json
{
  "requirements": [
    {
      "feature_id": "REQ-001",
      "feature_name": "로그인",
      "platform": ["WEB"],
      "actor": "사용자",
      "entry_point": "로그인 화면",
      "preconditions": [],
      "business_rules": ["이메일과 비밀번호로 로그인 가능"],
      "states": ["성공", "실패"],
      "dependencies": ["로그인 API"],
      "open_questions": [],
      "source_section": "로그인",
      "source_quote": "이메일과 비밀번호로 로그인 가능",
      "confidence": 0.9,
      "evidence": ["이메일과 비밀번호로 로그인 가능"]
    }
  ],
  "perspectives": ["PM", "DEV", "QA"]
}
```

응답에는 `analysis`와 확장된 테스트케이스 필드가 포함된다.

- `analysis`: PM/DEV/QA별 findings, risks, open_questions
- `analysis.requirement_focus`: requirement별 핵심도, 생성 깊이 판단
- `analysis.scenario_gaps`: 유저 시나리오 기반 기획 누락/확인 필요 지점
- `analysis.gap_report`: 누락 유형, 영향 영역, 리스크, PM 질문, 추론 테스트 후보
- `analysis.questions_for_pm`: 기획자에게 바로 확인할 질문 리스트
- `analysis.policy_conflicts`: 현재 기획서와 기존 정책 충돌
- `analysis.assumptions`: 추론 기반 판단에 사용한 가정
- `analysis.inferred_test_candidates`: 문서 근거가 부족하지만 검토 가치가 있는 테스트 후보
- `category`: 정상/예외/경계값/권한/상태전이/API/회귀 등 테스트 분류
- `severity`: Critical, Major, Minor 등 영향도
- `automation_candidate`: 자동화 후보 여부
- `related_risks`: 관련 리스크
- `traceability`: 요구사항/근거 연결
- `source_quote`: 테스트케이스 근거 원문
- `source_policy`: 참고한 정책 문서
- `related_policy`: 관련 정책/규칙
- `generation_scope`: core-deep, smoke-only 등 생성 범위
- `risk_basis`: business, data, state, auth, api 등 리스크 근거
- `omit_reason`: 비핵심 축약 또는 제외 사유
- `quality_warnings`: 후처리 품질 경고

## Export APIs

- `POST /export-testcases-tsv`: 생성된 `testcases` 배열을 TSV 파일로 다운로드한다.
- `POST /export-testcases-xlsx`: 생성된 `testcases` 배열을 Excel 파일로 다운로드한다. `openpyxl` 설치가 필요하다.
- `POST /export-gap-report-md`: 생성된 `analysis`를 기획서 보완 필요사항 Markdown으로 다운로드한다.

`/generate-testcases` 응답의 `testcases` 배열을 그대로 넣으면 된다.

Excel 파일은 QA 진행용 양식으로 생성된다.

| no. | title | 테스트 진행 화면 | precondition | steps | expected result | test-result | comment | issue ticket |
|---|---|---|---|---|---|---|---|---|

- `test-result`는 `pass`, `fail`, `blocked`, `fixed` 드롭다운이다.
- `comment`와 `issue ticket`은 QA 진행 중 작성할 수 있도록 빈 값으로 생성된다.

## End-to-end APIs

`POST /generate-testcases-from-document`

기획서 파일 또는 텍스트를 넣으면 요구사항 추출, PM/DEV/QA 분석, 테스트케이스 생성을 한 번에 수행한다.

- `file`: txt, md, pdf, docx, xlsx, xls 기획서 파일
- `text`: 파일 대신 바로 분석할 기획서 텍스트
- `perspectives`: 쉼표로 구분한 관점. 기본값은 `PM,DEV,QA`

`POST /export-testcases-from-document-tsv`

기획서 파일 또는 텍스트를 넣으면 요구사항 추출, PM/DEV/QA 분석, 테스트케이스 생성 후 TSV 파일을 바로 다운로드한다.

`POST /export-testcases-from-document-xlsx`

기획서 파일 또는 텍스트를 넣으면 요구사항 추출, PM/DEV/QA 분석, 테스트케이스 생성 후 Excel 파일을 바로 다운로드한다.

`POST /export-gap-report-from-document-md`

기획서 파일 또는 텍스트를 넣으면 요구사항 추출과 Gap Review를 수행하고, 기획서에 보완되어야 할 누락/모호점/PM 확인 질문을 Markdown 파일로 다운로드한다.
