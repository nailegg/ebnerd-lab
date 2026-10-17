# 2026-10-17 Architect — 둘째 묶음 "Plan 도입"

## 경위

사용자가 Codabench 채점 대기 중에 둘째 묶음으로 "워크플로에 Plan 도입"을 지시했다. 맥락은 다른 세션(ebnerd-lab-31)이 사용자 질문("전체 플랜을 두고 Architect가 거기서 작업거리를 State로 떼 오면 어떤가")에 낸 제안이었고, 그 세션은 파일을 고치지 않았다. 제안을 받아 사용자에게 올렸고 사용자가 승인했다.

## 근거

§6 두 번째 질문에 플랜을 넣으면 State인데, 로드맵을 State에 두면 1페이지 목표와 충돌하고 Coder가 다음 단위를 보고 미리 helper를 만드는 K2 유혹이 생긴다. 그래서 질문을 쪼갠다: 끝나는 조건이 있고 진행 중이면 State, 시작 전이면 Plan. 이미 플랜이 STATE 세 곳에 흩어져 있어 §6 "한 곳에만" 위반 상태였다. Plan은 새 층이 아니라 그것들의 통합이다.

## 사용자 승인 사항

- Rule 수정 다섯 곳(AGENTS.md §4 Architect 행, §5 1단계, §5 6단계, §6 두 번째 질문과 층 정의, observer.md 검사 3).
- 자동 로드 안 함(Architect가 세션 시작에 읽음). subagent에는 불필요하고 K2 유혹만 생김.
- Observer 검사 3에 Plan 이탈 확인 추가.
- 만족선 hidden AUC 0.85, 중간 0.70(M3) · 0.80(M4). 숫자는 사용자 검토 중.
- 국면 1 마일스톤 M1 끝에서 끝까지 → M2 시간 경계 인기도 → M3 LightGBM → M4 GPU 모델 → M5 앙상블.

## 이동

STATE 열린 질문 셋(전송 수단, features/<version>, run_id · seed)을 PLAN.md "시점이 오면 정할 것"으로 옮겼다. D5의 "첫 학습 직전에 정한다 · 권장 R2 + rclone"은 Plan M4 항목으로 옮기고 D5는 빌드/학습 위치와 push/pull 금지만 남겼다.
