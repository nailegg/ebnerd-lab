# ebnerd-lab

EB-NeRD(RecSys Challenge 2024) 뉴스 추천. 공식 hidden test 점수를, 추천 시점에 알 수 없는 정보를 쓰지 않고 최대화한다.

- 규칙: [`AGENTS.md`](AGENTS.md) — 목표, 입력 경계, 코드 기준, 역할, 흐름
- 현재 상태와 유효한 결정: [`STATE.md`](STATE.md)
- 데이터 사실: [`docs/data.md`](docs/data.md) · 받아들인 한계: [`docs/limitations.md`](docs/limitations.md)
- 작업 기록: `history/` (지시 없이 열지 않음)

## 환경

WSL2 Ubuntu, Python 3.11, [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env     # EBNERD_DATA_ROOT 설정
uv run pytest
uv run ruff check .
```

데이터와 산출물은 `$EBNERD_DATA_ROOT` 아래에만 둔다. 저장소에는 코드, 규칙, 집계 결과만 둔다.
