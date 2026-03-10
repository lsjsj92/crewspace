# backend/Dockerfile
# Planship 백엔드 컨테이너 이미지
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# entrypoint.sh: 마이그레이션 실행 후 uvicorn 기동
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
