# 2026-10-17 Architect — U5 검증과 WSL 중단

## 중단

첫 U5 실행은 validation 평가 단계에서 WSL VM(상한 15 GB)째 죽었다. 원인: `evaluate.py`가 1.5억 후보를 한 번에 explode하면서 `is_in(pl.col("clicked"))`로 클릭 list를 후보마다 복제했고, `load_behaviors` 전체 열도 메모리에 있었다. 조치: 100만 행 slice로 잘라 impression 수 가중 평균(impression 평균이므로 정확), 클릭은 따로 explode해 join, 실데이터 실행은 `systemd-run --user --scope -p MemoryMax=11G`. 결과 evaluate validation 22초 · 3.2 GB.

## 독립 검증

recency AUC 0.5004가 평가기 버그(라벨 정렬 오류)여도 같은 숫자가 나오므로 스크래치(저장소 밖)에서 validation 앞 300k 행을 독립 재계산했다.

| 점수 | AUC |
|---|---|
| 순위 파일(−rank) | 0.4991 |
| published_time 직접 | 0.4991 |
| `total_inviews`(금지 열, 검증용) | 0.5590 |
| 무작위 | 0.5003 |

순위 파일과 재계산이 일치하고 누설 신호는 0.5를 벗어나므로 평가기는 정상. recency가 이 데이터에서 신호가 없는 것이 맞다(후보 나이 중앙값 4.4h, 모두 신선). 기준선의 목적은 점수 경로 검증이므로 그대로 제출한다.

## Architect 판정

- Coder 보고 5번(clicked 중복): 사실로 `docs/data.md`에, 처리는 U5 명세에 추가. 수용.
- Coder 보고 1번(`scores_to_ranks` 미사용): K2 위반이므로 함수와 테스트를 제거하고 명세에서 뺐다. 모델 점수→순위가 필요해지는 묶음에서 다시 만든다.
- 테스트의 `importlib` 스크립트 로딩: 허용. 대안(패키지화)이 더 무겁다.
