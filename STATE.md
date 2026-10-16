# STATE

갱신: 2026-10-17 (Architect). 규칙은 `AGENTS.md`. 은퇴한 결정은 `history/*-state-retire.md`.

## 현재 위치

저장소를 재구축하고 외부 시각의 구조 평가를 반영했다. 코드는 없다. 다음은 WSL 세션에서 첫 구현 묶음을 정하는 것이다.

## 현재 묶음

없음. 다음 세션에서 정한다. 후보 단위와 평가에서 나온 성공 기준:

- **환경** — WSL ext4에 clone, `pyproject.toml`에 CUDA 12.8 torch index 명시, `uv lock`, `uv sync` · `pytest` · `ruff` 통과, `uv.lock` 커밋.
- **원본 데이터 복사** — Windows 원본을 `$EBNERD_DATA_ROOT/raw/`로. sha256 확인.
- **로더** — 세 split을 같은 함수로 연다. §2 금지 열을 로드 시 제거, 라벨은 분리 객체로 반환, test 스키마 합성 프레임 스모크 테스트.
- **공식 지표**(QA) — impression 단위 AUC · MRR · nDCG@5 · nDCG@10. 느린 정답 구현과 대조.
- **Codabench 확인**(코드 없음) — hidden test 제출이 아직 가능한지. 불가능하면 D1을 다시 정한다.

## 유효한 결정

- **D1** 점수판은 공식 hidden test 점수. 자체 validation protocol 연구는 그 뒤 후속(국면 2). 국면 전환 시 `AGENTS.md` §2의 "test 파일에 존재" 조항을 다시 본다.
- **D3** test의 beyond-accuracy 행(`impression_id` 0, 200,000개, 같은 시각, 같은 250개 후보)은 모든 집계의 원천 이벤트에서 뺀다. 합성 행이라 노출 수를 부풀린다. 대상 행으로서는 점수를 낸다(제출에 필요). 로더 · feature 코드와 테스트에 체화되면 은퇴.
- **D4** 이전 저장소(EASEM, `Desktop/당근`)의 결정과 코드는 승계하지 않는다. 사실만 `docs/data.md`. 첫 묶음 뒤 국면 종료로 은퇴 예정.
- **D5** 로컬 WSL(CPU)에서 원본 → feature 빌드, vast.ai(GPU)에서 학습. 둘 사이의 전송 수단(외부 버킷 vs 직접 전송)은 첫 학습 직전에 정한다. 그때까지 push/pull 코드는 만들지 않는다. 권장은 Cloudflare R2 + rclone.

## Observer 지적 처리

| 날짜 | 지적 | 처분 | 이유 |
|---|---|---|---|
| — | — | — | — |

## 열린 질문

- hidden test 점수를 확인하는 경로(Codabench). 첫 묶음에서 확인.
- 전송 수단(D5). 첫 학습 직전.
- `features/<version>` 규칙. 첫 feature 빌드 직전. 유력안: 빌드 커밋 short SHA + manifest(커밋 · 입력 sha256 · 생성 시각).
- run_id · seed · 설정 스냅샷 규칙. 첫 학습 직전.

## 한계

`docs/limitations.md`.
