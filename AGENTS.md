# ebnerd-lab 규칙

이 파일이 저장소의 유일한 전역 규칙이다. 모든 agent는 세션 시작 시 이 파일과 `STATE.md`만 읽는다. `history/`는 명시적 지시가 있을 때만 연다. 이 파일은 사용자 승인 없이 바꾸지 않는다.

## 1. 목표

EB-NeRD(RecSys Challenge 2024) 뉴스 추천에서 **공식 hidden test 점수**를 최대화한다. 제약은 하나다. 실제 서비스가 추천 시점에 알 수 없는 정보(미래)는 쓰지 않는다. 만족할 점수에 이른 뒤, 자체 validation protocol 안에서 성능을 보는 연구를 후속으로 한다.

## 2. 입력 경계

대상 impression의 시각을 t라 한다.

- 입력은 **test 파일에 존재하고 t보다 엄격히 이전인 정보**만 쓴다. 같은 시각의 다른 impression은 "이전"이 아니다.
- 쓸 수 있는 것: 대상 impression 자체의 속성(시각, 기기, 후보 목록과 수), 모든 사용자의 t 이전 impression(inview 목록 · 시각 · 기기), 사용자의 history 파일(노출 기간 이전 21일 클릭), 기사 메타와 공식 기사 벡터.
- 쓸 수 없는 것: 그 주의 클릭(test에 없다. 라벨로만 쓴다), 방문이 끝나야 확정되는 값(`read_time`, `scroll_percentage`, `next_*`, 현재 페이지 `article_id`), 기사 파일의 누적치(`total_inviews`, `total_pageviews`, `total_read_time`), t 이후 이벤트, 다른 split의 behaviors.
- 예외: 기사 메타는 최종 snapshot을 그대로 쓴다(수정 시각이 t 이후여도). 받아들인 한계다(`docs/limitations.md`).
- 집계 지연은 흉내 내지 않는다. t 이전이면 즉시 사용 가능으로 본다.
- 세 split(train · validation · test)은 **같은 코드 경로**로 만든다. split 이름으로 로직을 분기하지 않는다.

## 3. 코드 기준 — Coder와 Observer가 공유하는 체크리스트

Karpathy의 네 원칙을 이 저장소의 체크리스트로 쓴다. Coder는 이것을 지키고, Observer는 **이 목록의 위반만** 지적한다. 목록에 없는 것은 취향이며 지적 대상이 아니다.

**K1. 생각 먼저.** 가정을 적는다. 명세가 모호하면 추측하지 않고 멈춰서 묻는다. 더 단순한 길이 보이면 말한다.

**K2. 단순함.** 과업을 푸는 최소 코드. 금지: 지금 쓰지 않는 helper, 한 곳에서만 쓰는 추상화(클래스 · 레이어 · 레지스트리), 요청받지 않은 설정 옵션, 일어날 수 없는 경우의 에러 처리, 호환 레이어. 판단 기준: "시니어 엔지니어가 과하다고 할 것인가."

**K3. 외과적 변경.** 과업 범위의 파일만 고친다. 인접 코드 · 주석 · 포맷을 "개선"하지 않는다. 자기 변경 때문에 죽은 import · 함수만 지운다. 무관한 죽은 코드는 지우지 않고 보고한다.

**K4. 목표 주도.** 모든 단위에 검증 수단이 있다(테스트, 또는 실행해 확인할 수 있는 명령). 성공 기준은 단위 명세에 미리 적힌다. 버그는 재현 테스트를 먼저 쓴다.

저장소 규칙(체크리스트의 일부):

- row-level 데이터, user · impression ID, 자격 증명은 git에 넣지 않는다. 데이터는 `$EBNERD_DATA_ROOT` 아래에만 둔다. `reports/`에는 집계만 둔다.
- 코드에 절대 경로를 적지 않는다. 경로는 환경 변수와 설정 파일에서 온다.
- 시간 경계가 있는 계산은 느린 정답 구현과 작은 표본에서 한 번 대조한다(QA 단위).

