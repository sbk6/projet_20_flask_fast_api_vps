# ── Stage 1 : installation des dépendances ──────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2 : image finale minimale ──────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copier les dépendances depuis le builder (image finale plus légère)
COPY --from=builder /install /usr/local

# Copier le code source
COPY . .

# Variables d'environnement Python (pas de .pyc, logs en temps réel)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Production : Gunicorn avec workers Uvicorn (async)
# 4 workers = 2 * nb_CPU + 1 (règle recommandée)
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
