import os
import sys
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

class LocalQwenModel:
    _instance = None
    _model = None
    _tokenizer = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_model()
    
    def _initialize_model(self):
        try:
            logger.info("正在初始化本地Qwen模型...")
            
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = os.path.join(MODEL_DIR, "qwen2.5-0.5b-instruct")
            
            if os.path.exists(model_path) and os.path.exists(os.path.join(model_path, "config.json")):
                logger.info(f"从本地路径加载模型: {model_path}")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_path, 
                    trust_remote_code=True,
                    local_files_only=True
                )
                self._model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                    local_files_only=True
                )
                
                self._model.eval()
                self._initialized = True
                logger.info("本地Qwen模型初始化完成")
            else:
                logger.info(f"本地模型不存在: {model_path}")
                logger.info("请运行 'python -m audio_stego.utils.local_qwen --download' 下载模型")
                self._initialized = False
            
        except ImportError as e:
            logger.warning(f"transformers库未安装: {e}")
            self._initialized = False
        except Exception as e:
            logger.warning(f"模型初始化失败，将使用回退模式: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        return self._initialized and self._model is not None
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        if not self.is_available():
            return ""
        
        try:
            import torch
            
            messages = [
                {"role": "system", "content": "你是一个专业的音频信息隐藏专家，擅长分析和优化音频隐写参数。"},
                {"role": "user", "content": prompt}
            ]
            
            text = self._tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            inputs = self._tokenizer(text, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self._model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self._tokenizer.eos_token_id
                )
            
            generated_text = self._tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            return ""


class LocalQwenIntegration:
    def __init__(self):
        self.model = LocalQwenModel()
        self._fallback_mode = False
    
    def check_model_availability(self) -> bool:
        if self.model.is_available():
            return True
        
        try:
            import requests
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if "qwen3:0.6b" in model_names:
                    self._fallback_mode = True
                    return True
        except Exception:
            pass
        
        return False
    
    def generate_response(self, prompt: str, temperature: float = 0.7, 
                         max_tokens: int = 500) -> str:
        if self.model.is_available():
            return self.model.generate(prompt, max_tokens, temperature)
        
        if self._fallback_mode:
            try:
                import requests
                payload = {
                    "model": "qwen3:0.6b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                response = requests.post(
                    "http://127.0.0.1:11434/api/generate", 
                    json=payload, 
                    timeout=30
                )
                result = response.json()
                return result.get("response", "")
            except Exception as e:
                logger.error(f"Ollama调用失败: {e}")
        
        return ""
    
    def chat_completion(self, messages: list, temperature: float = 0.7,
                       max_tokens: int = 500) -> str:
        if self.model.is_available():
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            return self.model.generate(prompt, max_tokens, temperature)
        
        if self._fallback_mode:
            try:
                import requests
                payload = {
                    "model": "qwen3:0.6b",
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                response = requests.post(
                    "http://127.0.0.1:11434/api/chat", 
                    json=payload, 
                    timeout=30
                )
                result = response.json()
                return result.get("message", {}).get("content", "")
            except Exception as e:
                logger.error(f"Ollama聊天调用失败: {e}")
        
        return ""
    
    def optimize_embedding_parameters(self, audio_info: Dict, message_length: int) -> Dict:
        prompt = f"""作为音频信息隐藏专家，请根据以下信息优化嵌入参数：

音频信息：
- 时长: {audio_info.get('duration', 0):.2f}秒
- 采样率: {audio_info.get('sample_rate', 0)}Hz
- 长度: {audio_info.get('length', 0)}采样点
- 最大振幅: {audio_info.get('max_amplitude', 0):.4f}

消息长度: {message_length}字符

请提供JSON格式的优化建议，包括：
1. layer1_dwt: 第一层数据量（字符数）
2. layer2_dct: 第二层数据量（字符数）
3. layer3_lsb: 第三层数据量（字符数）
4. recommendation: 优化建议说明

确保三层数据量总和等于{message_length}。
只返回JSON，不要其他内容。"""
        
        response = self.generate_response(prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析优化响应失败: {e}")
        
        return self._get_default_distribution(message_length)
    
    def analyze_audio_quality(self, audio_info: Dict) -> Dict:
        prompt = f"""分析音频质量并给出信息隐藏建议：

音频信息：
- 时长: {audio_info.get('duration', 0):.2f}秒
- 采样率: {audio_info.get('sample_rate', 0)}Hz
- RMS值: {audio_info.get('rms', 0):.4f}
- 最大振幅: {audio_info.get('max_amplitude', 0):.4f}

请提供JSON格式的分析结果，包括：
1. quality_score: 音频质量评分(0-100)
2. suitable_for_embedding: 是否适合嵌入(true/false)
3. recommended_method: 推荐的嵌入方法(dwt/dct/lsb/mixed)
4. capacity_estimate: 预估容量(字符数)
5. risk_factors: 风险因素列表

只返回JSON，不要其他内容。"""
        
        response = self.generate_response(prompt, temperature=0.3)
        
        try:
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
    
    def generate_embedding_report(self, embedding_result: Dict) -> str:
        prompt = f"""生成音频信息隐藏报告：

嵌入结果：
- 操作类型: {embedding_result.get('operation', 'unknown')}
- 输入文件: {embedding_result.get('input_file', 'unknown')}
- 输出文件: {embedding_result.get('output_file', 'unknown')}
- 消息长度: {embedding_result.get('message_length', 0)}字符
- 是否加密: {embedding_result.get('encrypted', False)}
- SNR: {embedding_result.get('metrics', {}).get('snr', 0):.2f}dB
- PSNR: {embedding_result.get('metrics', {}).get('psnr', 0):.2f}dB

请生成一份专业的信息隐藏报告，包括：
1. 操作概述
2. 技术指标分析
3. 安全性评估
4. 质量评估
5. 建议"""
        
        return self.generate_response(prompt, temperature=0.5)
    
    def _get_default_distribution(self, total_length: int) -> Dict:
        layer1 = total_length // 3
        layer2 = total_length // 3
        layer3 = total_length - layer1 - layer2
        
        return {
            "layer1_dwt": layer1,
            "layer2_dct": layer2,
            "layer3_lsb": layer3,
            "recommendation": "使用默认的三层平均分配策略"
        }


def download_model():
    print("=" * 50)
    print("下载Qwen2.5-0.5B-Instruct模型")
    print("=" * 50)
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        os.makedirs(MODEL_DIR, exist_ok=True)
        model_path = os.path.join(MODEL_DIR, "qwen2.5-0.5b-instruct")
        
        if os.path.exists(model_path):
            print(f"模型已存在于: {model_path}")
            return True
        
        print(f"正在从HuggingFace下载模型...")
        print(f"模型名称: {MODEL_NAME}")
        print(f"保存路径: {model_path}")
        
        print("\n[1/2] 下载Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True
        )
        tokenizer.save_pretrained(model_path)
        print("✓ Tokenizer下载完成")
        
        print("\n[2/2] 下载模型...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            torch_dtype=torch.float32
        )
        model.save_pretrained(model_path)
        print("✓ 模型下载完成")
        
        print(f"\n模型已成功保存到: {model_path}")
        return True
        
    except ImportError as e:
        print(f"错误: 缺少必要的库 - {e}")
        print("请运行: pip install transformers torch")
        return False
    except Exception as e:
        print(f"下载失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="本地Qwen模型管理")
    parser.add_argument("--download", action="store_true", help="下载模型到本地")
    parser.add_argument("--test", action="store_true", help="测试模型")
    args = parser.parse_args()
    
    if args.download:
        download_model()
    elif args.test:
        print("测试本地模型...")
        model = LocalQwenIntegration()
        if model.check_model_availability():
            print("✓ 模型可用")
            response = model.generate_response("你好，请简单介绍一下你自己。")
            print(f"响应: {response}")
        else:
            print("✗ 模型不可用")
    else:
        parser.print_help()
