# 2026-10-17 Observer — 첫 묶음 "끝에서 끝까지 한 번"

## 검토 과정

- 읽은 것: `AGENTS.md`, `STATE.md`, `pyproject.toml`, `uv.lock`(torch · lightgbm · cuda 항목), `docs/data.md`, `docs/limitations.md`, `.env.example`, `src/ebnerd/{prepare/load.py,eval/metrics.py,eval/submission.py}`, `scripts/{rank_recency,evaluate,make_submission}.py`, `tests/*.py`, 지정된 history 6개.
- 커밋 범위 `8224d07..HEAD` 11개. 코드 커밋 4개(`8e25be4`, `4bb48fb`, `f607891`, `1df2986`)의 변경 파일을 각각 확인해 범위 밖 파일 수정이 없음을 봤다(STATE · history 외에는 명세의 범위 파일만).
- 실행: `uv run pytest -q` → 26 passed, 0.47s. `uv run ruff check .` → All checks passed.
- 추가 실행(스크래치, 저장소 밖): test 스키마(라벨 없음 · `is_beyond_accuracy` 있음 · `impression_id` 0 두 행 · `read_time` 등 금지 열 포함) 합성 parquet로 `rank_recency.py --split test` → `make_submission.py`를 돌렸다. zip에 `predictions.txt` 하나, 세 줄(`5 [1,2]`, `0 [1,2,3]`, `0 [1,2,3]`), BA 행도 점수가 나온다(D3 "대상 행으로서는 점수"). 같은 프레임에 `evaluate.py --split test`는 `ColumnNotFoundError: article_ids_clicked`로 멈춘다(U3 (b)대로).
- grep: `src/ scripts/ tests/ pyproject.toml`에 절대 경로 · EASEM 참조 없음. grep이 지정 밖 history 두 파일의 줄도 걸어 올렸는데 그 내용은 검토에 쓰지 않았다.
- `uv.lock`: torch 2.14.1 `source = pypi`, 의존 `cuda-toolkit 13.0.3.0` · `cuda-bindings 13.4.4` · `nvidia-cuda-runtime 13.0.96`. `pytorch.org` 문자열 0건. `pyproject.toml`에 `[tool.uv.sources]` · `[[tool.uv.index]]` 없음.

## 보고서 전문

## Observer 보고 — 끝에서 끝까지 한 번 (2026-10-17)

검토 범위: `8224d07..HEAD`(11 커밋). 코드: `src/ebnerd/prepare/load.py`, `src/ebnerd/eval/{metrics,submission}.py`, `scripts/{rank_recency,evaluate,make_submission}.py`, `tests/{test_load,test_metrics,test_metrics_qa,test_submission}.py`, `pyproject.toml`, `uv.lock`.
pytest: 26 passed (0.47s)   ruff: All checks passed

### 위반
- [§7 · Rule–설정 모순] `pyproject.toml` · `uv.lock` — §7은 "torch는 CUDA 12.8 PyTorch index를 명시해 lock한다"인데 lock의 torch 2.14.1은 PyPI 소스이고 `cuda-toolkit 13.0.3.0` · `nvidia-cuda-runtime 13.0.96`에 의존한다. `pyproject.toml`에 index · sources 지정이 없고 lock에 `pytorch.org`가 없다. vast.ai에서 "CUDA ≥ 12.8 호스트"를 빌리는 전제와 맞지 않는다(CUDA 13 wheel은 12.8 드라이버에서 못 돈다). U1 "uv.lock 커밋"이 완료로 표시돼 있으나 Rule과 설정이 다르다. 코드(설정) 쪽이 틀린 것으로 본다.

### 의심
- [§2 집행] `tests/test_submission.py` — 집행 조항은 "test 스키마의 작은 합성 프레임으로 feature 코드 전체를 돌리는 테스트"를 요구한다. 로더는 `test_load.py`가 test 스키마로 확인하지만, behaviors를 소비하는 유일한 파이프라인(`rank_recency` → `make_submission`)의 연쇄 테스트 fixture는 validation형(라벨 있음 · BA 열 없음)뿐이다. 스크래치에서 test형으로 돌려 보니 동작은 한다. 아직 "feature 코드"가 없어 조항의 적용 시점이 모호하므로 의심으로 둔다. 다음 묶음(인기도)부터는 필수.
- [K4] U5 성공 기준 "test zip 행 수 13,536,710 · 행 순서 원본과 동일 · 각 행 1..n 순열"은 Coder의 스크래치 스크립트로만 확인됐고(`coder-recency.md`), 저장소에 재실행할 테스트 · 명령이 없다. Architect의 독립 AUC 대조(`architect-u5-verify.md`)도 스크래치다. K4의 "실행해 확인할 수 있는 명령"이 저장소 안에 있어야 다음 제출 때 다시 돌릴 수 있다.
- [U4 명세 내부] 명세는 "ebnerd-benchmark와 동일"과 "동률은 입력 순서 유지(stable)"를 함께 말하는데, QA가 원본은 `argsort[::-1]`라 동률 순서가 역순이라고 지적했다(`qa-metrics.md` 2번). 제출은 순열이라 hidden 점수에는 무관하지만, 로컬에서 raw score를 평가할 때 공식 구현과 수치가 다를 수 있다. 판정이 STATE · docs 어디에도 없다.

