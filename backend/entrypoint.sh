#!/usr/bin/env bash
# backend/entrypoint.sh
# 컨테이너 시작 시 마이그레이션 실행 후 애플리케이션 기동
set -e

# DB 컨테이너가 준비되기 전에 기동될 수 있으므로 마이그레이션을 재시도한다.
# 접속 실패로 컨테이너가 죽고 재기동되는 것을 막는 방어 로직이다.
MIGRATION_MAX_RETRIES="${MIGRATION_MAX_RETRIES:-30}"
MIGRATION_RETRY_DELAY="${MIGRATION_RETRY_DELAY:-2}"

echo "[entrypoint] Alembic 마이그레이션 실행 중..."
attempt=1
until alembic upgrade head; do
    if [ "$attempt" -ge "$MIGRATION_MAX_RETRIES" ]; then
        echo "[entrypoint] 마이그레이션이 ${MIGRATION_MAX_RETRIES}회 실패했습니다. 기동을 중단합니다."
        exit 1
    fi
    echo "[entrypoint] 마이그레이션 실패 (${attempt}/${MIGRATION_MAX_RETRIES}). ${MIGRATION_RETRY_DELAY}초 후 재시도..."
    attempt=$((attempt + 1))
    sleep "$MIGRATION_RETRY_DELAY"
done
echo "[entrypoint] 마이그레이션 완료"

echo "[entrypoint] uvicorn 서버 기동..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-2}"
