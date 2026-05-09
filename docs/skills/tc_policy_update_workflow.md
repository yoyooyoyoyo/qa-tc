# TC Policy Update Workflow

이 문서는 최신 기획서와 Figma context를 기준으로 정책 문서를 업데이트한 뒤 테스트케이스를 생성하기 위한 에이전트 작업 순서다.

## 핵심 원칙

- 기획서는 이번 변경사항이다.
- 정책 문서는 앞으로도 반복 적용할 회사/서비스 기준이다.
- 최신 기획서 전체를 계속 누적하지 않고, 확정된 정책만 `docs/policies`에 정리한다.
- TC 생성 전에는 관련 정책 문서가 최신인지 먼저 확인한다.

## 입력 컨텍스트

TC 작성 또는 정책 업데이트 요청 시 아래 정보를 함께 본다.

- 현재 기획서: Swagger 업로드 파일, 대화 입력, PDF/Word/Excel/Markdown 원문
- Figma context: 화면명, 버튼명, 문구, 상태별 화면 구조
- Global policy: 회사 QA 기준, TC 작성 스타일, 결함/릴리즈 기준
- Domain policy: 쿠폰, 예약, 결제, 예약내역 등 누적 정책
- Feature policy: 특정 배포/기능에서 확정된 세부 정책 메모

## 작업 순서

1. 최신 기획서에서 요구사항과 정책 후보를 분리한다.
2. 기존 `docs/policies`와 비교해 신규/변경/삭제/충돌 정책을 찾는다.
3. 확정된 정책은 domain 또는 feature 정책 문서에 누적한다.
4. 미확정 내용은 정책으로 단정하지 않고 `QA 확인 필요` 또는 `Open Questions`에 남긴다.
5. Figma 기준 화면명, 버튼명, 문구가 있으면 정책 문서의 화면/문구 기준에 반영한다.
6. TC 생성 시 `app/core/policy_loader.py`가 관련 정책을 자동으로 읽게 한다.
7. 생성된 TC의 `source_policy`, `related_policy`, `traceability`로 정책 근거를 추적한다.
8. Excel export 전 open question, 정책 충돌, 누락 케이스를 확인한다.

## 정책으로 남길 항목

- 이번 기획서에서 새로 추가된 정책
- 기존 정책에서 변경된 부분
- 예외 케이스
- 상태값과 상태 전이
- 노출/미노출 조건
- 권한/사용자 유형별 차이
- 화면 진입 경로
- Figma 기준 버튼명/문구/화면명
- 확정되지 않은 open question

## 정책 문서 선택 기준

- 회사 공통 QA 기준: `docs/policies/global/`
- 서비스 공통 용어: `docs/policies/domain/domain_terms.md`
- 쿠폰 공통 정책: `docs/policies/domain/coupon_policy.md`
- 예약 공통 정책: `docs/policies/domain/booking_policy.md`
- 결제/가격 공통 정책: `docs/policies/domain/payment_policy.md`
- 예약내역 공통 정책: `docs/policies/domain/booking_history_policy.md`
- 특정 기능/배포 메모: `docs/policies/feature/`

## 충돌 처리

정책 충돌 시 우선순위는 아래 순서를 따른다.

1. 현재 기획서에 명시된 내용
2. 해당 기능/도메인 정책 문서
3. 회사 공통 QA 정책
4. 기존 도메인 용어/관례
5. 추론

현재 기획서와 기존 정책이 충돌하면 현재 기획서를 우선하되, 바로 단정하지 않고 TC의 `notes`, `quality_warnings`, 분석 결과의 `open_questions`에 확인 필요 내용을 남긴다.

## TC 생성 요청 예시

```text
첨부한 기획서 기준으로 TC 작성해줘.
기존 정책은 docs/policies 기준으로 참고해줘.
특히 coupon_policy.md, booking_policy.md, testcase_style_guide.md 반영해줘.
Figma context도 같이 참고해서 테스트 진행 화면/Step/Expected Result를 작성해줘.
```

## 정책 업데이트 요청 예시

```text
이 기획서에서 확정된 쿠폰/예약 정책만 docs/policies에 업데이트해줘.
기존 정책과 충돌하는 부분은 바로 덮어쓰지 말고 QA 확인 필요로 남겨줘.
```
