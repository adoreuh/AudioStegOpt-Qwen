import requests
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

GGUF_MODEL_AVAILABLE = False
LOCAL_MODEL_AVAILABLE = False

try:
    from .gguf_qwen import QwenLocalIntegration as GGUFIntegration
    GGUF_MODEL_AVAILABLE = True
except ImportError:
    logger.debug("GGUF模型模块不可用")

try:
    from .local_qwen import LocalQwenIntegration
    LOCAL_MODEL_AVAILABLE = True
except ImportError:
    logger.debug("本地transformers模型模块不可用")


class QwenModelIntegration:
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url
        self.model_name = "qwen3:0.6b"
        self.api_endpoint = f"{base_url}/api/generate"
        self.api_chat_endpoint = f"{base_url}/api/chat"
        
        self._gguf_model = None
        self._local_model = None
        self._use_gguf = False
        self._use_local = False
        self._ollama_available = False
        
        self._initialize_model()

    def _initialize_model(self):
        if GGUF_MODEL_AVAILABLE:
            try:
                self._gguf_model = GGUFIntegration()
                if self._gguf_model.check_model_availability():
                    self._use_gguf = True
                    logger.info("使用GGUF Qwen3:0.6b模型（直接加载）")
                    return
            except Exception as e:
                logger.warning(f"GGUF模型初始化失败: {e}")
        
        if LOCAL_MODEL_AVAILABLE:
            try:
                self._local_model = LocalQwenIntegration()
                if self._local_model.check_model_availability():
                    self._use_local = True
                    logger.info("使用本地transformers Qwen模型")
                    return
            except Exception as e:
                logger.warning(f"本地transformers模型初始化失败: {e}")
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if self.model_name in model_names:
                    self._ollama_available = True
                    logger.info("使用Ollama Qwen模型服务")
        except Exception:
            pass

    def generate_response(self, prompt: str, temperature: float = 0.7, 
                         max_tokens: int = 500) -> str:
        if self._use_gguf and self._gguf_model:
            return self._gguf_model.generate_response(prompt, temperature, max_tokens)
        
        if self._use_local and self._local_model:
            return self._local_model.generate_response(prompt, temperature, max_tokens)
        
        if self._ollama_available:
            return self._ollama_generate(prompt, temperature, max_tokens)
        
        return self._get_fallback_response(prompt)

    def _ollama_generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(self.api_endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama生成失败: {str(e)}")
            return ""

    def _get_fallback_response(self, prompt: str) -> str:
        if "优化嵌入参数" in prompt or "layer" in prompt.lower():
            return '{"layer1_dwt": 33, "layer2_dct": 33, "layer3_lsb": 34, "recommendation": "使用默认的三层平均分配策略"}'
        elif "质量" in prompt or "quality" in prompt.lower():
            return '{"quality_score": 75, "suitable_for_embedding": true, "recommended_method": "dwt", "capacity_estimate": 1000, "risk_factors": []}'
        return ""

    def chat_completion(self, messages: list, temperature: float = 0.7,
                       max_tokens: int = 500) -> str:
        if self._use_gguf and self._gguf_model:
            return self._gguf_model.chat_completion(messages, temperature, max_tokens)
        
        if self._use_local and self._local_model:
            return self._local_model.chat_completion(messages, temperature, max_tokens)
        
        if self._ollama_available:
            try:
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                
                response = requests.post(self.api_chat_endpoint, json=payload, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                return result.get("message", {}).get("content", "")
                
            except Exception as e:
                logger.error(f"Ollama聊天失败: {str(e)}")
        
        return ""

    def optimize_embedding_parameters(self, audio_info: Dict, message_length: int) -> Dict:
        prompt = f"""
作为音频信息隐藏专家，请根据以下信息优化嵌入参数：

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
只返回JSON，不要其他内容。
"""
        
        response = self.generate_response(prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析优化响应失败: {str(e)}")
        
        return self._get_default_distribution(message_length)

    def analyze_audio_quality(self, audio_info: Dict) -> Dict:
        prompt = f"""
分析音频质量并给出信息隐藏建议：

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

只返回JSON，不要其他内容。
"""
        
        response = self.generate_response(prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析质量分析失败: {str(e)}")
        
        return {
            "quality_score": 75,
            "suitable_for_embedding": True,
            "recommended_method": "dwt",
            "capacity_estimate": 1000,
            "risk_factors": []
        }

    def generate_embedding_report(self, embedding_result: Dict) -> str:
        prompt = f"""
生成音频信息隐藏报告：

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
5. 建议
"""
        
        return self.generate_response(prompt, temperature=0.5)

    def check_model_availability(self) -> bool:
        if self._use_gguf and self._gguf_model:
            return True
        
        if self._use_local and self._local_model:
            return True
        
        if self._ollama_available:
            return True
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            return self.model_name in model_names
            
        except Exception as e:
            logger.debug(f"检查模型可用性失败: {str(e)}")
            return False

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
