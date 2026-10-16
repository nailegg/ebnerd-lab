# 데이터 사실

EB-NeRD Large와 공식 test set에 대해 확인된 사실. 결정이 아니라 사실만 적는다. 결정은 `STATE.md`.

## Split

| split | 노출 기간(dataset-naive 시각, `[시작, 끝)`) | impression 행 | 후보 행(Σ inview 길이) | 라벨 |
|---|---|---|---|---|
| train | 2023-05-18 07:00 – 05-25 07:00 | 12,063,890 | 133,810,641 | 있음 |
| validation | 2023-05-25 07:00 – 06-01 07:00 | 12,566,385 | 150,228,869 | 있음 |
| test | 2023-06-01 07:00 – 06-08 07:00 | 13,536,710 (BA 200,000 포함) | 205,925,868 (BA 50,000,000 포함) | 없음 |

- `behaviors.parquet` 주요 열: `impression_id`, `user_id`, `impression_time`, `article_id`(현재 페이지, 결측 가능), `article_ids_inview`(후보 list), `article_ids_clicked`(라벨, train · validation만), `read_time`, `scroll_percentage`, `device_type`, `session_id`, `is_sso_user`, `gender`, `postcode`, `age`, `is_subscriber`, `next_read_time`, `next_scroll_percentage`.
- test에는 `article_id`, `article_ids_clicked`, `next_read_time`, `next_scroll_percentage`가 없고 `is_beyond_accuracy`가 있다.
- `history.parquet`: split 노출 기간 직전 21일의 클릭. 사용자당 4개 list: `impression_time_fixed`, `scroll_percentage_fixed`, `article_id_fixed`, `read_time_fixed`. 사용자 수 train 788,090 / validation 791,582 / test 807,677.
- 시각은 timezone 정보가 없는 naive 값이다.

## Beyond-accuracy(BA) 행

- test에 200,000개. `impression_id`가 전부 0이라 key로 쓸 수 없다. 전부 2023-06-01 07:00:01, 후보는 같은 250개 기사.
- 그 250개 기사는 일반 test 후보 칸의 약 14.85%를 차지한다. BA 행을 노출 집계에 넣으면 test 시작 직후 그 기사들의 노출 수가 200,000씩 부풀려진다.
- `scroll_percentage` 결측 여부와 `article_id` 결측 여부는 train · validation에서 약 0.99 일치한다(현재 페이지가 front page인지의 대리 신호).

## 기사

- `articles.parquet` 125,541개. test 동봉본과 sha256이 같다. 주요 열: `article_id`, `title`, `subtitle`, `body`, `category`, `category_str`, `subcategory`, `topics`, `sentiment_score`, `sentiment_label`, `published_time`, `last_modified_time`, `premium`, `article_type`, `url`, `ner_clusters`, `entity_groups`, `image_ids`, `total_inviews`, `total_pageviews`, `total_read_time`.
- 값은 최종 snapshot이다. `last_modified_time`이 노출 시각 이후인 기사가 있다.
- topic 문자열은 78종, `published_time` 결측 기사가 있다.
- 공식 기사 벡터 `Ekstra_Bladet_contrastive_vector`: 125,541개, 768D. 어떤 텍스트(본문 포함 여부)로 만들었는지는 확인되지 않았다.

## 이 PC의 원본 위치(읽기 전용)

- train · validation · 기사 · 벡터: `C:\EASEM-data\raw\`
- hidden test: `C:\Users\naile\Desktop\당근\data\ebnerd_testset` (사본 `C:\ebnerd-data\raw\test`, sha256 검증됨)
- 이전 저장소 문서 사본: `C:\ebnerd-data\archive\`

## 도구 · 하드웨어

- 로컬: Windows 11, Ryzen 5 7500F(6코어 12스레드), 32 GB RAM, RTX 4060 Ti 8 GB.
- DuckDB 1.5.5(Windows)는 사용자–기사 쌍 9,616만 개의 정렬 list 집계(`list(... ORDER BY)`)에서 네이티브 크래시(0xc0000409)를 냈다. 스레드 · 메모리를 줄여도 같았다. long 형식으로 바꾸면 수 초에 끝났다.
- Windows에서 보통 방식으로 띄운 장시간 프로세스는 Claude Code 세션 종료와 함께 죽었다. WSL로 옮기는 이유 중 하나다.
- 참고 수치(이전 구현, DuckDB, 전체 데이터): split당 feature 빌드 30–90분, 최대 메모리 약 14 GB.

## 2024 우승팀 참고치(공식 validation AUC)

단일 Transformer(v1170): 미래 · 과거 노출 정보 없음 0.7699, 과거만 0.8680, 미래 포함 0.8864, 앙상블 0.8924. 피처와 프로토콜이 달라 직접 비교 기준은 아니다.
