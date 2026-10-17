# STATE

갱신: 2026-10-17 (Architect). 규칙은 `AGENTS.md`. 은퇴한 결정은 `history/*-state-retire.md`.

## 현재 위치

U1–U5 완료. 남은 것은 U6: 사용자가 `$EBNERD_DATA_ROOT/runs/recency/predictions_recency.zip`을 Codabench에 제출하고 hidden 점수를 받는다. 그 뒤 Observer 검토.

## 현재 묶음: 끝에서 끝까지 한 번

원본 → 로더 → 최단 기준선 → 제출 zip → Codabench hidden 점수를 한 줄로 관통해 점수 경로를 검증하고, 로컬 validation 점수와 hidden 점수의 첫 대응점을 얻는다.

| 단위 | 담당 | 상태 |
|---|---|---|
| U1 환경: `uv.lock` 커밋, `.env` 경로, `uv sync` · ruff 통과 | Architect | 완료 |
| U2 원본 복사: D7 배치로 복사, sha256을 `docs/data.md`에 기록 | Architect(셸) | 완료 |
| U3 로더 | Coder | 완료 |
| U4 공식 지표 | QA → Coder | 완료 |
| U5 recency 기준선 + 평가 · 제출 스크립트 | Coder | 완료. validation AUC 0.5004 · MRR 0.3067 · nDCG@5 0.3355 · nDCG@10 0.4207 (무작위 수준. 누설 신호 `total_inviews`로 평가기 정상 확인) |
| U6 Codabench 제출, hidden 점수를 이 파일에 기록 | 사용자 + Architect | 대기 |

### U3 로더 명세

- 목표: split 하나의 네 파일을 `AGENTS.md` §2 경계 안의 열만 가진 polars DataFrame으로 읽는다.
- 범위: `src/ebnerd/prepare/load.py`, `tests/test_load.py`.
- 인터페이스: 경로는 `$EBNERD_DATA_ROOT/raw/` + D7 배치. `load_behaviors(split)`, `load_labels(split)`, `load_history(split)`, `load_articles()`, `load_article_vectors()`.
- 성공 기준: (a) `load_behaviors` 반환 열은 정확히 `impression_id, user_id, impression_time, article_ids_inview, device_type, session_id, is_sso_user, gender, postcode, age, is_subscriber, is_beyond_accuracy`. 파일에 `is_beyond_accuracy`가 없으면 False로 채운다. 행 순서는 파일 순서 그대로. (b) `load_labels`는 `impression_id, article_ids_clicked`만 반환하고, 열이 없는 파일(test)에서는 예외. (c) `load_history`는 파일 그대로. (d) `load_articles`는 `total_inviews, total_pageviews, total_read_time`을 뺀 나머지. (e) `load_article_vectors`는 파일 그대로. (f) 테스트는 tmp 디렉터리의 작은 합성 parquet로, train형(라벨 있음 · BA 열 없음)과 test형(라벨 없음 · BA 열 있음) 파일을 같은 함수로 읽어 (a)(b)를 확인.
- 금지: 집계 · feature 계산, split 이름 분기, 호출자가 요청하지 않은 옵션 · 캐시 · 설정.
- QA: 없음.

### U4 공식 지표 명세

- 목표: impression 단위 AUC · MRR · nDCG@5 · nDCG@10을 계산해 impression 평균을 낸다.
- 범위: Coder `src/ebnerd/eval/metrics.py`, `tests/test_metrics.py`. QA `tests/test_metrics_qa.py`(느린 정답 구현 포함).
- 인터페이스: `impression_metrics(group: np.ndarray, score: np.ndarray, label: np.ndarray) -> dict[str, float]`. 세 배열은 같은 길이의 long 형식. `group`은 impression 식별 정수이고 같은 group은 연속 블록이다. `label`은 0 · 1. 반환 키 `auc, mrr, ndcg@5, ndcg@10`.
- 정의(ebnerd-benchmark와 동일): 후보를 score 내림차순으로 정렬, 동률은 입력 순서 유지(stable). AUC는 양성–음성 쌍 중 양성 score가 큰 비율, 동률 쌍은 0.5. MRR은 양성마다 1/순위를 더해 양성 수로 나눈 값. nDCG@k는 gain 2^label−1, 할인 1/log2(순위+1), 상위 k, 이상 DCG로 정규화. 모든 impression은 양성 · 음성이 각각 1개 이상이라고 가정한다(검사하지 않음).
- 성공 기준: QA 테스트 통과. validation 전체(1,257만 impression · 1.5억 행)를 로컬 CPU에서 10분 안에 계산(Architect가 U5에서 확인).
- 금지: 새 의존성(sklearn 등). impression별 Python 루프.
- QA: 있음.