### 결정 미반영
- "`scripts/*.py`는 패키지로 만들지 않고 테스트는 `importlib`로 경로에서 로드한다" — `architect-u5-verify.md`에서 수용했으나 STATE에 없다. 다음 스크립트 단위의 Coder가 볼 수 없다.
- "실데이터 실행은 `systemd-run --user --scope -p MemoryMax=11G` 아래에서, WSL VM 상한 15 GB" — 지금은 U5 명세 안에만 있다. 명세가 국면 종료로 은퇴하면 집을 잃는다(결정이 아니라 환경 사실 + 절차이므로 `docs/data.md` 도구 · 하드웨어 섹션이 후보).

### State 은퇴 후보
- **D6** — 체화됨 + 사실은 docs. 형식(`predictions.txt`만 든 zip, `id [r,...]`): `src/ebnerd/eval/submission.py` · `tests/test_submission.py::test_write_predictions_zip_format`. 행 순서 · BA id 0: `test_rank_recency_then_evaluate_then_zip`(impression_id `[3,0,0]` 순서 단언). phase · 하루 상한 · 채점 시간: `docs/data.md` "Codabench". 현재 D6과 docs가 같은 사실을 두 번 적고 있다(§6). **단, "점수→순위 동률은 입력 순서"는 남긴다.** `scores_to_ranks`가 제거돼 이를 잡는 코드 · 테스트가 없다(recency의 `published_time` 동률만 테스트됨).
- **D7** — 체화됨 + 국면 종료. 배치: `src/ebnerd/prepare/load.py`(`_raw_dir`, 각 함수의 경로) · `tests/test_load.py::data_root`(같은 배치의 fixture). sha256: `docs/data.md`. "복사 스크립트 없음 · test 동봉 articles 안 둠": U2 완료.
- **D4** — 국면 종료. STATE 자체가 "첫 묶음 뒤 은퇴 예정". `src/ scripts/ tests/`에 EASEM 참조 없음(grep). 사실은 `docs/data.md`.
- **D8** — 국면 종료. U5 완료(STATE 표 · 커밋 `1df2986`). 후반("인기도는 둘째 묶음, 시간 경계 QA 필요")은 다음 "현재 묶음"을 쓸 때 그쪽으로.
- **U3 · U4 · U5 명세** — 국면 종료(§5.6). 명세 안의 값 결정은 체화됨: U3 열 목록 → `BEHAVIOR_COLUMNS` · `test_load_behaviors_columns_and_order` · `test_load_articles_drops_aggregates` · `test_load_labels_test_raises`; U4 정의 → `tests/test_metrics_qa.py` 정답 구현 · 손 계산 사례; U5 결측 `published_time` 1900-01-01 → `scripts/rank_recency.py::OLDEST` · 연쇄 테스트(기사 13 None → 뒤), 라벨 중복 제거 → `scripts/evaluate.py` `list.unique()` · fixture `[15, 15]`, 100만 행 slice → `evaluate.py::SLICE_ROWS` · monkeypatch 2 테스트. 체화되지 않은 것: 위 "결정 미반영"의 `systemd-run` 절차, 그리고 U5의 validation 점수(hidden 점수와 짝지어 history로).
- D3은 후보 아님: 집계 코드가 아직 없어 체화 안 됨. D1 · D5는 끝나는 조건 미도래.

### 적합
- §2 집행: `load_behaviors`는 allow-list로 금지 열(`read_time`, `scroll_percentage`, `article_id`, `next_*`)을 모든 split에서 떨어뜨리고, `load_labels`는 분리 객체로만 라벨을 준다(`test_load.py`가 train형 · test형 둘 다 같은 함수로 확인). `load_articles`는 누적치 3열 제거. split 이름 분기 없음.
- D3: BA 행이 점수 대상에 포함된다(테스트의 id 0 두 행, 스크래치 test형 실행). 집계는 이번 묶음에 없음.
- K2 · K3: 네 코드 커밋 모두 명세 범위 파일 + STATE · history만 변경. 미사용 helper 없음(`scores_to_ranks`는 Architect가 제거). `_idcg_table`, `KEYS`, `_raw_dir`는 모두 쓰인다.
- K4: U3 → `test_load.py`(7), U4 → QA 16 + Coder 1, U5 → `test_submission.py`(2, 연쇄). validation 10분 기준은 22초로 충족(`architect-u5-verify.md`).
- 저장소 규칙: 절대 경로 없음(`.env.example`은 `<user>` 자리표시자), row-level 데이터 · ID 미커밋(`*.parquet` gitignore), `reports/` 없음.
