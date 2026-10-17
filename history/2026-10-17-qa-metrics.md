# QA: U4 공식 지표 (2026-10-17)

## 입력

`STATE.md` "U4 공식 지표 명세"만 보고 작성. Coder 구현 `src/ebnerd/eval/metrics.py`는 존재하지 않았고 열지 않았다.

## 산출물

- `tests/test_metrics_qa.py`
  - 정답 구현 `reference_metrics`: impression별 순수 Python 루프. `_ranks`(Python `sorted`의 stable 정렬, score 내림차순, 동률은 입력 순서), `_auc`(양성×음성 O(n²) 쌍 비교, 동률 0.5), `_mrr`(양성마다 1/순위 합 ÷ 양성 수), `_dcg`/`_ndcg`(gain 2^label−1, 할인 1/log2(순위+1), 상위 k, 이상 DCG로 정규화). 연속 블록 단위로 group 경계를 찾아 impression 평균.
  - 손 계산 사례: A(후보 2, 완벽), B(후보 5, 0.5 삼중 동률 중 음성이 앞, 양성 2개), C(후보 12, 양성이 순위 1·7이라 nDCG@5≠nDCG@10).
  - 동률 순서 테스트(같은 점수 두 후보에서 양성의 입력 위치에 따라 MRR 1.0 vs 0.5).
  - 비연속 group id 테스트(7,7,7,42,42).
  - 난수 사례: seed 0·1·2, impression 200개, 후보 2–30, score를 {0, .25, .5, .75, 1} 5단계로 양자화해 동률 다수, 양성·음성 각 1개 이상 보장, group id는 간격이 불규칙한 증가 정수. 정답과 1e-9 안 일치 요구.

## 검증 결과

- `uv run ruff check tests/test_metrics_qa.py`: 통과.
- `uv run pytest tests/test_metrics_qa.py`: `ModuleNotFoundError: No module named 'ebnerd.eval.metrics'`로 수집 단계에서 실패. 구현 부재이므로 정상.
- 정답 구현 자체 검증(scratchpad에서 구현 모듈을 stub으로 대체하고 `-k reference`만 실행): 7개 통과.
  - 손 계산 3사례와 일치.
  - 단일 양성 완벽 순위 → 네 지표 모두 1.0.
  - 양성 3개 완벽 순위 → AUC·nDCG 1.0, MRR = (1+1/2+1/3)/3.
  - 양성이 모두 뒤 → AUC 0.0, MRR·nDCG@10은 손 계산값, nDCG@5 0.0.
  - 동률 2후보에서 입력 순서가 순위를 결정.
  - 난수 사례(score와 label 독립)에서 AUC ≈ 0.50–0.52로 기대 범위.

## 작업 중 수정

처음에 "완벽한 순위면 모든 지표 1.0"을 양성 3개 사례에 적용했다가 정답 구현이 MRR 0.611을 내서 실패. 명세의 MRR(양성마다 1/순위를 더해 양성 수로 나눔)은 양성이 2개 이상이면 완벽 순위에서도 1 미만이다. 정답 구현이 맞고 테스트 기대값이 틀렸으므로 테스트를 둘로 나눴다(단일 양성 → 전부 1.0, 다중 양성 → MRR 손 계산값).

## 명세에서 본 점

1. MRR 정의가 통상의 MRR(첫 양성의 역순위)과 다르다. 명세는 ebnerd-benchmark의 `mrr_score`(모든 양성의 역순위 평균)를 따른다고 명시하므로 그대로 테스트했다. 공식 채점과 같은 식이라면 문제없다.
2. "동률은 입력 순서 유지(stable)"는 명세가 명확하다. 다만 ebnerd-benchmark 원본은 `np.argsort(score)[::-1]`를 써서 동률 순서가 입력의 역순이 되므로 동률이 있는 raw score에서는 명세와 수치가 다를 수 있다. 제출 파이프라인(U5)에서는 순위가 1..n 순열이라 동률이 없으니 실질 영향은 없다. 테스트는 명세(stable)를 강제한다.
3. 같은 group id가 떨어진 두 블록에 다시 나타나는 경우는 명세가 다루지 않는다. 테스트하지 않았다(명세대로 "같은 group은 연속 블록"을 전제).
4. `label` dtype은 int64, `score`는 float64, `group`은 int64로만 호출한다. 반환값은 `isinstance(v, float)`로 확인(`np.float64`도 통과).