### U5 recency 기준선 + 평가 · 제출 명세

- 목표: 후보를 `published_time` 최신순으로 순위화해 validation 로컬 점수를 내고 test 제출 zip을 만든다.
- 범위: `src/ebnerd/eval/submission.py`, `scripts/rank_recency.py`, `scripts/evaluate.py`, `scripts/make_submission.py`, 각 테스트.
- 인터페이스: `rank_recency.py --split S --out P`는 behaviors 행 순서 그대로 `impression_id, ranks(list)` parquet. `evaluate.py --split S --ranks P`는 행 순서로 라벨과 맞춰 네 지표를 출력(score = −rank). `make_submission.py --ranks P --out Z`는 D6 형식의 zip.
- 성공 기준: validation AUC > 0.5. test zip은 행 수 13,536,710, 행 순서 원본과 동일, 각 행의 순위가 1..n 순열. `published_time` 결측은 가장 오래된 것으로 취급(1900-01-01로 채움). `article_ids_clicked`에 같은 기사가 두 번 든 impression이 있으므로(`docs/data.md`) 라벨은 중복 제거 후 만든다.
- 메모리: WSL VM 상한 15 GB. `evaluate.py`는 behaviors를 100만 행 단위로 잘라 slice마다 long 배열(int32)을 만들어 `impression_metrics`를 부르고, slice의 impression 수로 가중 평균한다(impression 평균이므로 정확히 같다). 실데이터 실행은 `systemd-run --user --scope -p MemoryMax=11G`로 상한을 건다.
- 금지: 모델 학습, feature 저장, split 이름 분기.
- QA: 없음.

## 유효한 결정

- **D1** 점수판은 공식 hidden test 점수. 자체 validation protocol 연구는 그 뒤 후속(국면 2). 국면 전환 시 `AGENTS.md` §2의 "test 파일에 존재" 조항을 다시 본다.
- **D3** test의 beyond-accuracy 행(`impression_id` 0, 200,000개, 같은 시각, 같은 250개 후보)은 모든 집계의 원천 이벤트에서 뺀다. 합성 행이라 노출 수를 부풀린다. 대상 행으로서는 점수를 낸다(제출에 필요). 로더 · feature 코드와 테스트에 체화되면 은퇴.
- **D4** 이전 저장소(EASEM, `Desktop/당근`)의 결정과 코드는 승계하지 않는다. 사실만 `docs/data.md`. 첫 묶음 뒤 국면 종료로 은퇴 예정.
- **D5** 로컬 WSL(CPU)에서 원본 → feature 빌드, vast.ai(GPU)에서 학습. 둘 사이의 전송 수단(외부 버킷 vs 직접 전송)은 첫 학습 직전에 정한다. 그때까지 push/pull 코드는 만들지 않는다. 권장은 Cloudflare R2 + rclone.
- **D6** 제출은 Codabench 2469 phase "EB-NeRD official testset"(종료일 없음, 하루 5회). 형식: `predictions.txt`만 담은 zip, 한 줄 `impression_id [순위,...]`, 행 순서는 test behaviors 원본, 순위 1..n(1이 최고). BA 행은 id 0이지만 행 순서로 채점한다. 점수→순위 동률은 입력 순서.
- **D7** 원본 배치: `$EBNERD_DATA_ROOT/raw/{articles,contrastive_vector}.parquet`, `raw/{train,validation,test}/{behaviors,history}.parquet`. test 동봉 articles는 sha 동일이라 두지 않는다. 복사 스크립트는 만들지 않고 sha256만 기록.
- **D8** 첫 기준선은 recency(기사 메타만). "t 이전 노출 수" 인기도는 시간 경계 QA가 필요하므로 둘째 묶음.

## Observer 지적 처리

| 날짜 | 지적 | 처분 | 이유 |
|---|---|---|---|
| — | — | — | — |

## 열린 질문

- 전송 수단(D5). 첫 학습 직전.
- `features/<version>` 규칙. 첫 feature 빌드 직전. 유력안: 빌드 커밋 short SHA + manifest(커밋 · 입력 sha256 · 생성 시각).
- run_id · seed · 설정 스냅샷 규칙. 첫 학습 직전.

## 한계

`docs/limitations.md`. 추가: Codabench는 조직자가 직접 돌리는 worker라 예고 없이 멈출 수 있다(2025-07 한 차례, 8월 복구).
