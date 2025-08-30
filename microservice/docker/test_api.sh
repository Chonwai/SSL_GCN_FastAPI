#!/bin/bash

# SSL-GCN API 測試腳本
echo "🧪 開始測試 SSL-GCN 毒性預測 API..."
echo "=================================="

API_BASE="http://localhost:8007"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 測試函數
test_endpoint() {
    local test_name="$1"
    local url="$2"
    local method="$3"
    local data="$4"
    
    echo -e "\n${BLUE}🔍 測試: $test_name${NC}"
    echo "URL: $url"
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST "$url" -H "Content-Type: application/json" -d "$data")
    else
        response=$(curl -s "$url")
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 成功${NC}"
        echo "回應: $response" | jq '.' 2>/dev/null || echo "回應: $response"
    else
        echo -e "${RED}❌ 失敗${NC}"
    fi
}

# 1. 健康檢查
test_endpoint "健康檢查" "$API_BASE/health" "GET"

# 2. 根端點
test_endpoint "根端點" "$API_BASE/" "GET"

# 3. 模型信息
test_endpoint "模型信息" "$API_BASE/model/info" "GET"

# 4. 支持的任務
test_endpoint "支持的任務列表" "$API_BASE/predict/tasks" "GET"

# 5. 單一分子預測 - 乙醇
single_data='{
  "molecule_id": "ETHANOL_TEST",
  "smiles": "CCO",
  "task_type": "NR-AR"
}'
test_endpoint "單一分子預測 (乙醇)" "$API_BASE/predict/single" "POST" "$single_data"

# 6. 單一分子預測 - 阿司匹林
aspirin_data='{
  "molecule_id": "ASPIRIN_TEST",
  "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "task_type": "NR-ER"
}'
test_endpoint "單一分子預測 (阿司匹林)" "$API_BASE/predict/single" "POST" "$aspirin_data"

# 7. 批次預測
batch_data='{
  "molecules": [
    {"molecule_id": "WATER", "smiles": "O"},
    {"molecule_id": "METHANOL", "smiles": "CO"},
    {"molecule_id": "ACETONE", "smiles": "CC(=O)C"},
    {"molecule_id": "BENZENE", "smiles": "C1=CC=CC=C1"}
  ],
  "task_type": "SR-p53"
}'
test_endpoint "批次分子預測" "$API_BASE/predict/batch" "POST" "$batch_data"

# 8. 測試不同的毒性端點
echo -e "\n${YELLOW}🎯 測試不同毒性端點...${NC}"

endpoints=("NR-AR" "NR-ER" "SR-ARE" "SR-p53")
test_molecule='{
  "molecule_id": "CAFFEINE_MULTI_TEST",
  "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
  "task_type": "ENDPOINT_PLACEHOLDER"
}'

for endpoint in "${endpoints[@]}"; do
    endpoint_data=$(echo "$test_molecule" | sed "s/ENDPOINT_PLACEHOLDER/$endpoint/")
    test_endpoint "咖啡因 @ $endpoint" "$API_BASE/predict/single" "POST" "$endpoint_data"
done

# 9. 錯誤處理測試
echo -e "\n${YELLOW}⚠️  測試錯誤處理...${NC}"

# 無效任務類型
invalid_task_data='{
  "molecule_id": "INVALID_TASK_TEST",
  "smiles": "CCO",
  "task_type": "INVALID_TASK"
}'
test_endpoint "無效任務類型" "$API_BASE/predict/single" "POST" "$invalid_task_data"

# 空分子列表
empty_batch_data='{
  "molecules": [],
  "task_type": "NR-AR"
}'
test_endpoint "空分子列表" "$API_BASE/predict/batch" "POST" "$empty_batch_data"

echo -e "\n${GREEN}🎉 API測試完成！${NC}"
echo "=================================="