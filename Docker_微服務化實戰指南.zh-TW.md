## 目標與適用範圍

本文件總結本專案（xDeep-AcPEP-Classification）從一般 Python 專案到「可部署的 Docker 微服務」的實戰經驗，並提供一套可重複套用的標準化步驟與範本，方便你將另一個尚未容器化的 Python 專案，也快速轉為可上線的微服務。

適用情境：
- **Python 應用**（特別是 FastAPI/Flask 等 API 服務）
- 需要打包模型、腳本、原生函式庫（如 BLAS/LAPACK）
- 需要在本地與雲端用 Docker 執行，並可透過 `docker-compose` 進行開發與測試


## 成功案例重點（本專案做了什麼）

- **清晰的服務邊界與介面**：以 FastAPI 暴露 `/health`、`/model/info`、`/predict/*` 等端點（見 `microservice/api/app.py`）。
- **容器化基礎**：
  - 使用 `python:3.8-slim` 作為基底映像，安裝必要原生套件（`openblas`, `lapack`, `gcc` 等）。
  - 以 `uvicorn` 啟動 API，將服務固定在 `0.0.0.0:<PORT>` 對外暴露。
  - 將模型與腳本（`sav/`、`feat_1.sh`、`functionList.py`、`iFeature-master/` 等）打包進容器。
- **相依版本固定**：針對舊版模型環境，將 `numpy/pandas/scipy/sklearn` 等版本明確 pin 住，降低行為差異。
- **建置與執行**：提供 `docker-compose.yml` 用於本地快速起服與對外 mapping 連接埠，並在 Apple Silicon 上強制 `linux/amd64` 平台，避免特徵計算與舊版二進位相容性問題。
- **映像與建置最佳化**：
  - 使用 `.dockerignore` 排除不必要檔案，縮小建置 context。
  - 先複製必要檔案再安裝套件，以提高 Docker layer 快取命中率。


## 標準化微服務化步驟（一步一步）

### 第 0 步：倉庫整理與可重現性
- **列出執行服務所需的最小檔案集合**：主程式、API 入口、模型檔、外部腳本、必要資料與設定。
- **固定 Python 與套件版本**：若有舊模型或 C 擴充套件相依，請明確 pin 住（例如 `numpy==1.20.1`、`scipy==1.4.1`）。
- **建立 `.dockerignore`**：排除 dataset、暫存檔、大型中間輸出、`.git` 等，以縮小建置 context。

### 第 1 步：服務化 API 入口
- 建立或整理一個清晰的 API 入口（本專案為 `microservice/api/app.py`），確保：
  - 有 `/health` 健康檢查端點。
  - 有主要功能端點（如 `/predict/single`、`/predict/batch`）。
  - 啟動語法簡單（例如：`uvicorn microservice.api.app:app --host 0.0.0.0 --port 8003`）。

### 第 2 步：Dockerfile（可直接套用之最佳實務模板）

以下模板在本專案上已驗證可行，並加入一些通用最佳實務（非 root、健康檢查、清理套件快取等）：

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.8-slim AS base

# 安裝原生依賴（依你的專案調整）
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash build-essential gcc gfortran libopenblas-dev liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    APP_ROOT=/app \
    API_PORT=8003

WORKDIR /app

# 先複製必要檔案提高快取命中
COPY sav/ /app/sav/
COPY feat_1.sh /app/feat_1.sh
COPY functionList.py /app/functionList.py
COPY iFeature-master /app/iFeature-master
COPY microservice /app/microservice

# 釘選版本以配合既有模型環境（依你的專案調整）
RUN pip install --no-cache-dir \
    fastapi==0.109.2 \
    uvicorn[standard]==0.27.1 \
    numpy==1.20.1 \
    pandas==0.25.3 \
    scipy==1.4.1 \
    scikit-learn==0.22.1

# 確保腳本可執行
RUN chmod +x /app/feat_1.sh

# 推薦：建立一個非 root 使用者（提高安全性）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8003

# 也可加入 Docker 原生 HEALTHCHECK（可與 /health 對應）
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD \
  wget -qO- http://localhost:8003/health || exit 1

