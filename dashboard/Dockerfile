FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NLTK_DATA=/app/.cache/nltk
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-topics.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu 'torch>=2.6,<3' \
    && pip install --no-cache-dir -r requirements-topics.txt 'gunicorn>=23,<24'
COPY scripts/setup_nltk.py scripts/setup_nltk.py
RUN python scripts/setup_nltk.py
COPY server ./server
COPY config ./config
COPY reports ./reports
COPY models ./models
COPY run.py ./run.py
RUN useradd --create-home app && chown -R app:app /app
USER app
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "180", "run:app"]
