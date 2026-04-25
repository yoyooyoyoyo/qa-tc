# Defect Policy

## Test Result 기준

- pass: 실제 결과가 expected result와 일치한다.
- fail: 실제 결과가 expected result와 다르거나 기능이 동작하지 않는다.
- blocked: 환경, 데이터, 권한, 선행 결함 때문에 테스트를 진행할 수 없다.
- fixed: 이전에 fail이었던 항목이 수정되어 재검증 완료되었다.

## 이슈 등록 기준

- fail인 경우 원칙적으로 issue ticket을 등록한다.
- blocked가 반복되거나 일정에 영향을 주면 issue ticket을 등록한다.
- 동일 원인의 결함은 하나의 대표 issue ticket에 연결하고 comment에 영향 범위를 기록한다.

## Comment 작성 기준

- 재현 경로
- 입력 데이터
- 실제 결과
- 기대 결과와의 차이
- 발생 환경
- 첨부 자료 위치 또는 로그 요약

## Severity 기준

- Critical: 서비스 주요 플로우 차단, 결제/예약/로그인/권한/개인정보 문제
- Major: 핵심 기능 일부 실패, 잘못된 데이터 저장/노출, 주요 예외 처리 누락
- Minor: 비핵심 UI, 문구, 정렬, 안내 표시 문제

## Priority 기준

- High: 배포 전 수정 필요
- Medium: 배포 전 수정 권장 또는 다음 패치 포함
- Low: 후속 개선으로 처리 가능
