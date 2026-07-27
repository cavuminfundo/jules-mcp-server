FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml .
COPY jules_mcp ./jules_mcp

RUN uv sync --frozen || uv sync

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "-m", "jules_mcp.jules_mcp"]
