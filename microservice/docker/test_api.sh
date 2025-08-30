#!/bin/bash

# SSL-GCN API 測試腳本

echo "🧪 測試 SSL-GCN 毒性預測 API..."

BASE_URL="http://localhost:8007"

# 測試健康檢查
echo "1. 測試健康檢查..."
curl -s "${BASE_URL}/health" | jq '.' || echo "健康檢查失敗"

echo ""

# 測試模型資訊
echo "2. 測試模型資訊..."
curl -s "${BASE_URL}/model/info" | jq '.' || echo "模型資訊獲取失敗"

echo ""

# 測試支援的任務列表
echo "3. 測試支援的任務列表..."
curl -s "${BASE_URL}/predict/tasks" | jq '.' || echo "任務列表獲取失敗"

echo ""

# 測試單一分子預測
echo "4. 測試單一分子預測..."
curl -s -X POST "${BASE_URL}/predict/single" \
  -H "Content-Type: application/json" \
  -d '{
    "molecule_id": "TEST001",
    "smiles": "CCO",
    "task_type": "NR-AR"
  }' | jq '.' || echo "單一預測失敗"

echo ""

# 測試批次分子預測
echo "5. 測試批次分子預測..."
curl -s -X POST "${BASE_URL}/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "molecules": [
      {"molecule_id": "TEST001", "smiles": "CCO"},
      {"molecule_id": "TEST002", "smiles": "CCCO"},
      {"molecule_id": "TEST003", "smiles": "CCCC"}
    ],
    "task_type": "NR-AR"
  }' | jq '.' || echo "批次預測失敗"

echo ""

# 測試無效SMILES
echo "6. 測試無效SMILES..."
curl -s -X POST "${BASE_URL}/predict/single" \
  -H "Content-Type: application/json" \
  -d '{
    "molecule_id": "INVALID",
    "smiles": "INVALID_SMILES",
    "task_type": "NR-AR"
  }' | jq '.' || echo "無效SMILES測試失敗"

echo ""

echo "✅ API 測試完成！" 