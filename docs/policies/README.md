# Company Policy Context

이 폴더는 테스트케이스 생성 시 참조할 회사 정책/규칙을 정리하는 공간이다.

권장 작성 방식:

- 실제 회사 정책을 짧고 명확한 bullet로 작성한다.
- 기획서에 없는 내용을 단정하지 말고, 확인 필요 조건으로 남길 기준을 작성한다.
- 화면명, 메뉴명, 상태값, 결함 기준처럼 테스트케이스 품질에 직접 영향을 주는 규칙을 우선 채운다.
- 정책이 바뀌면 모델을 다시 학습시키기보다 이 문서를 수정한다.

파일 역할:

- `qa_policy.md`: QA 범위, 필수 검증 관점, 테스트 우선순위 기준
- `testcase_style_guide.md`: TC title/steps/expected result 작성 규칙
- `domain_terms.md`: 서비스 용어, 메뉴 경로, 상태값 정의
- `defect_policy.md`: pass/fail/blocked/fixed 및 이슈 등록 기준
- `release_checklist.md`: 배포 전 회귀/스모크 체크 기준
