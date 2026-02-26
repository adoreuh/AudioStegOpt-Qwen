"""
HuggingFace格式Qwen模型加载器
用于直接加载HuggingFace transformers格式的模型
"""

import os
import json
import logging
import time
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# 模型配置
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
HF_MODEL_PATH = os.path.join(MODEL_DIR, "qwen_hf")


class QwenHFModel:
    """Qwen HuggingFace格式模型管理器"""
    
    _instance = None
    _model = None
    _tokenizer = None
    _initialized = False
    _model_path = None
    _load_time = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_model()
    
    def _find_model_path(self) -> Optional[str]:
        """查找模型文件路径"""
        # 检查HuggingFace格式模型
        if os.path.exists(HF_MODEL_PATH):
            config_path = os.path.join(HF_MODEL_PATH, "config.json")
            if os.path.exists(config_path):
                logger.info(f"找到HuggingFace格式模型: {HF_MODEL_PATH}")
                return HF_MODEL_PATH
        
        # 检查其他可能的位置
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        alternative_paths = [
            os.path.join(project_root, "Qwen", "Qwen3-0___6B"),
            os.path.join(MODEL_DIR, "Qwen3-0___6B"),
        ]
        
        for path in alternative_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "config.json")):
                logger.info(f"找到模型: {path}")
                return path
        
        logger.warning("未找到HuggingFace格式模型文件")
        return None
    
    def _initialize_model(self):
        """初始化模型"""
        start_time = time.time()
        
        try:
            logger.info("正在初始化Qwen3:0.6b HuggingFace模型...")
            
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = self._find_model_path()
            
            if model_path is None:
                logger.warning("模型文件不存在")
                self._initialized = False
                return
            
            self._model_path = model_path
            logger.info(f"从路径加载模型: {model_path}")
            
            # 加载tokenizer
            logger.info("加载Tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            # 加载模型 - 使用优化配置
            logger.info("加载模型...")
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True,
                local_files_only=True
            )
            
            self._model.eval()
            self._initialized = True
            self._load_time = time.time() - start_time
            
            logger.info(f"✓ 模型初始化完成，加载耗时: {self._load_time:.2f}秒")
            
        except ImportError as e:
            logger.warning(f"transformers库未安装: {e}")
            logger.info("请运行: pip install transformers torch")
            self._initialized = False
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self._initialized and self._model is not None and self._tokenizer is not None
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        if not self.is_available():
            return {"status": "未加载"}
        
        try:
            param_count = sum(p.numel() for p in self._model.parameters())
            return {
                "status": "已加载",
                "model_path": self._model_path,
                "load_time": f"{self._load_time:.2f}s",
                "parameters": f"{param_count / 1e6:.0f}M",
                "format": "HuggingFace",
                "device": "cpu"
            }
        except:
            return {
                "status": "已加载",
                "model_path": self._model_path,
                "load_time": f"{self._load_time:.2f}s",
                "format": "HuggingFace"
            }
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """生成文本"""
        if not self.is_available():
            return ""
        
        try:
            import torch
            
            # 构建对话格式
            messages = [
                {"role": "system", "content": "你是一个专业的音频信息隐藏专家，擅长分析和优化音频隐写参数。"},
                {"role": "user", "content": prompt}
            ]
            
            # 应用对话模板
            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # 编码输入
            inputs = self._tokenizer(text, return_tensors="pt")
            
            # 生成
            with torch.no_grad():
                outputs = self._model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True if temperature > 0 else False,
                    top_p=0.9,
                    pad_token_id=self._tokenizer.eos_token_id
                )
            
            # 解码输出
            generated_text = self._tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            return ""
    
    def chat(self, messages: List[Dict], max_tokens: int = 500, temperature: float = 0.7) -> str:
        """对话接口"""
        if not self.is_available():
            return ""
        
        try:
            import torch
            
            # 应用对话模板
            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # 编码输入
            inputs = self._tokenizer(text, return_tensors="pt")
            
            # 生成
            with torch.no_grad():
                outputs = self._model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True if temperature > 0 else False,
                    top_p=0.9,
                    pad_token_id=self._tokenizer.eos_token_id
                )
            
            # 解码输出
            generated_text = self._tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"对话失败: {e}")
            return ""
    
    def unload(self):
        """卸载模型释放内存"""
        if self._model is not None:
            import torch
            del self._model
            del self._tokenizer
            self._model = None
            self._tokenizer = None
            self._initialized = False
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            logger.info("模型已卸载，内存已释放")


