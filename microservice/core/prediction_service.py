#coding=utf-8
import os
import torch
import numpy as np
import pandas as pd
import tempfile
import shutil
from typing import List, Dict, Any
from torch.utils.data import DataLoader

# 導入原有模組
from utils import init_featurizer, load_dataset, get_self_configure, mkdir_p, collate_molgraphs, load_model, predict, read_fasta

class ToxicityPredictionService:
    """毒性預測服務核心類別"""
    
    def __init__(self):
        """初始化預測服務"""
        self.supported_tasks = [
            'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase',
            'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE',
            'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
        ]
        self.model_root = "model"
        self.device = torch.device('cpu')
        
        # 預載入模型配置
        self.model_configs = {}
        for task in self.supported_tasks:
            config_path = os.path.join(self.model_root, task, 'configure.json')
            if os.path.exists(config_path):
                self.model_configs[task] = get_self_configure(config_path)
    
    def _validate_task_type(self, task_type: str) -> None:
        """驗證任務類型"""
        if task_type not in self.supported_tasks:
            raise ValueError(f"不支援的任務類型: {task_type}。支援的類型: {self.supported_tasks}")
    
    def _create_temp_fasta(self, molecules: List[Dict[str, str]]) -> str:
        """創建臨時FASTA檔案"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False)
        try:
            for mol in molecules:
                temp_file.write(f">{mol['molecule_id']}\n")
                temp_file.write(f"{mol['smiles']}\n")
            temp_file.close()
            return temp_file.name
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            raise e
    
    def _prediction(self, args: Dict[str, Any], exp_config: Dict[str, Any], data_set) -> Dict[str, List]:
        """執行預測邏輯"""
        exp_config.update({
            'model': args['model'],
            'n_tasks': args['n_tasks'],
            'atom_featurizer_type': args['atom_featurizer_type'],
            'bond_featurizer_type': args['bond_featurizer_type']
        })
        
        test_loader = DataLoader(
            dataset=data_set, 
            batch_size=len(data_set), 
            collate_fn=collate_molgraphs, 
            num_workers=0
        )
        
        model = load_model(exp_config).to(self.device)
        model.load_state_dict(
            torch.load(args['model_data_path']+'/model.pth', map_location=self.device)['model_state_dict']
        )
        
        result = {'id': [], 'smiles': [], 'pre': []}
        model.eval()
        
        with torch.no_grad():
            for batch_id, batch_data in enumerate(test_loader):
                smiles, bg, idx = batch_data
                logits = predict(args, model, bg)
                proba = torch.sigmoid(logits).squeeze(1)
                result['id'].extend(np.array(idx).squeeze(1))
                result['smiles'].extend(smiles)
                result['pre'].extend((proba.detach().cpu().data > exp_config['t1']).int().numpy())
        
        return result
    
    def predict_single(self, molecule_id: str, smiles: str, task_type: str) -> Dict[str, Any]:
        """單一分子預測"""
        try:
            self._validate_task_type(task_type)
            
            # 創建臨時目錄
            temp_dir = tempfile.mkdtemp()
            temp_fasta = None
            
            try:
                # 執行預測
                result = self._predict_batch_internal([{'molecule_id': molecule_id, 'smiles': smiles}], task_type, temp_dir)
                
                if result and len(result) > 0:
                    prediction_result = result[0]
                    return {
                        "molecule_id": prediction_result["molecule_id"],
                        "smiles": prediction_result["smiles"],
                        "prediction": prediction_result["prediction"],
                        "confidence": prediction_result.get("confidence"),
                        "status": prediction_result["status"]
                    }
                else:
                    return {
                        "molecule_id": molecule_id,
                        "smiles": smiles,
                        "prediction": "invalid mol",
                        "confidence": None,
                        "status": "error"
                    }
                    
            finally:
                # 清理臨時檔案
                if temp_fasta and os.path.exists(temp_fasta):
                    os.unlink(temp_fasta)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    
        except ValueError as e:
            # 任務類型驗證錯誤
            return {
                "molecule_id": molecule_id,
                "smiles": smiles,
                "prediction": "error",
                "confidence": None,
                "status": "error",
                "error_message": str(e)
            }
        except Exception as e:
            # 其他預測錯誤
            return {
                "molecule_id": molecule_id,
                "smiles": smiles,
                "prediction": "invalid mol",
                "confidence": None,
                "status": "error",
                "error_message": f"預測失敗: {str(e)}"
            }
    
    def predict_batch(self, molecules: List[Dict[str, str]], task_type: str) -> List[Dict[str, Any]]:
        """批次分子預測"""
        self._validate_task_type(task_type)
        
        if not molecules:
            raise ValueError("分子列表不能為空")
        
        # 創建臨時目錄
        temp_dir = tempfile.mkdtemp()
        try:
            result = self._predict_batch_internal(molecules, task_type, temp_dir)
            return result
        finally:
            # 清理臨時檔案
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _predict_batch_internal(self, molecules: List[Dict[str, str]], task_type: str, output_dir: str) -> List[Dict[str, Any]]:
        """內部批次預測邏輯"""
        # 創建臨時FASTA檔案
        temp_fasta = self._create_temp_fasta(molecules)
        
        try:
            # 設定參數
            pretrain_folder_path = os.path.join(self.model_root, task_type)

            args = {
                'task_names': task_type,
                'smiles_column': 'SMILES',
                'model': 'GCN',
                'result_path': output_dir,
                'model_data_path': pretrain_folder_path,
                'atom_featurizer_type': 'canonical',
                'bond_featurizer_type': 'canonical'
            }
            
            args = init_featurizer(args)
            args['device'] = self.device
            args['task_names'] = [args['task_names']]
            
            # 讀取數據
            trans_mol, dataset = read_fasta(args, temp_fasta)
            args['n_tasks'] = dataset.n_tasks
            args['valid_mol_ids'] = set(dataset.valid_ids)
            args['in_mol_ids'] = set([i for i in range(len(trans_mol['id']))])
            args['invalid_mol_ids'] = list(args['valid_mol_ids'] ^ args['in_mol_ids'])
            
            # 獲取模型配置
            exp_config = get_self_configure(args['model_data_path'] + '/configure.json')
            
            # 執行預測
            result = self._prediction(args, exp_config, dataset)
            
            # 處理無效分子
            if args['invalid_mol_ids']:
                try:
                    result['id'].extend(np.array(trans_mol['id'])[args['invalid_mol_ids']])
                    result['smiles'].extend(np.array(trans_mol['SMILES'])[args['invalid_mol_ids']])
                    result['pre'].extend(['invalid mol']*len(args['invalid_mol_ids']))
                except (IndexError, TypeError) as e:
                    # 如果索引出錯，添加默認的無效分子結果
                    for invalid_id in args['invalid_mol_ids']:
                        if invalid_id < len(trans_mol['id']):
                            result['id'].append(trans_mol['id'][invalid_id])
                            result['smiles'].append(trans_mol['SMILES'][invalid_id])
                            result['pre'].append('invalid mol')
            
            # 格式化結果
            formatted_results = []
            for i in range(len(result['id'])):
                prediction_value = result['pre'][i]
                if prediction_value == 'invalid mol':
                    status = "error"
                    confidence = None
                else:
                    status = "success"
                    confidence = float(prediction_value) if isinstance(prediction_value, (int, float)) else None
                
                formatted_results.append({
                    "molecule_id": result['id'][i],
                    "smiles": result['smiles'][i],
                    "prediction": str(prediction_value),
                    "confidence": confidence,
                    "status": status
                })
            
            return formatted_results
            
        finally:
            # 清理臨時FASTA檔案
            if os.path.exists(temp_fasta):
                os.unlink(temp_fasta) 