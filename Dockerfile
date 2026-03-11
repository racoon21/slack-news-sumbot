FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# 의존성 파일 복사 및 설치 (캐시 레이어 활용)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 소스 코드 복사
COPY . .
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "python", "main.py"]
