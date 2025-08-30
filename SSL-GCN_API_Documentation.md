# SSL-GCN 毒性預測 API 文檔

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-repo/ssl-gcn)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-red.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

## 📋 概述

SSL-GCN 是一個基於**半監督學習（Semi-Supervised Learning）**和**圖卷積神經網絡（Graph Convolutional Networks）**的先進化學分子毒性預測微服務。本服務採用 Mean Teacher 算法和圖神經網絡技術，能夠準確預測 SMILES 格式化學分子在多種毒理學端點上的毒性特性。

### 🎯 主要特色

- 🧬 **圖神經網絡技術**：直接在分子圖結構上進行學習，比傳統分子指紋方法更精確
- 🤖 **半監督學習**：採用 Mean Teacher 算法，能有效利用無標籤數據提升預測性能
- 🎯 **多端點支持**：支援 12 種標準毒理學測定端點（Tox21 標準）
- ⚡ **高效能服務**：FastAPI 框架，支援非同步處理
- 📊 **批量處理**：支援一次處理多個分子的毒性預測
- 🐳 **容器化部署**：完整的 Docker 支援，一鍵部署

### 🔬 支持的毒性端點

#### NR 系列（核受體相關）
- **NR-AR**: 雄性激素受體 | **NR-AR-LBD**: AR 配體結合域 | **NR-AhR**: 芳基羥基化合物受體
- **NR-Aromatase**: 芳香化酶 | **NR-ER**: 雌激素受體 | **NR-ER-LBD**: ER 配體結合域
- **NR-PPAR-gamma**: 過氧化物酶體增殖物激活受體 γ

#### SR 系列（壓力反應相關）
- **SR-ARE**: 抗氧化反應元件 | **SR-ATAD5**: ATPase 家族蛋白 | **SR-HSE**: 熱休克元件
- **SR-MMP**: 線粒體膜電位 | **SR-p53**: p53 蛋白（腫瘤抑制因子）

## 🚀 快速開始

### Docker 部署（推薦）

```bash
# 下載並啟動服務
git clone <your-repo-url>
cd SSL-GCN/microservice/docker
docker compose up --build -d

# 驗證服務
curl http://localhost:8007/health
```

### 基礎資訊

| 參數 | 值 |
|------|-----|
| **基礎 URL** | `http://localhost:8007` |
| **API 版本** | `1.0.0` |
| **內容類型** | `application/json` |

## 📖 API 端點

### 基礎端點

| HTTP 方法 | 端點 | 功能描述 |
|-----------|------|----------|
| `GET` | `/` | 服務基本資訊 |
| `GET` | `/health` | 健康檢查 |
| `GET` | `/model/info` | 模型詳細資訊 |
| `GET` | `/predict/tasks` | 支援的毒性端點列表 |

### 預測端點

#### `POST /predict/single` - 單一分子預測

**請求格式**：
```json
{
  "molecule_id": "test_molecule_1",
  "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "task_type": "NR-AR"
}
```

**成功回應**：
```json
{
  "molecule_id": "test_molecule_1",
  "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
  "prediction": "0",  // "0" = 無毒, "1" = 有毒
  "confidence": null,
  "status": "success"
}
```

#### `POST /predict/batch` - 批量分子預測

**請求格式**：
```json
{
  "molecules": [
    {"molecule_id": "mol_1", "smiles": "CCO"},
    {"molecule_id": "mol_2", "smiles": "CO"}
  ],
  "task_type": "NR-AR"
}
```

**回應格式**：返回分子預測結果的陣列，格式與單一預測相同。

## 📝 Laravel 整合範例

### 服務類別

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class SSLGCNToxicityService
{
    private string $baseUrl = 'http://localhost:8007';
    private int $timeout = 30;

    public function checkHealth(): array
    {
        try {
            $response = Http::timeout($this->timeout)->get($this->baseUrl . '/health');
            return $response->successful() ? 
                ['success' => true, 'data' => $response->json()] :
                ['success' => false, 'error' => 'Health check failed'];
        } catch (\Exception $e) {
            return ['success' => false, 'error' => $e->getMessage()];
        }
    }

    public function getSupportedTasks(): array
    {
        try {
            $response = Http::timeout($this->timeout)->get($this->baseUrl . '/predict/tasks');
            return $response->successful() ? 
                ['success' => true, 'tasks' => $response->json()] :
                ['success' => false, 'error' => 'Failed to get tasks'];
        } catch (\Exception $e) {
            return ['success' => false, 'error' => $e->getMessage()];
        }
    }

    public function predictSingle(string $moleculeId, string $smiles, string $taskType): array
    {
        try {
            $data = [
                'molecule_id' => $moleculeId,
                'smiles' => $smiles,
                'task_type' => $taskType
            ];

            $response = Http::timeout($this->timeout)
                ->post($this->baseUrl . '/predict/single', $data);

            return $response->successful() ? 
                ['success' => true, 'prediction' => $response->json()] :
                ['success' => false, 'error' => 'Prediction failed'];
        } catch (\Exception $e) {
            return ['success' => false, 'error' => $e->getMessage()];
        }
    }

    public function predictBatch(array $molecules, string $taskType): array
    {
        try {
            $data = [
                'molecules' => $molecules,
                'task_type' => $taskType
            ];

            $response = Http::timeout($this->timeout * 2)
                ->post($this->baseUrl . '/predict/batch', $data);

            return $response->successful() ? 
                ['success' => true, 'predictions' => $response->json()] :
                ['success' => false, 'error' => 'Batch prediction failed'];
        } catch (\Exception $e) {
            return ['success' => false, 'error' => $e->getMessage()];
        }
    }

    public function validateTaskType(string $taskType): bool
    {
        $supportedTasks = [
            'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase',
            'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE',
            'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
        ];
        return in_array($taskType, $supportedTasks);
    }
}
```

### 控制器範例

```php
<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\SSLGCNToxicityService;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Validation\Rule;

