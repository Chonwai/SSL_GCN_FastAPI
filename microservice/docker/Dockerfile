# syntax=docker/dockerfile:1.6
FROM python:3.8-slim AS base

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    gcc \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    APP_ROOT=/app \
    API_PORT=8007

WORKDIR /app

# 先複製必要檔案以提高快取命中率
COPY requirements.txt /app/
COPY model/ /app/model/
COPY utils.py /app/
COPY dataset.py /app/

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY microservice/ /app/microservice/

# 建立非root使用者（提高安全性）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8007

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD \
  wget -qO- http://localhost:8007/health || exit 1

# 啟動命令
CMD ["uvicorn", "microservice.api.app:app", "--host", "0.0.0.0", "--port", "8007"] 