# SSL-GCN 毒性預測微服務

基於半監督學習和圖卷積神經網絡的化學毒性預測微服務，支援12種毒性端點預測。

## 🚀 快速開始

### 使用 Docker Compose（推薦）

```bash
# 啟動服務
cd microservice/docker
./start.sh

# 或手動執行
docker-compose up --build
```

### 手動啟動

```bash
# 建置映像
docker build -f microservice/docker/Dockerfile -t ssl-gcn-api .

# 運行容器
docker run -p 8007:8007 ssl-gcn-api
```

## 📊 API 端點

### 健康檢查
```bash
GET /health
```

### 模型資訊
```bash
GET /model/info
```

### 支援的任務列表
```bash
GET /predict/tasks
```

### 單一分子預測
```bash
POST /predict/single
Content-Type: application/json

{
  "molecule_id": "TEST001",
  "smiles": "CCO",
  "task_type": "NR-AR"
}
```

### 批次分子預測
```bash
POST /predict/batch
Content-Type: application/json

{
  "molecules": [
    {"molecule_id": "TEST001", "smiles": "CCO"},
    {"molecule_id": "TEST002", "smiles": "CCCO"}
  ],
  "task_type": "NR-AR"
}
```

## 🧪 測試

```bash
# 執行 API 測試
cd microservice/docker
./test_api.sh
```

## 📋 支援的毒性端點

- **核受體 (Nuclear Receptors)**
  - NR-AR
  - NR-AR-LBD
  - NR-AhR
  - NR-Aromatase
  - NR-ER
  - NR-ER-LBD
  - NR-PPAR-gamma

- **應激反應 (Stress Response)**
  - SR-ARE
  - SR-ATAD5
  - SR-HSE
  - SR-MMP
  - SR-p53

## 🔧 配置

### 環境變數
- `API_PORT`: API 服務端口（預設：8007）
- `PYTHONUNBUFFERED`: Python 輸出緩衝（預設：1）

### Docker 配置
- 基底映像：`python:3.8-slim`
- 端口：8007
- 健康檢查：每30秒檢查一次

## 📁 目錄結構

```
microservice/
├── api/
│   └── app.py              # FastAPI 應用程式入口
├── core/
│   └── prediction_service.py # 核心預測服務
├── docker/
│   ├── Dockerfile          # Docker 映像配置
│   ├── docker-compose.yml  # Docker Compose 配置
│   ├── .dockerignore       # Docker 忽略檔案
│   ├── start.sh           # 啟動腳本
│   └── test_api.sh        # API 測試腳本
└── README.md              # 本檔案
```

## 🛠️ 開發

### 本地開發
```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動開發服務器
uvicorn microservice.api.app:app --host 0.0.0.0 --port 8007 --reload
```

### 建置新映像
```bash
cd microservice/docker
docker-compose build --no-cache
```

## 📈 監控

### 健康檢查
```bash
curl http://localhost:8007/health
```

### 查看日誌
```bash
docker-compose logs -f
```

## 🔒 安全性

- 使用非 root 使用者運行容器
- 健康檢查機制
- 輸入驗證和錯誤處理
- 臨時檔案自動清理

## 🚨 故障排除

### 常見問題

1. **端口被佔用**
   ```bash
   # 檢查端口使用情況
   lsof -i :8007
   ```

2. **模型載入失敗**
   ```bash
   # 檢查模型檔案是否存在
   ls -la model/
   ```

3. **記憶體不足**
   ```bash
   # 增加 Docker 記憶體限制
   docker run -m 4g -p 8007:8007 ssl-gcn-api
   ```

### 日誌查看
```bash
# 查看容器日誌
docker-compose logs ssl-gcn-api

# 進入容器調試
docker exec -it ssl-gcn-toxicity-prediction /bin/bash
```

## 📄 授權

本項目基於原有 SSL-GCN 模型，遵循相應的授權條款。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！ 