## 4. 역할

| 역할 | 누구 | 한다 | 하지 않는다 |
|---|---|---|---|
| **Architect** | 메인 세션 | 사용자와 범위 · 구조 · 단위를 정한다. 단위 명세를 쓴다. 결정을 즉시 `STATE.md`에 반영한다. 커밋한다. Observer 지적에 수용 · 기각과 이유를 적는다 | 큰 코드를 직접 쓰지 않는다 |
| **Coder** | `.claude/agents/coder.md` | 단위 하나를 구현하고 그 단위의 테스트를 쓴다(QA가 붙은 단위는 QA 테스트를 통과시킨다) | 범위 밖 파일 수정, 규칙 · State 수정 |
| **QA** | `.claude/agents/qa.md` | Architect가 지정한 단위에만. 명세만 보고 정답 구현과 테스트를 쓴다 | Coder의 구현을 읽지 않는다 |
| **Observer** | `.claude/agents/observer.md` | 구현 묶음이 끝날 때 한 번. §3 위반, 코드와 Rule · State의 모순, 이번 묶음의 결정이 State에 적혔는지를 본다. 보고만 한다 | 코드 수정, 취향 지적 |

Observer 보고서는 가공 없이 사용자에게 전달된다.

## 5. 흐름

1. Architect와 사용자가 **구현 묶음**(단위들의 집합)을 정하고 `STATE.md`에 적는다.
2. Architect가 단위마다 명세를 쓴다. 명세 = 목표 한 문장, 범위(파일), 성공 기준, 금지 사항, QA 여부.
3. QA가 붙은 단위는 QA가 명세에서 테스트를 쓰고, Coder가 통과시킨다. 아니면 Coder가 구현과 테스트를 함께 쓴다.
4. 단위가 끝나면 Architect가 검증 명령을 실행하고 커밋한다.
5. 묶음이 끝나면 Observer가 한 번 검토한다. Architect는 지적마다 수용 · 기각과 이유를 `STATE.md`에 적고, 수용한 것은 단위로 만들어 처리한다.
6. 각 agent는 작업이 끝날 때 `history/`에 자기 기록을 남긴다.

## 6. Rule · State · History

- **Rule** = 이 파일과 `.claude/agents/*.md`. 바뀌지 않는 원칙만. 사용자 승인으로만 바꾼다.
- **State** = `STATE.md`. 지금 유효한 결정, 현재 위치, 열린 질문, 한계. Architect만 수정한다. **1페이지 상한.** 유효한 결정은 한 줄로 압축하되 State 밖으로 내보내지 않는다. 길이 압박은 결정 수가 아니라 서술을 줄여 푼다. 매 세션 시작에 Architect가 유효성을 확인한다.
- **History** = `history/YYYY-MM-DD-<역할>-<주제>.md`. 추가만 한다. 토론, 결정 근거, 작업 내용을 소상히 적는다. **지시 없이 열지 않는다.**
- 결정은 내린 즉시 State에 적는다. 코드와 State가 다르면 코드가 틀린 것이다.

## 7. 환경

- 개발: WSL2 Ubuntu, Python 3.11, `uv`. 학습: vast.ai GPU 인스턴스(저장소는 git으로 이동한다. 환경은 `pyproject.toml` · `uv.lock`만으로 재현돼야 한다).
- 스택: polars · pyarrow(데이터), torch(모델), lightgbm(기준선), pytest · ruff(검증). 새 의존성은 Architect가 결정한다.
- 명령: `uv sync`, `uv run pytest`, `uv run ruff check .`
- 데이터: `$EBNERD_DATA_ROOT`(WSL ext4 디스크, git 밖). `raw/`, `features/<version>/`, `runs/<run_id>/`.
- 언어: 문서(Rule · State · History · docs)는 한국어, 코드 · 식별자 · 주석 · 커밋 메시지는 영어.
