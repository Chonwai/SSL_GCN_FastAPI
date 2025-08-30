#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL-GCN API 測試腳本
測試所有API端點的功能和錯誤處理
"""

import requests
import json
import time
from typing import Dict, List, Any

class SSLGCNAPITester:
    def __init__(self, base_url: str = "http://localhost:8007"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def print_test_header(self, test_name: str):
        """打印測試標題"""
        print(f"\n{'='*60}")
        print(f"🧪 測試: {test_name}")
        print(f"{'='*60}")
    
    def print_result(self, success: bool, response_data: Any = None, error: str = None):
        """打印測試結果"""
        if success:
            print(f"✅ 成功")
            if response_data:
                print(f"回應: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 失敗")
            if error:
                print(f"錯誤: {error}")
                
    def test_health_check(self):
        """測試健康檢查端點"""
        self.print_test_header("健康檢查")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            self.print_result(True, response.json())
            return True
        except Exception as e:
            self.print_result(False, error=str(e))
            return False
    
    def test_root_endpoint(self):
        """測試根端點"""
        self.print_test_header("根端點")
        try:
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            self.print_result(True, response.json())
            return True
        except Exception as e:
            self.print_result(False, error=str(e))
            return False
    
    def test_model_info(self):
        """測試模型信息端點"""
        self.print_test_header("模型信息")
        try:
            response = self.session.get(f"{self.base_url}/model/info")
            response.raise_for_status()
            data = response.json()
            self.print_result(True, data)
            
            # 驗證回應格式
            required_fields = ["model_name", "version", "supported_tasks", "description"]
            for field in required_fields:
                if field not in data:
                    print(f"⚠️  缺少必要字段: {field}")
                    return False
            
            print(f"📊 支持的毒性端點數量: {len(data['supported_tasks'])}")
            return True
        except Exception as e:
            self.print_result(False, error=str(e))
            return False
    
    def test_supported_tasks(self):
        """測試支持的任務列表"""
        self.print_test_header("支持的任務列表")
        try:
            response = self.session.get(f"{self.base_url}/predict/tasks")
            response.raise_for_status()
            tasks = response.json()
            self.print_result(True, tasks)
            print(f"📝 共支持 {len(tasks)} 個毒性端點")
            return tasks
        except Exception as e:
            self.print_result(False, error=str(e))
            return []
    
    def test_single_prediction(self, molecule_id: str, smiles: str, task_type: str):
        """測試單一分子預測"""
        self.print_test_header(f"單一分子預測 - {molecule_id}")
        try:
            data = {
                "molecule_id": molecule_id,
                "smiles": smiles,
                "task_type": task_type
            }
            response = self.session.post(f"{self.base_url}/predict/single", json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.print_result(True, result)
                return result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.print_result(False, error=error_msg)
                return None
        except Exception as e:
            self.print_result(False, error=str(e))
            return None
    
    def test_batch_prediction(self, molecules: List[Dict[str, str]], task_type: str):
        """測試批次分子預測"""
        self.print_test_header(f"批次分子預測 - {len(molecules)} 個分子")
        try:
            data = {
                "molecules": molecules,
                "task_type": task_type
            }
            response = self.session.post(f"{self.base_url}/predict/batch", json=data)
            
            if response.status_code == 200:
                results = response.json()
                self.print_result(True, results)
                print(f"📊 預測完成 {len(results)} 個分子")
                
                # 統計結果
                success_count = sum(1 for r in results if r.get('status') == 'success')
                error_count = len(results) - success_count
                print(f"✅ 成功: {success_count} 個")
                print(f"❌ 失敗: {error_count} 個")
                
                return results
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.print_result(False, error=error_msg)
                return None
        except Exception as e:
            self.print_result(False, error=str(e))
            return None
    
    def test_error_handling(self):
        """測試錯誤處理"""
        self.print_test_header("錯誤處理測試")
        
        # 測試無效SMILES
        print("\n🔍 測試無效SMILES...")
        result = self.test_single_prediction("INVALID_TEST", "INVALID_SMILES", "NR-AR")
        
        # 測試無效任務類型
        print("\n🔍 測試無效任務類型...")
        try:
            data = {
                "molecule_id": "TEST",
                "smiles": "CCO",
                "task_type": "INVALID_TASK"
            }
            response = self.session.post(f"{self.base_url}/predict/single", json=data)
            print(f"狀態碼: {response.status_code}")
            print(f"回應: {response.text}")
        except Exception as e:
            print(f"錯誤: {e}")
        
        # 測試空分子列表
        print("\n🔍 測試空分子列表...")
        try:
            data = {
                "molecules": [],
                "task_type": "NR-AR"
            }
            response = self.session.post(f"{self.base_url}/predict/batch", json=data)
            print(f"狀態碼: {response.status_code}")
            print(f"回應: {response.text}")
        except Exception as e:
            print(f"錯誤: {e}")
    
    def run_comprehensive_test(self):
        """運行全面測試"""
        print("🚀 開始 SSL-GCN API 全面測試")
        print(f"⏰ 測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 基礎端點測試
        tests_passed = 0
        total_tests = 0
        
        total_tests += 1
        if self.test_health_check():
            tests_passed += 1
            
        total_tests += 1
        if self.test_root_endpoint():
            tests_passed += 1
            
        total_tests += 1
        if self.test_model_info():
            tests_passed += 1
            
        supported_tasks = self.test_supported_tasks()
        if supported_tasks:
            tests_passed += 1
        total_tests += 1
        
        # 預測功能測試
        if supported_tasks:
            # 測試分子
            test_molecules = [
                {"molecule_id": "ETHANOL", "smiles": "CCO"},
                {"molecule_id": "METHANOL", "smiles": "CO"},
                {"molecule_id": "WATER", "smiles": "O"},
                {"molecule_id": "ASPIRIN", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"},
                {"molecule_id": "CAFFEINE", "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"}
            ]
            
            # 測試前3個端點
            for i, task in enumerate(supported_tasks[:3]):
                print(f"\n🎯 測試端點: {task} ({i+1}/{min(3, len(supported_tasks))})")
                
                # 單一預測
                result = self.test_single_prediction(
                    test_molecules[0]["molecule_id"], 
                    test_molecules[0]["smiles"], 
                    task
                )
                if result:
                    tests_passed += 1
                total_tests += 1
                
                # 批次預測
                result = self.test_batch_prediction(test_molecules[:3], task)
                if result:
                    tests_passed += 1
                total_tests += 1
        
        # 錯誤處理測試
        self.test_error_handling()
        
        # 測試總結
        self.print_test_header("測試總結")
        print(f"📊 通過測試: {tests_passed}/{total_tests}")
        print(f"📈 成功率: {(tests_passed/total_tests)*100:.1f}%")
        
        if tests_passed == total_tests:
            print("🎉 所有測試通過！API 運行正常。")
        else:
            print("⚠️  部分測試失敗，請檢查服務狀態。")
        
        return tests_passed, total_tests

if __name__ == "__main__":
    # 運行測試
    tester = SSLGCNAPITester()
    passed, total = tester.run_comprehensive_test()
    
    # 退出碼
    exit(0 if passed == total else 1)