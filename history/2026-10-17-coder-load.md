# 2026-10-17 Coder — U3 로더

## 단위

STATE.md "U3 로더 명세". 범위: `src/ebnerd/prepare/load.py`, `tests/test_load.py`.

## 구현

- `_raw_dir()`: `$EBNERD_DATA_ROOT/raw`. 환경 변수가 없으면 `KeyError`(별도 처리 없음).
- `load_behaviors(split)`: `scan_parquet` → 스키마에 `is_beyond_accuracy`가 없으면 `pl.lit(False)`로 추가 → 12개 열을 고정 순서로 `select` → `collect`. 행 순서는 파일 순서.
- `load_labels(split)`: `impression_id, article_ids_clicked`만 `select`. 열이 없으면 polars가 `ColumnNotFoundError`를 내므로 별도 검사를 두지 않았다.
- `load_history(split)`, `load_article_vectors()`: `read_parquet` 그대로.
- `load_articles()`: `total_inviews, total_pageviews, total_read_time`을 `drop`.
- 열 목록은 모듈 상수(`BEHAVIOR_COLUMNS`, `LABEL_COLUMNS`, `ARTICLE_AGGREGATE_COLUMNS`). 테스트가 `BEHAVIOR_COLUMNS`를 import해 (a)를 확인한다.

## 가정

- "열이 없는 파일에서는 예외"는 polars 기본 예외(`ColumnNotFoundError`)로 충분하다고 봤다. 테스트는 그 타입으로 고정했다.
- `is_beyond_accuracy`를 채울 때 dtype은 `Boolean`. 실데이터 test의 dtype과 같다.
- 합성 테스트 parquet에는 금지 열(`read_time`, `scroll_percentage`, `article_id`, `next_*`, `total_*`)을 일부러 넣어 로더가 떨어뜨리는지 본다.
- `tests/`에 `__init__.py`를 두지 않았다. `uv_build`가 `ebnerd`를 설치하므로 import는 그대로 된다.

## 실데이터 확인(테스트에 넣지 않음)

`EBNERD_DATA_ROOT=/home/oans/ebnerd-data`:

- `load_behaviors("test")`: 열 (a) 정확히 12개, 13,536,710행, `is_beyond_accuracy` 합 200,000.
- `load_behaviors("validation")`: 같은 열, 12,566,385행, BA 합 0.
- `load_labels("validation")`: 2열, 12,566,385행.
- `load_labels("test")`: `ColumnNotFoundError: unable to find column "article_ids_clicked"`.
- `load_articles()`: 18열(총 21에서 3개 제거), 125,541행.
- `load_article_vectors()`: 2열, 125,541행. `load_history("test")`: 5열, 807,677행.

## 검증

- `uv run pytest`: 7 passed.
- `uv run ruff check .`: All checks passed. `ruff format --check`도 통과.
