#coding=utf-8
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from microservice.core.prediction_service import ToxicityPredictionService

app = FastAPI(
    title="SSL-GCN 毒性預測 API",
    description="基於半監督學習和圖卷積神經網絡的化學毒性預測服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 初始化預測服務
prediction_service = ToxicityPredictionService()

# 請求模型
class SinglePredictionRequest(BaseModel):
    molecule_id: str
    smiles: str
    task_type: str

class BatchPredictionRequest(BaseModel):
    molecules: List[Dict[str, str]]
    task_type: str

# 回應模型
class PredictionResponse(BaseModel):
    molecule_id: str
    smiles: str
    prediction: str
    confidence: Optional[float] = None
    status: str

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class ModelInfoResponse(BaseModel):
    model_name: str
    version: str
    supported_tasks: List[str]
    description: str

@app.get("/", response_model=Dict[str, str])
async def root():
    """根端點"""
    return {"message": "SSL-GCN 毒性預測服務", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "message": "服務運行正常",
        "version": "1.0.0"
    }

@app.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """獲取模型資訊"""
    return {
        "model_name": "SSL-GCN",
        "version": "1.0.0",
        "supported_tasks": [
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase",
            "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma", "SR-ARE",
            "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
        ],
        "description": "基於半監督學習和圖卷積神經網絡的化學毒性預測模型"
    }

@app.post("/predict/single", response_model=PredictionResponse)
async def predict_single(request: SinglePredictionRequest):
    """單一分子毒性預測"""
    try:
        result = prediction_service.predict_single(
            molecule_id=request.molecule_id,
            smiles=request.smiles,
            task_type=request.task_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/batch", response_model=List[PredictionResponse])
async def predict_batch(request: BatchPredictionRequest):
    """批次分子毒性預測"""
    try:
        results = prediction_service.predict_batch(
            molecules=request.molecules,
            task_type=request.task_type
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/predict/tasks", response_model=List[str])
async def get_supported_tasks():
    """獲取支援的毒性端點列表"""
    return [
        "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase",
        "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma", "SR-ARE",
        "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
    ]

if __name__ == "__main__":
    uvicorn.run(
        "microservice.api.app:app",
        host="0.0.0.0",
        port=8007,
        reload=True
    ) 