class ToxicityPredictionController extends Controller
{
    private SSLGCNToxicityService $toxicityService;

    public function __construct(SSLGCNToxicityService $toxicityService)
    {
        $this->toxicityService = $toxicityService;
    }

    public function getSupportedTasks(): JsonResponse
    {
        $result = $this->toxicityService->getSupportedTasks();
        
        return $result['success'] ? 
            response()->json(['success' => true, 'data' => $result['tasks']]) :
            response()->json(['success' => false, 'message' => $result['error']], 500);
    }

    public function predictSingle(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'molecule_id' => 'required|string|max:255',
            'smiles' => 'required|string|max:300',
            'task_type' => ['required', Rule::in([
                'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase',
                'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE',
                'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
            ])]
        ]);

        $result = $this->toxicityService->predictSingle(
            $validated['molecule_id'],
            $validated['smiles'], 
            $validated['task_type']
        );

        return $result['success'] ? 
            response()->json(['success' => true, 'data' => $result['prediction']]) :
            response()->json(['success' => false, 'message' => $result['error']], 500);
    }

    public function predictBatch(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'molecules' => 'required|array|max:50',
            'molecules.*.molecule_id' => 'required|string|max:255',
            'molecules.*.smiles' => 'required|string|max:300',
            'task_type' => ['required', Rule::in([
                'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase',
                'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE',
                'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
            ])]
        ]);

        $result = $this->toxicityService->predictBatch(
            $validated['molecules'],
            $validated['task_type']
        );

        return $result['success'] ? 
            response()->json(['success' => true, 'data' => $result['predictions']]) :
            response()->json(['success' => false, 'message' => $result['error']], 500);
    }

    public function healthCheck(): JsonResponse
    {
        $result = $this->toxicityService->checkHealth();
        
        return $result['success'] ? 
            response()->json(['success' => true, 'data' => $result['data']]) :
            response()->json(['success' => false, 'message' => $result['error']], 503);
    }
}
```

## 📝 使用範例

### cURL 測試

```bash
# 健康檢查
curl http://localhost:8007/health

# 單一預測
curl -X POST http://localhost:8007/predict/single \
  -H "Content-Type: application/json" \
  -d '{"molecule_id": "aspirin", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "task_type": "NR-AR"}'

# 批量預測
curl -X POST http://localhost:8007/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"molecules": [{"molecule_id": "ethanol", "smiles": "CCO"}], "task_type": "SR-p53"}'
```

### Python 範例

```python
import requests

class SSLGCNClient:
    def __init__(self, base_url="http://localhost:8007"):
        self.base_url = base_url

    def predict_single(self, molecule_id, smiles, task_type):
        data = {"molecule_id": molecule_id, "smiles": smiles, "task_type": task_type}
        response = requests.post(f"{self.base_url}/predict/single", json=data)
        return response.json()

    def predict_batch(self, molecules, task_type):
        data = {"molecules": molecules, "task_type": task_type}
        response = requests.post(f"{self.base_url}/predict/batch", json=data)
        return response.json()

# 使用範例
client = SSLGCNClient()
result = client.predict_single("test", "CCO", "NR-AR")
print(result)
```

## ⚠️ 錯誤處理

### 常見錯誤

| 錯誤類型 | 解決方案 |
|----------|----------|
| 無效毒性端點 | 使用 `/predict/tasks` 獲取支援的端點 |
| SMILES 格式錯誤 | 檢查 SMILES 字符串有效性 |
| 服務不可用 | 檢查 Docker 容器狀態 |

### HTTP 狀態碼

- `200`: 成功（包含預測成功和失敗）
- `422`: 驗證錯誤
- `500`: 內部伺服器錯誤
- `503`: 服務不可用

## 🔧 配置與部署

### 環境變數

```yaml
# docker-compose.yml
services:
  ssl-gcn-api:
    environment:
      - PYTHONUNBUFFERED=1
      - API_PORT=8007
    ports:
      - "8007:8007"
```

### Docker 管理

```bash
# 啟動服務
docker compose up -d

# 檢查狀態
docker compose ps

# 查看日誌
docker compose logs ssl-gcn-api

# 重啟服務
docker compose restart ssl-gcn-api

# 停止服務
docker compose down
```

## 📊 性能規格

| 指標 | 值 |
|------|-----|
| **預測延遲** | ~200ms |
| **併發支援** | 5+ 併發 |
| **記憶體使用** | ~500MB |
| **建議批量大小** | ≤ 50 分子 |

## 📚 技術背景

SSL-GCN 基於 2021 年發表的學術研究，結合了：
- **半監督學習**：Mean Teacher 算法
- **圖神經網絡**：GCN 架構
- **分子表示**：SMILES → 分子圖轉換
- **毒性預測**：Tox21 標準端點

## 🔗 相關資源

- **互動式文檔**: [http://localhost:8007/docs](http://localhost:8007/docs)
- **ReDoc 文檔**: [http://localhost:8007/redoc](http://localhost:8007/redoc)
- **OpenAPI JSON**: [http://localhost:8007/openapi.json](http://localhost:8007/openapi.json)

---

**© 2025 SSL-GCN 開發團隊** | *文檔最後更新：2025年1月20日*