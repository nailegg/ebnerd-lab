# 2026-10-17 Architect — 첫 묶음 결정

## 맥락

WSL ext4로 clone한 첫 세션. Windows 원본은 `/mnt/c/EASEM-data/raw`(articles · 벡터 · train · validation)와 `/mnt/c/ebnerd-data/raw/test`(test 동봉본, articles는 sha 동일).

## 확인한 사실

- Codabench 2469 API(`/api/competitions/2469/`): phase "EB-NeRD official testset"이 Current, 종료일 없음, max_submissions_per_day 10(안내문은 5). 제출 형식은 `docs/data.md`에 옮겼다.
- codabench 이슈 #1951: 2025-07-26 조직자 worker 고장, 08-03 복구. 외부 의존이라 한계로 적었다.
- `.env`의 데이터 루트가 이전 사용자명(`naile`) 기준이라 `/home/oans/ebnerd-data`로 고쳤다. `uv.lock`은 미커밋 상태였다.
- 원본 7개 parquet 합계 약 5.3 GB. ext4 여유 925 GB.

## 사용자와 결정한 것

사용자에게 세 가지를 물었다. (1) 묶음 범위: STATE 후보 다섯(기반만) vs 기준선 · 제출기를 더해 hidden 점수까지 관통 → **관통**. (2) 최단 기준선: published_time 최신순 vs t 이전 inview 인기도 vs 무작위 → **recency**(기사 메타만 쓰므로 시간 경계 QA 불필요). (3) Codabench 계정 → **있음, 제출 가능**.

관통을 권한 이유: 점수 경로(형식 · 행 순서 · BA 처리 · 채점 대기)를 모델 전에 검증하고, 로컬 validation과 hidden의 첫 대응점을 얻는다.

## Architect가 정한 것(D6 · D7 · D8)

- D7 raw 배치와 "복사 스크립트 없음". 한 번 하는 일이라 셸로 하고 sha256만 기록(K2).
- D6 제출 형식과 동률 처리(입력 순서).
- U4 인터페이스를 long 형식(group · score · label)으로 못 박았다. impression별 Python 루프는 1,257만 impression에서 비현실적이라 금지했고, QA와 Coder가 같은 시그니처를 보게 했다.
- U5를 세 스크립트(rank · evaluate · make_submission)로 나눴다. evaluate와 make_submission은 모든 모델이 쓸 것이고, "split 이름 분기 금지"를 지키면서 라벨 유무를 다루는 가장 단순한 길이다.

## 열린 질문에서 닫은 것

"hidden test 점수를 확인하는 경로" → 닫음(D6).
