#!/usr/bin/env bash
# backend/entrypoint.sh
# 컨테이너 시작 시 마이그레이션 실행 후 애플리케이션 기동
set -e

echo "[entrypoint] Alembic 마이그레이션 실행 중..."
alembic upgrade head
echo "[entrypoint] 마이그레이션 완료"

echo "[entrypoint] uvicorn 서버 기동..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-2}"
