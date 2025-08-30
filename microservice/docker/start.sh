#!/bin/bash

# SSL-GCN 毒性預測服務啟動腳本

echo "🚀 啟動 SSL-GCN 毒性預測微服務..."

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

# 檢查 Docker Compose 是否安裝
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 進入 docker 目錄
cd "$(dirname "$0")"

# 建置並啟動服務
echo "📦 建置 Docker 映像..."
docker-compose build

echo "🔄 啟動服務..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查健康狀態
echo "🏥 檢查服務健康狀態..."
if curl -f http://localhost:8007/health > /dev/null 2>&1; then
    echo "✅ 服務啟動成功！"
    echo "📊 API 文檔: http://localhost:8007/docs"
    echo "🔍 健康檢查: http://localhost:8007/health"
    echo "📋 模型資訊: http://localhost:8007/model/info"
else
    echo "❌ 服務啟動失敗，請檢查日誌"
    docker-compose logs
    exit 1
fi

echo ""
echo "🎉 SSL-GCN 毒性預測服務已成功啟動！"
echo "📍 服務地址: http://localhost:8007"
echo "📚 API 文檔: http://localhost:8007/docs"
echo ""
echo "💡 使用範例:"
echo "curl -X POST http://localhost:8007/predict/single \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"molecule_id\":\"TEST\",\"smiles\":\"CCO\",\"task_type\":\"NR-AR\"}'" 