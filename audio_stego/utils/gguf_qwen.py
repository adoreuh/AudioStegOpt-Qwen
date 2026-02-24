import os
import sys
import json
import logging
import shutil
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
OLLAMA_MODEL_PATH = r"D:\models\blobs\sha256-7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa"

QWEN_TEMPLATE = """{{- if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end -}}
{{- range .Messages }}
{{- if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{ else if eq .Role "assistant" }}<|im_start|>assistant
{{ .Content }}<|im_end|>
{{ end -}}
{{- end }}<|im_start|>assistant
"""

QWEN_PARAMS = {
    "repeat_penalty": 1.0,
    "stop": ["<|im_start|>", "<|im_end|>"],
    "temperature": 0.6,
    "top_k": 20,
    "top_p": 0.95
}


class QwenGGUFModel:
    _instance = None
    _model = None
    _initialized = False
    _model_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_model()
    
    def _find_model_path(self) -> Optional[str]:
        local_model = os.path.join(MODEL_DIR, "qwen3-0.6b.gguf")
        if os.path.exists(local_model):
            return local_model
        
        if os.path.exists(OLLAMA_MODEL_PATH):
            return OLLAMA_MODEL_PATH
        
        return None
    
    def _initialize_model(self):
        try:
            logger.info("正在初始化Qwen3:0.6b GGUF模型...")
            
            from llama_cpp import Llama
            
            model_path = self._find_model_path()
            
            if model_path is None:
                logger.warning("未找到模型文件")
                logger.info(f"请确保模型文件存在于以下位置之一:")
                logger.info(f"  1. {os.path.join(MODEL_DIR, 'qwen3-0.6b.gguf')}")
                logger.info(f"  2. {OLLAMA_MODEL_PATH}")
                self._initialized = False
                return
            
            self._model_path = model_path
            logger.info(f"从路径加载模型: {model_path}")
            
            self._model = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_batch=512,
                n_threads=4,
                verbose=False
            )
            
            self._initialized = True
            logger.info("Qwen3:0.6b GGUF模型初始化完成")
            
        except ImportError as e:
            logger.warning(f"llama-cpp-python库未安装: {e}")
            logger.info("请运行: pip install llama-cpp-python")
            self._initialized = False
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        return self._initialized and self._model is not None
    
    def format_chat(self, messages: List[Dict], system: str = None) -> str:
        prompt = ""
        
        if system:
            prompt += f"<|im_start|>system\n{system}<|im_end|>\n"
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        
        prompt += "<|im_start|>assistant\n"
        
        return prompt
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.6) -> str:
        if not self.is_available():
            return ""
        
        try:
            response = self._model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=QWEN_PARAMS["top_p"],
                top_k=QWEN_PARAMS["top_k"],
                repeat_penalty=QWEN_PARAMS["repeat_penalty"],
                stop=QWEN_PARAMS["stop"]
            )
            
            return response["choices"][0]["text"].strip()
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            return ""
    
    def chat(self, messages: List[Dict], system: str = None, 
             max_tokens: int = 500, temperature: float = 0.6) -> str:
        if not self.is_available():
            return ""
        
        prompt = self.format_chat(messages, system)
        return self.generate(prompt, max_tokens, temperature)


class QwenLocalIntegration:
    def __init__(self):
        self.model = QwenGGUFModel()
        self._initialized = self.model.is_available()
    
    def check_model_availability(self) -> bool:
        return self.model.is_available()
    
    def generate_response(self, prompt: str, temperature: float = 0.7, 
                         max_tokens: int = 500) -> str:
        if not self._initialized:
            return ""
        
        messages = [{"role": "user", "content": prompt}]
        system = "你是一个专业的音频信息隐藏专家，擅长分析和优化音频隐写参数。"
        
        return self.model.chat(messages, system, max_tokens, temperature)
    
    def chat_completion(self, messages: list, temperature: float = 0.7,
                       max_tokens: int = 500) -> str:
        if not self._initialized:
            return ""
        
        return self.model.chat(messages, max_tokens=max_tokens, temperature=temperature)
    
    def optimize_embedding_parameters(self, audio_info: Dict, message_length: int) -> Dict:
        prompt = f"""请根据以下音频信息优化嵌入参数：

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
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析优化响应失败: {e}")
        
        return self._get_default_distribution(message_length)
    
    def analyze_audio_quality(self, audio_info: Dict) -> Dict:
        prompt = f"""分析音频质量：

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
        layer1 = total_length // 3
        layer2 = total_length // 3
        layer3 = total_length - layer1 - layer2
        
        return {
            "layer1_dwt": layer1,
            "layer2_dct": layer2,
            "layer3_lsb": layer3,
            "recommendation": "使用默认的三层平均分配策略"
        }


def copy_model_to_project():
    print("=" * 60)
    print("复制Qwen3:0.6b模型到项目目录")
    print("=" * 60)
    
    if not os.path.exists(OLLAMA_MODEL_PATH):
        print(f"错误: Ollama模型文件不存在: {OLLAMA_MODEL_PATH}")
        return False
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    dest_path = os.path.join(MODEL_DIR, "qwen3-0.6b.gguf")
    
    if os.path.exists(dest_path):
        print(f"模型文件已存在: {dest_path}")
        return True
    
    print(f"正在复制模型文件...")
    print(f"源路径: {OLLAMA_MODEL_PATH}")
    print(f"目标路径: {dest_path}")
    print(f"文件大小: {os.path.getsize(OLLAMA_MODEL_PATH) / (1024*1024):.1f} MB")
    
    try:
        shutil.copy2(OLLAMA_MODEL_PATH, dest_path)
        print("✓ 模型复制完成")
        return True
    except Exception as e:
        print(f"复制失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Qwen3:0.6b GGUF模型管理")
    parser.add_argument("--copy", action="store_true", help="复制模型到项目目录")
    parser.add_argument("--test", action="store_true", help="测试模型")
    args = parser.parse_args()
    
    if args.copy:
        copy_model_to_project()
    elif args.test:
        print("测试Qwen3:0.6b GGUF模型...")
        model = QwenLocalIntegration()
        if model.check_model_availability():
            print("✓ 模型可用")
            response = model.generate_response("你好，请简单介绍一下你自己。")
            print(f"响应: {response}")
        else:
            print("✗ 模型不可用")
            print("提示: 运行 'python -m audio_stego.utils.gguf_qwen --copy' 复制模型")
    else:
        parser.print_help()
