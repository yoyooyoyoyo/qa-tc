# Policy Context

이 폴더는 테스트케이스 생성 시 자동으로 참조할 회사/서비스 정책을 레이어별로 관리하는 공간이다.

## Policy Layers

### 1. Global Policy

경로: `docs/policies/global/`

- 회사 QA 기준
- Priority 기준
- 테스트케이스 작성 스타일
- 결함 등록 기준
- 릴리즈 체크 기준

현재 파일:

- `global/qa_policy.md`: QA 범위, 필수 검증 관점, 테스트 우선순위 기준
- `global/focus_policy.md`: 핵심 기능 선별, 비핵심 축약, 엣지케이스 확장 기준
- `global/testcase_style_guide.md`: TC title/steps/expected result 작성 규칙
- `global/defect_policy.md`: pass/fail/blocked/fixed 및 이슈 등록 기준
- `global/release_checklist.md`: 배포 전 회귀/스모크 체크 기준

### 2. Domain Policy

경로: `docs/policies/domain/`

- 서비스 공통 용어
- 화면/메뉴 경로
- 예약, 쿠폰, 검진, 결제, 기업검진, CRM, PMS 등 도메인 공통 기준

현재 파일:

- `domain/domain_terms.md`: 서비스 용어, 화면 경로, 상태값, 쿠폰/가격 용어 정의
- `domain/coupon_policy.md`: 쿠폰 유형, 노출/hide, 실패, 어드민 쿠폰 상태 정책
- `domain/booking_policy.md`: 예약 상태, 예약/결제 화면 구성, 예약 변경/취소, 버튼 정책
- `domain/payment_policy.md`: 결제금액 구성, 가격 산식, 툴팁, 0원 결제, B2B 지원금 정책
- `domain/booking_history_policy.md`: 예약내역 카드/상세, 결제정보, 영수증/확인서, 버튼 정책

### 3. Feature Policy

경로: `docs/policies/feature/`

- 특정 기능 또는 화면군의 누적 정책
- 이전 기획서 분석 결과
- 기능별 상태/노출/버튼/문구/금액 정책

현재 파일:

- `feature/app_v20_coupon_booking_policy_notes.md`: App v20 쿠폰/예약 정책 참고 메모
- `feature/booking_history_policy_notes.md`: 예약내역 정책 참고 메모

## Current Spec / Figma Context

- Current Spec: 사용자가 Swagger 또는 대화로 업로드하는 이번 기획서
- Figma Context: Figma MCP 또는 Figma API로 가져온 화면명, 버튼명, 문구, 화면 구조

이 둘은 `docs/policies`에 누적 저장하지 않고, TC 생성 요청 시 입력 컨텍스트로 사용한다.

## Policy Update Workflow

최신 기획서는 그대로 정책 문서에 붙이지 않는다. 최신 기획서에서 앞으로도 반복 적용할 확정 정책만 추출해 `docs/policies`에 누적한다.

정책 업데이트 시 아래 항목을 확인한다.

- 이번 기획서에서 새로 추가된 정책
- 기존 정책에서 변경된 부분
- 예외 케이스
- 상태값과 상태 전이
- 노출/미노출 조건
- 권한/사용자 유형별 차이
- 화면 진입 경로
- Figma 기준 버튼명/문구/화면명
- 확정되지 않은 open question

에이전트 작업 순서는 `docs/skills/tc_policy_update_workflow.md`를 따른다.

## Policy Priority

정책 충돌 시 우선순위는 아래 순서를 따른다.

1. 현재 기획서에 명시된 내용
2. 해당 기능/도메인 정책 문서
3. 회사 공통 QA 정책
4. 기존 도메인 용어/관례
5. 추론

기존 정책과 현재 기획서가 충돌하면 현재 기획서를 우선하되, `open question` 또는 `notes`에 충돌 내용을 남긴다.

예:

```text
기존 정책상 쿠폰 적용은 결제 단계 기준이나, 이번 기획서에서는 상품 상세 선노출이 추가됨.
상세 화면의 쿠폰 배지는 실제 적용 가능 여부 기준인지, 단순 혜택 안내 기준인지 확인 필요.
```

## Auto Injection Rule

TC 생성 시 기본 정책은 항상 주입한다.

- `global/*.md`
- `domain/domain_terms.md`

도메인별/기능별 정책은 현재 기획서, 요구사항, Figma context의 키워드로 관련 있을 때만 주입한다.

- coupon/쿠폰 관련: `domain/coupon_policy.md`, `feature/app_v20_coupon_booking_policy_notes.md`
- booking/reservation 관련: `domain/booking_policy.md`, `feature/booking_history_policy_notes.md`
- booking history/예약내역 관련: `domain/booking_history_policy.md`, `feature/booking_history_policy_notes.md`
- payment/price 관련: `domain/payment_policy.md`

정책 문서는 모델 학습 대상이 아니라 런타임 컨텍스트다. 정책이 바뀌면 이 문서를 수정하고, 에이전트가 다음 TC 생성부터 새 정책을 읽도록 한다.
