# 2026-10-17 Coder — U5 recency 기준선 + 평가 · 제출

## 범위와 산출물

- `src/ebnerd/eval/submission.py`: `scores_to_ranks`, `write_predictions_zip`.
- `scripts/rank_recency.py`, `scripts/evaluate.py`, `scripts/make_submission.py`.
- `tests/test_submission.py`: 순위 변환(동률), zip 형식, 합성 데이터로 rank_recency → evaluate → make_submission 연쇄.
- 실데이터 산출물(git 밖): `$EBNERD_DATA_ROOT/runs/recency/{validation_ranks.parquet, test_ranks.parquet, predictions_recency.zip}`.

## 구현 요약

- `rank_recency.py`: behaviors의 `article_ids_inview`를 explode → articles(`article_id, published_time`) left join → `published_time` 결측(기사 표에 없는 후보 포함)은 `datetime(1900, 1, 1)`로 채움(실데이터 최소 1993-09-15보다 이전) → `pl.arg_sort_by(["row", "published_time"], descending=[False, True], maintain_order=True)`로 안정 정렬 순열만 얻고(정렬된 복사본을 만들지 않음) → 순위 = 정렬 위치 − 행 시작 위치 + 1을 numpy로 scatter → `group_by("row", maintain_order=True)`로 list 복원. impression_id로 join하지 않고 행 번호로만 묶는다(test BA 행은 id가 모두 0).
- `evaluate.py`: behaviors · labels · ranks를 `SLICE_ROWS = 1_000_000` 행 단위로 잘라 slice마다 long 배열(group u32, score int32 = −rank, label int8)을 만들고 `impression_metrics`를 부른 뒤 slice의 impression 수로 가중 평균(impression 평균이므로 전체 한 번과 동일). 라벨은 clicked list를 따로 explode해 `(row, article_id)`로 left join(`maintain_order="left"`)하므로 clicked list가 후보마다 복제되지 않는다.
- `make_submission.py`: `df.select("ranks").iter_rows()`(512행 버퍼 변환) 제너레이터를 `write_predictions_zip`에 넘긴다. list Series를 직접 순회하면 원소마다 Series가 만들어져 느리다.
- `write_predictions_zip`: `ZipFile(ZIP_DEFLATED).open("predictions.txt", "w")`를 `TextIOWrapper`로 감싸 한 줄씩 f-string으로 쓴다.

## OOM 사고와 조치

이전 세션의 첫 `evaluate.py`는 validation 전체(1.5억 후보)를 한 번에 explode했고, `pl.col("article_id").is_in(pl.col("clicked"))`를 쓰느라 explode 때 clicked list 열이 후보마다 복제됐으며, `load_behaviors` 전체 열도 메모리에 있었다. WSL VM 상한 15 GB를 넘겨 VM째 죽었다. 조치: (1) 100만 행 slice + 가중 평균, (2) clicked를 별도 explode 후 join, (3) 필요한 열만 `get_column`으로 꺼내 나머지는 즉시 해제, (4) 실데이터 실행은 모두 `systemd-run --user --scope -p MemoryMax=11G` 아래에서. `rank_recency.py`도 `pos` 열과 정렬 복사본을 없애 validation maxrss 8.0 GB → 6.5 GB.

## 구현 중 발견한 데이터 사실

- validation `article_ids_clicked`에 같은 기사가 두 번 들어간 impression이 있다(클릭 12,649,444건 중 고유 12,616,005건, 중복 33,439건). `(row, article_id)` join이 그 후보 행을 두 배로 만들어 지표가 어긋났다. `list.unique()`로 중복을 없앴고 테스트 fixture에 `[15, 15]` 사례를 넣었다(없애지 않으면 MRR 단언이 실패함을 확인). `article_ids_inview`에는 중복이 없고(1억 5,022만 = 고유 수), clicked ⊄ inview인 경우도 없다.
- articles의 `published_time` 결측은 0건. validation 첫 100만 행 후보 중 기사 표에 없는 것도 0건.

## 실데이터 결과(모두 MemoryMax=11G 아래)

| 단계 | Elapsed | maxrss |
|---|---|---|
| rank_recency validation | 0:13.87 | 6.47 GB |
| evaluate validation | 0:21.58 | 3.15 GB |
| rank_recency test | 0:19.55 | 8.19 GB |
| make_submission test | 1:38.02 | 1.11 GB |

validation: `auc=0.5003909760342452`, `mrr=0.30668227636651796`, `ndcg@5=0.33550749077866926`, `ndcg@10=0.4206861377808822`. AUC > 0.5(성공 기준)이지만 사실상 무작위 수준이다.

진단(validation 첫 100만 행, 스크래치 스크립트, 저장소에 넣지 않음): 후보의 impression 시각 대비 기사 나이는 중앙값 4.4시간(p10 0.67h, p90 3,748h). `published_time`을 점수로 직접 쓰면(동률 0.5) AUC 0.5006, 반대로(오래된 순) 0.4994, inview 위치(앞이 최고) 0.4998. 즉 recency 자체가 이 데이터에서 신호가 거의 없다. 동률(같은 `published_time`)이 있는 impression은 0.9%뿐이라 동률 규칙의 영향도 작다. 구현 오류가 아니라 기준선의 성질로 본다.

test zip: `predictions.txt` 하나(deflate, 압축 165,214,552 B / 원본 703,062,222 B), zip 파일 165,214,680 B(158 MB). 13,536,710줄, 형식 `^\d+ \[\d+(,\d+)*\]$`에 어긋나는 줄 0. impression_id 0 줄 200,000개. parquet 단계에서 행 순서가 원본 test behaviors의 impression_id 열과 같고(13,536,710행), 모든 행의 순위가 1..n 순열(n 5–250).

첫 3줄: `6451339 [4,9,2,5,7,1,3,6,8]`, `6451363 [8,2,6,1,3,7,4,5]`, `6451382 [1,4,5,2,3]`. 마지막 2줄은 BA 행 `0 [42,71,165,103,237,154,248,219,49,80,...]`(250개, 두 줄 동일 — 같은 250개 후보).

## 검증

`uv run pytest` 27 passed, `uv run ruff check .` All checks passed.

## 가정 · 명세와 다른 점

- `scores_to_ranks`는 명세대로 만들고 테스트했지만 이 단위의 스크립트는 부르지 않는다(순위는 polars로 전체를 한 번에 계산).
- 결측 `published_time` 채움값은 상수 `datetime(1900, 1, 1)`(표의 최소값 − 1일 대신). 결과는 같다.
- `evaluate.py`의 slice 크기는 모듈 상수 `SLICE_ROWS` 하나. 테스트는 monkeypatch로 2를 넣어 slice 경계(2 + 1행)를 지나게 한다.
- 테스트는 `importlib`로 `scripts/*.py`를 경로에서 로드한다(`scripts/`를 패키지로 만들거나 `pyproject`를 고치지 않기 위해).
