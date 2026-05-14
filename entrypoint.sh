#!/bin/sh
set -eu

# Kubernetes-friendly:
# prefer horizontal scaling over excessive worker count
WORKERS="${WORKERS:-2}"

exec gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind "${HOST:-0.0.0.0}:${PORT:-8000}" \
    --workers "${WORKERS}" \
    --log-level "${LOG_LEVEL:-info}" \
    --access-logfile "-" \
    --error-logfile "-" \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5
