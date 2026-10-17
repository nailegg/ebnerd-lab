# 2026-10-17 Coder — U4 공식 지표 구현

## 단위

STATE.md "U4 공식 지표 명세". QA 테스트 `tests/test_metrics_qa.py`가 먼저 있었고, 그것을 통과시키는 것이 목표.

## 바꾼 파일

- `src/ebnerd/eval/metrics.py` (신규): `impression_metrics(group, score, label) -> dict[str, float]`.
- `tests/test_metrics.py` (신규): QA가 다루지 않은 것만 — int32/float32/int8 입력이 int64/float64와 같은 결과(반환 키 집합 · float 타입 포함).

## 구현 요지

1. `np.lexsort((-score, group))`로 (group 오름차순, score 내림차순, 입력 순서 유지) 안정 정렬.
2. group 경계 `starts`는 정렬된 group의 인접 비교로, 동률 run 경계 `run_starts`는 (group, score) 인접 비교로 잡는다. 정렬 뒤에는 같은 (group, score)가 연속이므로 run이 곧 동률 집합이다.
3. 그 뒤 계산은 **양성 행만** 대상으로 한다. `pos = flatnonzero(label)`에서 `searchsorted`로 각 양성의 impression 번호와 run 번호를 얻고, 순위(1..n)와 동률 평균 순위(run 시작·끝 순위의 평균)를 구한다. 나머지 집계는 `np.bincount(imp, weights=...)`.
4. AUC는 Mann–Whitney: 오름차순 평균 순위 합 − n_pos(n_pos+1)/2, 나누기 n_pos·n_neg. 동률 평균 순위가 명세의 "동률 쌍 0.5"와 같다.
5. MRR = Σ(1/rank)/n_pos. nDCG@k = Σ_{rank≤k} 1/log2(rank+1), 이상 DCG는 min(n_pos, k)개 양성을 1..k 순위에 둔 누적표.
6. impression별 Python 루프 없음. 클래스 · 옵션 없음. 새 의존성 없음.

## 가정

- `label`은 `!= 0`으로 bool화한다(명세 0 · 1).
- `score`에 NaN이 없고 정수형이면 signed라고 본다(`-score`로 내림차순을 만들기 때문). 명세 범위 밖이라 검사하지 않는다.
- 양성 · 음성이 각각 1개 이상이라는 명세 가정에 기대어 0 나눗셈을 검사하지 않는다.
- 결과는 순위에만 의존하므로 float32 score도 순서가 같으면 float64와 정확히 같은 값을 돌려준다. 테스트는 이것을 확인한다.

## 검증

- `uv run pytest -q`: 24 passed (QA 16 + load 7 + 신규 1).
- `uv run ruff check .`: All checks passed.
- 벤치마크(합성, impression당 5–19 후보, 양성 1개, 스크립트는 scratchpad에만 두고 커밋하지 않음):
  - 10,204,210행 / 850,000 impression: 3.0초. maxrss 0.30 → 0.74GB (입력 0.24GB 별도, 증가분 ≈ 43 B/row).
  - 50,404,504행 / 4,200,000 impression: 17.9초. maxrss 1.32 → 3.42GB (입력 1.21GB 별도, 증가분 ≈ 42 B/row).
  - 1.5억 행으로 외삽: 약 60초, 입력 3.6GB 외 추가 ≈ 6.3GB. 로컬 15GB RAM 안이고 10분 목표 안. 정확한 수치는 U5에서 Architect가 실데이터로 확인.

## 범위 밖 발견

- 없음.