class QwenHFIntegration:
    """Qwen HuggingFace模型集成接口"""
    
    def __init__(self):
        self.model = QwenHFModel()
        self._initialized = self.model.is_available()
    
    def check_model_availability(self) -> bool:
        """检查模型可用性"""
        return self.model.is_available()
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return self.model.get_model_info()
    
    def generate_response(self, prompt: str, temperature: float = 0.7, 
                         max_tokens: int = 500) -> str:
        """生成响应"""
        if not self._initialized:
            return ""
        
        return self.model.generate(prompt, max_tokens, temperature)
    
    def chat_completion(self, messages: list, temperature: float = 0.7,
                       max_tokens: int = 500) -> str:
        """聊天补全"""
        if not self._initialized:
            return ""
        
        return self.model.chat(messages, max_tokens, temperature)
    
    def optimize_embedding_parameters(self, audio_info: Dict, message_length: int) -> Dict:
        """优化嵌入参数"""
        prompt = f"""作为音频信息隐藏专家，请根据以下信息优化嵌入参数：

音频信息：
- 时长: {audio_info.get('duration', 0):.2f}秒
- 采样率: {audio_info.get('sample_rate', 0)}Hz
- 长度: {audio_info.get('length', 0)}采样点
- 最大振幅: {audio_info.get('max_amplitude', 0):.4f}

消息长度: {message_length}字符

请提供JSON格式的优化建议：
{{"layer1_dwt": 数值, "layer2_dct": 数值, "layer3_lsb": 数值, "recommendation": "建议说明"}}

确保三层数据量总和等于{message_length}。只返回JSON。"""

        response = self.generate_response(prompt, temperature=0.3)
        
        try:
            import json
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析优化响应失败: {e}")
        
        return self._get_default_distribution(message_length)
    
    def analyze_audio_quality(self, audio_info: Dict) -> Dict:
        """分析音频质量"""
        prompt = f"""分析音频质量并给出信息隐藏建议：

音频信息：
- 时长: {audio_info.get('duration', 0):.2f}秒
- 采样率: {audio_info.get('sample_rate', 0)}Hz
- RMS值: {audio_info.get('rms', 0):.4f}
- 最大振幅: {audio_info.get('max_amplitude', 0):.4f}

请提供JSON格式的分析结果：
{{"quality_score": 评分(0-100), "suitable_for_embedding": true/false, "recommended_method": "dwt/dct/lsb", "capacity_estimate": 预估容量, "risk_factors": []}}

只返回JSON。"""

        response = self.generate_response(prompt, temperature=0.3)
        
        try:
            import json
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析质量分析失败: {e}")
        
        return {
            "quality_score": 75,
            "suitable_for_embedding": True,
            "recommended_method": "dwt",
            "capacity_estimate": 1000,
            "risk_factors": []
        }
    
    def _get_default_distribution(self, total_length: int) -> Dict:
        """默认分配策略"""
        layer1 = total_length // 3
        layer2 = total_length // 3
        layer3 = total_length - layer1 - layer2
        
        return {
            "layer1_dwt": layer1,
            "layer2_dct": layer2,
            "layer3_lsb": layer3,
            "recommendation": "使用默认的三层平均分配策略"
        }


if __name__ == "__main__":
    print("=" * 60)
    print("测试Qwen3:0.6b HuggingFace模型")
    print("=" * 60)
    
    model = QwenHFIntegration()
    
    if model.check_model_availability():
        print("✓ 模型已加载")
        info = model.get_model_info()
        print(f"\n模型信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print("\n测试文本生成...")
        response = model.generate_response("你好，请简单介绍一下你自己。", max_tokens=100)
        print(f"响应: {response}")
    else:
        print("✗ 模型不可用")
        print("请确保模型文件存在于正确位置")
