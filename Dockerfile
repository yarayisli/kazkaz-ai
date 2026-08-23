FROM node:22-alpine AS web-build
WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 kazkaz
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt
COPY api/ ./api/
COPY cfo_agent.py gemini_engine.py ./
COPY --from=web-build /app/web/dist ./web/dist
USER kazkaz
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/health', timeout=3).read()" || exit 1
CMD ["sh", "-c", "uvicorn api.main:uygulama --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*' --timeout-graceful-shutdown 30"]
