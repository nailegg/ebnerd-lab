# 2026-10-17 Architect — State 은퇴 기록

구조 평가(`2026-10-17-architect-structure-review.md`) 2-3 "State가 Rule을 복창한다"를 수용해, Rule에 이미 있는 결정을 State에서 뺐다. 전부 **체화됨**이고, 체화 위치는 `AGENTS.md`다. 은퇴 당시 원문을 그대로 남긴다.

| 결정 | 원문 | 체화 위치 |
|---|---|---|
| D2 | 입력 경계: test 파일에 있고 t보다 엄격히 이전인 정보만. 지연은 흉내 내지 않는다. 기사 메타는 최종 snapshot을 쓴다(한계). 상세는 `AGENTS.md` §2. | `AGENTS.md` §2 |
| D6 | 환경: WSL2 Ubuntu, Python 3.11, uv, polars · pyarrow · torch · lightgbm, pytest · ruff. | `AGENTS.md` §7(WSL · Python · uv), `pyproject.toml`(라이브러리) |
| D7 | QA는 Architect가 지정한 단위에만 붙는다(시간 경계가 있는 feature, 평가 지표). 나머지는 Coder가 테스트까지 쓴다. | `AGENTS.md` §4 · §5 |
| D8 | Observer는 묶음 끝에 한 번, 보고만. 보고서는 원문 그대로 사용자에게 전달. Architect는 지적마다 수용 · 기각과 이유를 표에 적는다. State 은퇴도 Observer 제안 → Architect 결정. | `AGENTS.md` §4 · §5 · §6 |
| D9 | git: `main` 하나. 커밋은 Architect가 단위마다. 커밋 메시지 영어. | `AGENTS.md` §4(커밋은 Architect) · §7(언어). "`main` 하나"는 Rule에 없으나 코드 · 설정에서 읽히지 않고 끝나는 조건도 없으므로 Rule 성격이다. 지금은 브랜치가 하나뿐이라 적을 필요가 없고, 브랜치 전략이 필요해지면 그때 Rule에 넣는다. |
| D10 | 문서는 한국어, 코드 · 커밋은 영어. | `AGENTS.md` §7 |

같은 평가의 2-7을 수용해 "한계" 절도 `docs/limitations.md` 포인터로 줄였다(원문: "기사 메타의 최종 snapshot 사용(`docs/limitations.md`)").

열린 질문 "vast.ai 이미지(Python 3.11 · CUDA 12.x 계열 PyTorch 공식 이미지 예정)"는 평가 2-8의 결론(이미지가 아니라 호스트 드라이버의 CUDA 버전이 관건, 12.8을 index로 명시해 lock)으로 **대체됨** → `AGENTS.md` §7.
