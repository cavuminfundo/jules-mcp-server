FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastmcp httpx pydantic

COPY jules_mcp ./jules_mcp

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.source=https://github.com/cavuminfundo/jules-mcp-server

CMD ["python", "-m", "jules_mcp.jules_mcp"]
