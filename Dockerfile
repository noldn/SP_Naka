FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    SP_NAKA_WEB_HOST=0.0.0.0 \
    SP_NAKA_WEB_PORT=8765

WORKDIR /app
COPY . /app

RUN useradd --create-home --uid 10001 spnaka \
    && mkdir -p /app/data/local /app/output \
    && chown -R spnaka:spnaka /app

USER spnaka
EXPOSE 8765
CMD ["python3", "-m", "sp_naka.webapp"]
