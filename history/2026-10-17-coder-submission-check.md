# 2026-10-17 Coder — U7 제출 검사 + test 스키마 연쇄 테스트

## 범위

`scripts/make_submission.py`, `tests/test_submission.py`. 다른 스크립트 · 모듈은 손대지 않았다.

## 구현

- `make_submission.py`에 `--split` 추가. `check_ranks(ranks, behaviors)`가 zip 쓰기 전에 네 검사를 순서대로 한다: 행 수 → `impression_id` 열(순서 포함, `Series.equals`) → 행별 `ranks` 길이 = `article_ids_inview` 길이 → 행별 순열(`list.sort() == int_ranges(1, n+1)`). 첫 실패에서 어떤 검사인지 담은 `SystemExit`. 모두 polars 표현식 · Series 연산, explode 없음.
- `int_ranges`의 dtype은 ranks 파일의 list 내부 dtype(`ranks.schema["ranks"].inner`)을 그대로 써서 dtype 불일치로 비교가 깨지지 않게 했다(recency ranks는 Int32).
- 테스트: 기존 validation형 fixture를 확장해 같은 tmp root 아래 `validation/`과 `test/` 두 split을 쓴다(fixture 하나, 둘째 fixture보다 짧음). test형은 라벨 열 없음, `is_beyond_accuracy` 있음, `impression_id` 0 행 두 개, 금지 열 `read_time` · `scroll_percentage` 포함. 추가 테스트: (b) `rank_recency → make_submission` 연쇄가 test형에서 통과하고 zip 줄이 기대와 같음, `evaluate`는 `ColumnNotFoundError`; (c) 순위가 중복된 ranks 파일은 `SystemExit(match="permutation")`이고 zip이 생기지 않음.

## 가정

- 검사 실패 메시지 문구는 명세에 없어 자유롭게 정했다. 테스트는 `permutation` 단어만 매칭.
- 행 수 불일치 케이스는 따로 테스트하지 않았다(명세 (c)는 "하나").

## 검증

- `uv run pytest`: 28 passed. `uv run ruff check .`: All checks passed.
- 작업 중 Architect의 `uv sync`가 돌고 있어 `uv run`이 venv lock에서 대기했다. 그 동안은 `.venv/bin/python`으로 테스트했고, sync가 끝난 뒤 `uv run`으로 다시 확인했다.

## 실데이터 (d)

`EBNERD_DATA_ROOT=/home/oans/ebnerd-data systemd-run --user --scope -p MemoryMax=11G --quiet -- /usr/bin/time -v uv run python scripts/make_submission.py --split test --ranks .../runs/recency/test_ranks.parquet --out .../runs/recency/predictions_recency.zip`

- 네 검사 모두 통과, exit 0. Elapsed 12:01.79, Max RSS 6,249,856 kB(약 6.0 GB).
- zip sha256: 실행 전 `ac40e06be591bd13e80fb841d0d43209b43078decc996f53993091fbb3e32705`, 실행 후 동일. zip 안 `predictions.txt`는 1980-01-01 고정 타임스탬프로 써지므로 내용이 같으면 zip 바이트도 같다(내부 파일 sha256 `e903903a…a7eb`, 703,062,222 B). 제출한 zip과 바이트 단위로 같다.