CMD ["uvicorn", "microservice.api.app:app", "--host", "0.0.0.0", "--port", "8003"]
```

關鍵點：
- 選擇 `*-slim` 基底映像，體積較小。
- 只安裝必要系統套件與 Python 相依。
- 利用複製順序提升快取效果：當相依不變，變更應用程式碼時可避免重灌套件。
- 非 root 執行提升安全性（可視需求加上唯讀檔系統、限制權限）。
- 可加入 `HEALTHCHECK` 與 `/health` 端點呼應，便於容器編排器監控。

### 第 3 步：docker-compose（本地開發與驗證）

```yaml
services:
  api:
    # Apple Silicon/Mac 上若有二進位相容問題，可固定成 x86_64
    platform: linux/amd64
    build:
      context: ../..
      dockerfile: microservice/docker/Dockerfile
    image: your-python-api:latest
    ports:
      - "8003:8003"
    environment:
      - PYTHONUNBUFFERED=1
      - API_PORT=8003
    # 可選：加上健康檢查，讓 compose 知道何時 ready
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8003/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    restart: unless-stopped
```

要點：
- `platform: linux/amd64` 可在 M 系 Mac 上避免相依二進位不相容。
- 在本地開發可直接 `docker compose up --build` 驗證。
- 若有模型或大量輸入輸出，可考慮改以 volume 掛載，避免映像膨脹。

### 第 4 步：.dockerignore（縮小建置 context）

```gitignore
.git
__pycache__
*.pyc
*.pyo
*.pyd
.DS_Store
*.log
*.csv
*tmpFolder/
backup/
*.zip
input_out.txt
testing_out.txt
sample_tmpFolder/
sample.csv
```

原則：排除 data、暫存、編譯輸出、大型中間檔案。

### 第 5 步：啟動與驗證

本地快速驗證：

```bash
# 進入 docker 目錄（依你的專案路徑）
docker compose -f microservice/docker/docker-compose.yml up --build

# 另開一個終端視窗做 smoke test
curl http://localhost:8003/health
curl -X POST http://localhost:8003/predict/single \
  -H 'Content-Type: application/json' \
  -d '{"name":"sequence_1","sequence":"ALWKTMLKKLGTMALHAGKAALGAAADTISQGTQ"}'
```


## 進階最佳實務

- **多階段建置**：若需要編譯 C 擴充、建 wheel，可用 builder 階段產出最終 wheel，runtime 階段只安裝 wheel。
- **快取與體積**：
  - 先複製 `requirements*` → 安裝 → 再複製程式碼，可提升快取命中。
  - 加上 `--no-cache-dir` 與清理 apt cache。
- **安全性**：
  - 非 root、唯讀檔系統（`--read-only`）、限制 capabilities。
  - 不要把秘密寫進映像，使用環境變數或外部 secret 管理。
- **健康檢查**：
  - 容器內 `HEALTHCHECK` 與 `/health` 端點互相對應。
  - 在 `docker-compose` 或雲端編排層也可加上 healthcheck 與 restart policy。
- **平台相容**：在 Apple Silicon 上若涉及舊版科學計算相依，建議 `linux/amd64`，或預先提供多平台映像（`docker buildx`）。


## 常見問題與除錯

- 映像建置很慢或很大？
  - 檢查 `.dockerignore` 是否正確；
  - 分離 data 與模型輸出，改用 volume；
  - 使用 `*-slim`、移除不必要套件。

- 科學套件版本衝突？
  - 鎖定版本，並確保 OS 原生依賴（BLAS/LAPACK、gcc/gfortran）已安裝；
  - 優先沿用「模型當時訓練所使用」的版本，避免推論行為差異。

- M 系 Mac 問題？
  - 在 compose 中加入 `platform: linux/amd64`；
  - 或使用 `docker buildx build --platform linux/amd64`。

- 快速進入容器內檢查：
  ```bash
  docker exec -it <container_id_or_name> /bin/bash
  ```


## 可直接複用的最小範本清單（Checklist）

- **API 入口**：`uvicorn package.module:app --host 0.0.0.0 --port <PORT>`
- **健康檢查端點**：`GET /health` 回傳 `{"status":"healthy"}` 類似結構。
- **Dockerfile**：基底 `python:3.8-slim`（或你的版本）、安裝原生依賴、固定 Python 相依版本、非 root、`CMD` 用 `uvicorn`。
- **docker-compose.yml**：設定 `platform`（若需要）、`ports`、`environment`、`healthcheck`、`restart`。
- **.dockerignore**：排除 `.git`、暫存、dataset、大型中間檔。


## 將另一個 Python 專案遷移為微服務（建議流程）

1) 整理專案：釐清 API 介面、輸入輸出、模型與腳本；建立 `/health` 與最小可用端點。
2) 釘選依賴：確認 Python 與套件版本，必要時回溯到與模型相容的版本。
3) 撰寫 Dockerfile：按本文件模板與你的相依調整；先以本地 `docker build` 驗證。
4) 撰寫 docker-compose：本地 `up --build` 驗證健康檢查與端點。
5) 縮小映像與提升安全性：加入 `.dockerignore`、非 root、必要時多階段建置。
6) 自動化：在 CI 建置映像、跑 smoke test，推送到映像倉庫；在 CD 進行部署。


## 參考（本專案）

- Dockerfile：`microservice/docker/Dockerfile`
- Compose：`microservice/docker/docker-compose.yml`
- Ignore：`microservice/docker/.dockerignore`
- API：`microservice/api/app.py`
- 服務邏輯：`microservice/core/prediction_service.py`

