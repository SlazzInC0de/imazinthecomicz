# API image for a Hugging Face Docker Space (or any container host).
# Build from the repo root:  docker build -f api/Dockerfile -t imazin-api .
FROM python:3.12-slim

RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV FASTEMBED_CACHE_PATH=/app/.cache/fastembed \
    DATA_DIR=/app/data \
    PYTHONUNBUFFERED=1

# Bake the model into the image so cold starts do not download it.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5', cache_dir='/app/.cache/fastembed')"

COPY data/catalog.parquet data/embeddings.npy data/meta.json /app/data/
COPY api/app /app/app
RUN chown -R app:app /app
USER app

EXPOSE 7860
HEALTHCHECK --interval=60s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
