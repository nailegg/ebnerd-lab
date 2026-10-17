# PLAN

갱신: 2026-10-17 (Architect). 미래만 적는다. 진행 중인 것은 `STATE.md`, 끝난 것은 `history/`. 규칙은 `AGENTS.md` §6.

## 국면

1. **hidden test 점수 최대화**(현재). 만족선: Codabench AUC 0.85.
2. **자체 validation protocol 연구.** 1이 만족선에 닿으면 시작. 전환 시 `AGENTS.md` §2의 "test 파일에 존재" 조항을 다시 본다.

## 국면 1 마일스톤

| | 마일스톤 | 내용 | 의존 | 목표 |
|---|---|---|---|---|
| M1 | 끝에서 끝까지 한 번 | 진행 중 → `STATE.md` | — | 점수 경로 검증 |
| M2 | 시간 경계 인기도 | 모든 사용자의 t 이전 inview 수 집계(QA, "같은 시각 두 이벤트" 케이스, BA 행 제외). `features/<version>` 규칙. 인기도 순위 제출 | M1 | 로컬–hidden 대응점 하나 더 |
| M3 | 첫 모델 | M2 집계 + history 피처(공식 벡터 유사도, category 일치) + 기사 메타 → LightGBM lambdarank. run_id · seed · 설정 스냅샷 규칙. 유사도 피처와 인코더 선택 절차 → `docs/design/models.md` 3절 | M2 | AUC 0.70 |
| M4 | GPU 모델 | 후보 설계 모델 A · B → `docs/design/models.md`. 채택은 시작 시 State 결정. vast.ai. 전송 수단 결정 | M3 | AUC 0.80 |
| M5 | 앙상블 · 튜닝 | | M4 | AUC 0.85(만족선) |

## 시점이 오면 정할 것

- `features/<version>` 규칙 — M2 시작 시. 유력안: 빌드 커밋 short SHA + manifest(커밋 · 입력 sha256 · 생성 시각).
- run_id · seed · 설정 스냅샷 규칙 — M3 시작 시.
- 로컬 ↔ vast.ai 전송 수단(외부 버킷 vs 직접 전송) — M4 시작 시. 권장: Cloudflare R2 + rclone.
