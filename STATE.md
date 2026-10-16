# STATE

갱신: 2026-10-17 (Architect). 규칙은 `AGENTS.md`. 은퇴한 결정은 `history/*-state-retire.md`.

## 현재 위치

저장소를 재구축했다. 코드는 없다. 다음은 WSL 세션에서 첫 구현 묶음을 정하는 것이다. 후보: WSL 환경과 `uv.lock`, 원본 데이터를 WSL 디스크로 복사, 원본 parquet 로딩과 공식 지표(AUC · MRR · nDCG@5 · nDCG@10) 구현.

## 유효한 결정

- **D1** 점수판은 공식 hidden test 점수. 자체 validation protocol 연구는 그 뒤 후속.
- **D2** 입력 경계: test 파일에 있고 t보다 엄격히 이전인 정보만. 지연은 흉내 내지 않는다. 기사 메타는 최종 snapshot을 쓴다(한계). 상세는 `AGENTS.md` §2.
- **D3** test의 beyond-accuracy 행(`impression_id` 0, 200,000개, 같은 시각, 같은 250개 후보)은 모든 집계의 원천 이벤트에서 뺀다. 합성 행이라 노출 수를 부풀린다. 대상 행으로서는 점수를 낸다(제출에 필요).
- **D4** 이전 저장소(EASEM, `Desktop/당근`)의 결정과 코드는 승계하지 않는다. 데이터 · 도구에 관한 사실만 `docs/data.md`에 둔다.
- **D5** 데이터 흐름: 로컬 WSL(CPU)에서 원본 → feature 빌드, vast.ai(GPU)에서 학습. 둘 사이의 전송 수단(외부 버킷 vs 직접 전송)은 첫 학습 직전에 정한다. 그때까지 push/pull 코드는 만들지 않는다.
- **D6** 환경: WSL2 Ubuntu, Python 3.11, uv, polars · pyarrow · torch · lightgbm, pytest · ruff.
- **D7** QA는 Architect가 지정한 단위에만 붙는다(시간 경계가 있는 feature, 평가 지표). 나머지는 Coder가 테스트까지 쓴다.
- **D8** Observer는 묶음 끝에 한 번, 보고만. 보고서는 원문 그대로 사용자에게 전달. Architect는 지적마다 수용 · 기각과 이유를 아래 표에 적는다. State 은퇴도 Observer 제안 → Architect 결정(`AGENTS.md` §6).
- **D9** git: `main` 하나. 커밋은 Architect가 단위마다. 커밋 메시지 영어.
- **D10** 문서는 한국어, 코드 · 커밋은 영어.

## Observer 지적 처리

| 날짜 | 지적 | 처분 | 이유 |
|---|---|---|---|
| — | — | — | — |

## 열린 질문

- hidden test 점수를 확인하는 경로(Codabench 제출이 아직 열려 있는지).
- 전송 수단(D5). 권장은 Cloudflare R2 + rclone.
- vast.ai 이미지(Python 3.11 · CUDA 12.x 계열 PyTorch 공식 이미지 예정).

## 한계

- 기사 메타의 최종 snapshot 사용(`docs/limitations.md`).
