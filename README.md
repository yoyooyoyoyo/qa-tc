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
      "source_section": "3.2 병원 리스트"
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

## Testcase generation API

`POST /generate-testcases`

`/extract-requirements` 응답의 `requirements` 배열을 넣으면 PM/DEV/QA 관점 테스트케이스를 생성한다.

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
      "source_section": "로그인"
    }
  ],
  "perspectives": ["PM", "DEV", "QA"]
}
```

## Export APIs

- `POST /export-testcases-tsv`: 생성된 `testcases` 배열을 TSV 파일로 다운로드한다.
- `POST /export-testcases-xlsx`: 생성된 `testcases` 배열을 Excel 파일로 다운로드한다. `openpyxl` 설치가 필요하다.

`/generate-testcases` 응답의 `testcases` 배열을 그대로 넣으면 된다.

## End-to-end APIs

`POST /generate-testcases-from-document`

기획서 파일 또는 텍스트를 넣으면 요구사항 추출과 테스트케이스 생성을 한 번에 수행한다.

- `file`: txt, md, pdf, docx, xlsx, xls 기획서 파일
- `text`: 파일 대신 바로 분석할 기획서 텍스트
- `perspectives`: 쉼표로 구분한 관점. 기본값은 `PM,DEV,QA`

`POST /export-testcases-from-document-tsv`

기획서 파일 또는 텍스트를 넣으면 요구사항 추출, 테스트케이스 생성 후 TSV 파일을 바로 다운로드한다.

`POST /export-testcases-from-document-xlsx`

기획서 파일 또는 텍스트를 넣으면 요구사항 추출, 테스트케이스 생성 후 Excel 파일을 바로 다운로드한다.
