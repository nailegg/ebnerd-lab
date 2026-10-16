# 2026-10-17 Architect — 저장소 재구축

## 배경

이 저장소는 2026-10-15에 이전 프로젝트 EASEM(`Desktop/당근`, tag `easem-v2-archive-2026-10-15`)의 후속으로 만들어졌다. 처음 이틀(10-15 ~ 16)은 "test-parity 감사" 노선이었다. EASEM v2의 validation AUC 0.857 대비 test 0.639 격차의 원인(그 주 클릭에서 만든 feature가 test에서 0, BA 행 미제외, split별 다른 코드 경로)을 기계적 검사로 막은 뒤 모델을 학습한다는 계획이었고, 감사 단계 S0–S4까지 통과하고 S5 도중 중단됐다. 그 문서(`docs/plan.md`)와 코드는 `C:\ebnerd-data\archive\repo-2026-10-17\`에 사본을 두고 저장소에서 지웠다.

10-17 세션에서 사용자가 노선을 바로잡았다. 이 저장소는 감사 저장소가 아니라 **hidden test 점수를, 미래 정보 없이, 최대로 올리는 연구 저장소**다. 이전 실험의 결정과 코드는 승계하지 않는다.

## 토론과 결정 근거

### 점수판과 입력 경계 (D1, D2)

Architect가 제기한 긴장: "실 서비스 유사 제약"과 "hidden test"는 어긋난다. 실 서비스는 t 이전 모든 사용자의 클릭을 알지만 hidden test는 그 주 클릭을 주지 않는다. 사용자 답: 일단 hidden test 점수를 골자로 하고, 만족할 점수 뒤에 자체 validation protocol 연구를 후속으로 한다. 지연은 흉내 내지 않는다. 기사 최종 snapshot은 t 이후 수정분까지 그대로 쓴다(엄밀히 가면 연구가 불가능에 가까워져 한계로 남긴다).

귀결로서 "입력 = test 파일에 있고 t보다 엄격히 이전"을 Architect가 제시했고 사용자가 수용했다. 다른 사용자의 t 이전 노출은 쓰고, t 이전 클릭은 test에 없어 못 쓴다.

### BA 행 제외 (D3)

이전 저장소의 결정을 승계하지 않는다는 원칙과 별개로, Architect가 데이터 사실(합성 행 20만 개, 같은 시각, 같은 250개 후보가 일반 후보 칸의 14.85%)에서 다시 내린 결정이다. 넣으면 test 시작 직후 노출 수가 20만씩 부풀어 train · validation과 분포가 달라진다.

### 맥락 승계 범위 (D4)

이전 저장소의 (a) 결정, (b) 사실, (c) 코드 · 산출물을 구분해 물었다. 사용자: 사실은 출처 표시 없이 참고해도 된다. 결정과 코드는 버린다. 산출물(로컬 13 GB feature)은 feature 정의를 새로 내릴 것이고 서버로 옮길 수단도 없어 재활용하지 않기로 Architect가 판단했다.

### 데이터 흐름과 환경 (D5, D6)

사용자: 저장소는 메인 파이프라인 학습 전 git으로 외부 GPU 서버(vast.ai)로 이전된다. 환경 재빌딩 가능성은 무조건 열려 있어야 한다. WSL이 더 적합하면 말해 달라.

Architect 권고: WSL2. 서버가 Linux이므로 wheel · 경로 · 프로세스 동작이 같아지고, 이전 저장소가 겪은 Windows 고유 문제(세션 종료 시 프로세스 사망을 WMI로 우회, Windows wheel 유무로 LightGBM 버전 결정, DuckDB 네이티브 크래시)가 사라진다. 데이터는 `/mnt/c`가 아니라 WSL ext4에 둔다. 사용자 수용.

vast.ai는 인스턴스를 끄면 디스크가 사라지므로 "로컬 CPU에서 feature 빌드 → 전송 → vast.ai GPU 학습" 흐름이 된다. 전송 수단으로 외부 버킷(Cloudflare R2 + rclone, egress 무료, 월 $1 미만)과 직접 scp를 비교했다. 버킷은 인스턴스를 여러 번 띄울 때와 결과물 보관에 유리하고, 직접 전송은 한 번만 띄울 때 간단하다. 결정은 첫 학습 직전으로 미루고 그때까지 push/pull 코드는 만들지 않는다(당장 안 쓰는 기능 금지).

스택은 이전 결정(DuckDB, scikit-learn · polars 금지)을 승계하지 않고 Architect가 새로 골랐다: polars · pyarrow(EB-NeRD 공식 도구가 polars 기반이고 DuckDB 크래시 이력이 있음), torch, lightgbm, pytest · ruff.

### 에이전트 구조 (D7, D8)

사용자 요구: Architect(총괄, 사용자와 직접 소통) · Coder(작은 단위 구현, 별도 매뉴얼) · Observer(묶음 끝 검토 후 Architect에 보고). 지양 사항 세 가지: 복잡한 세부 계약으로 agent를 과도하게 제약하는 것, 당장 안 쓰는 helper와 과도한 추상화, 규칙 · 버전관리의 묻힘(결정 미반영, 과거 코드 그대로 사용).

Coder의 비효율과 Observer의 과잉 단속 둘 다 피하기 위해 Karpathy guideline(Andrej Karpathy의 2026-01-26 LLM 코딩 관찰을 Forrest Chang이 CLAUDE.md 네 원칙으로 정리한 것: Think before coding, Simplicity first, Surgical changes, Goal-driven execution)을 **양쪽이 공유하는 하나의 체크리스트**로 `AGENTS.md` §3에 두었다. Observer는 그 목록의 위반만 지적한다.

Observer 권한: Architect 제안대로 "보고만 하되, 보고서는 가공 없이 사용자에게 전달되고, Architect는 지적마다 수용 · 기각과 이유를 STATE.md에 적는다". Architect 감시 문제(지양 3번은 Architect의 실패 양식인데 Observer는 Coder만 본다)도 Architect 제안대로 Observer 임무에 "이번 묶음의 결정이 STATE.md에 적혔는가, 코드가 Rule · State와 모순되지 않는가"를 추가해 해결했다.

QA 페르소나: 사용자가 추가를 제안했고 "테스트 내용은 사용자와 Architect가, 작성 · 검증은 아래로". Architect는 Coder가 구현과 테스트를 함께 쓰면 테스트가 구현의 가정을 베끼는 문제를 들어, QA의 가치가 가장 큰 곳은 느린 정답 구현과의 대조라고 설명했다. 모든 단위가 아니라 Architect가 지정한 단위(시간 경계 feature, 평가 지표)에만 QA를 붙이기로 했다(지양 1번과 부합).

사용자 질문 "정답 구현 대조와 데이터 검사가 ML 연구 코드에서 일반적인가"에 대한 Architect 답: 학계 연구 코드에서는 일반적이지 않지만 대회 · 산업 ML 엔지니어링에서는 표준 관행(Breck et al. 2017 ML Test Score, Kaggle 관행). 추천 대회에서 시간 누수는 가장 흔한 조용한 실패이며 이전 저장소에서도 그 대조로 버그 1건을 잡았다. 다만 최소한으로: 시간 경계 feature에만, 작은 표본, 한 번.

### Rule · State · History

사용자 요구: Rule(AGENTS.md · CLAUDE.md, 가능하면 통합; 페르소나별 Rule 별도 가능)과 History(상세 기록, 지시 없이 열지 않음)의 분리. Architect가 제기한 긴장: History를 열지 않으면 결정이 살아남으려면 Rule에 들어가야 하고, 그러면 Rule이 비대해진다. 세 번째 층 **State**(유효한 결정 · 현재 위치, 1페이지, 매 세션 읽음)를 제안했고 사용자가 수용하며 "Architect가 State 유효성도 판단하고 갱신"하도록 했다.

State 1페이지 상한을 넘기면 무엇을 버리느냐는 질문에, Architect 안("유효한 결정은 한 줄로 압축하되 State 밖으로 내보내지 않고, 길이 압박은 서술을 줄여 푼다")을 사용자가 수용했다. `AGENTS.md` §6에 넣었다.

CLAUDE.md는 `@AGENTS.md` 한 줄로 통합했다. 페르소나별 Rule은 `.claude/agents/*.md`가 subagent 정의와 같은 파일이라 중복이 없다.

### 작은 결정 (D9, D10)

git은 `main` 하나, 커밋은 Architect가 단위마다, 첫 커밋은 코드 없이 Rule · State · 뼈대. 문서는 한국어, 코드 · 커밋은 영어. 이의 없이 수용됐다.

## 이 세션에서 한 일

1. `docs/ configs/ reports/ README.md`를 `C:\ebnerd-data\archive\repo-2026-10-17\`에 복사하고 `src/ tests/ configs/ reports/ docs/ uv.lock .venv`를 삭제.
2. `AGENTS.md`, `CLAUDE.md`, `STATE.md` 작성.
3. `.claude/agents/{coder,observer,qa}.md` 작성.
4. `docs/data.md`(사실), `docs/limitations.md` 작성.
5. `pyproject.toml`(새 스택, 버전 미고정 — WSL에서 `uv lock`), `.env.example`, `.gitignore`, `README.md`, 빈 `src/ebnerd/{prepare,train,eval}/`.
6. 이 기록.
7. 첫 커밋.

## 다음 세션(WSL)에서 정할 것

첫 구현 묶음. 후보: WSL 환경 확인과 `uv lock`, 원본 데이터를 WSL 디스크로 복사, 원본 parquet 로딩, 공식 지표 구현(QA 단위). hidden test 점수 확인 경로(Codabench)도 확인한다.
