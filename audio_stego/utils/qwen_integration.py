import json
import logging
import hashlib
import time
from typing import Dict, Optional, List
from functools import lru_cache

logger = logging.getLogger(__name__)

GGUF_MODEL_AVAILABLE = False
HF_MODEL_AVAILABLE = False

# 尝试导入GGUF模型模块
try:
    from .gguf_qwen import QwenLocalIntegration as GGUFIntegration
    GGUF_MODEL_AVAILABLE = True
except ImportError:
    logger.debug("GGUF模型模块不可用")

# 尝试导入HuggingFace模型模块
try:
    from .hf_qwen import QwenHFIntegration as HFIntegration
    HF_MODEL_AVAILABLE = True
except ImportError:
    logger.debug("HuggingFace模型模块不可用")


class ResponseCache:
    """响应缓存管理器"""
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self._cache = {}
        self._max_size = max_size
        self._ttl = ttl
    
    def _generate_key(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """生成缓存键"""
        key_data = f"{prompt}:{temperature}:{max_tokens}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """获取缓存响应"""
        key = self._generate_key(prompt, temperature, max_tokens)
        if key in self._cache:
            timestamp, response = self._cache[key]
            if time.time() - timestamp < self._ttl:
                logger.debug(f"缓存命中: {key[:8]}...")
                return response
            else:
                del self._cache[key]
        return None
    
    def set(self, prompt: str, temperature: float, max_tokens: int, response: str):
        """设置缓存响应"""
        if len(self._cache) >= self._max_size:
            # 移除最旧的条目
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        
        key = self._generate_key(prompt, temperature, max_tokens)
        self._cache[key] = (time.time(), response)
        logger.debug(f"缓存已设置: {key[:8]}...")
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("响应缓存已清空")


class QwenModelIntegration:
    """Qwen模型集成管理器 - 支持多格式模型"""
    
    MODEL_TYPE_GGUF = "gguf"
    MODEL_TYPE_HF = "huggingface"
    MODEL_TYPE_FALLBACK = "fallback"
    
    def __init__(self):
        self.model_name = "qwen3:0.6b"
        self._model = None
        self._model_type = self.MODEL_TYPE_FALLBACK
        self._cache = ResponseCache(max_size=200, ttl=3600)  # 1小时TTL，增大缓存
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_latency_ms': 0
        }
        
        self._initialize_model()

    def _initialize_model(self):
        """初始化模型 - 按优先级尝试不同格式"""
        
        # 优先级1: HuggingFace格式 (直接从transformers加载)
        if HF_MODEL_AVAILABLE:
            try:
                logger.info("尝试加载HuggingFace格式模型...")
                hf_model = HFIntegration()
                if hf_model.check_model_availability():
                    self._model = hf_model
                    self._model_type = self.MODEL_TYPE_HF
                    logger.info("✓ HuggingFace格式模型已加载")
                    return
            except Exception as e:
                logger.warning(f"HuggingFace模型加载失败: {e}")
        
        # 优先级2: GGUF格式 (通过llama-cpp加载)
        if GGUF_MODEL_AVAILABLE:
            try:
                logger.info("尝试加载GGUF格式模型...")
                gguf_model = GGUFIntegration()
                if gguf_model.check_model_availability():
                    self._model = gguf_model
                    self._model_type = self.MODEL_TYPE_GGUF
                    logger.info("✓ GGUF格式模型已加载")
                    return
            except Exception as e:
                logger.warning(f"GGUF模型加载失败: {e}")
        
        # 回退模式
        logger.warning("所有模型格式均不可用，将使用算法回退模式")
        self._model_type = self.MODEL_TYPE_FALLBACK

    def generate_response(self, prompt: str, temperature: float = 0.7, 
                         max_tokens: int = 500) -> str:
        """生成文本响应 - 带缓存机制"""
        # 检查缓存
        cached_response = self._cache.get(prompt, temperature, max_tokens)
        if cached_response:
            self._stats['cache_hits'] += 1
            return cached_response
        
        self._stats['cache_misses'] += 1
        response = ""
        
        # 使用AI模型
        if self._model_type != self.MODEL_TYPE_FALLBACK and self._model:
            response = self._model.generate_response(prompt, temperature, max_tokens)
        
        # 如果模型未返回结果，使用回退响应
        if not response:
            response = self._get_fallback_response(prompt)
        
        # 缓存响应
        if response:
            self._cache.set(prompt, temperature, max_tokens, response)
        
        self._stats['total_requests'] += 1
        return response

    def _get_fallback_response(self, prompt: str) -> str:
        """获取回退响应（当模型不可用时）"""
        prompt_lower = prompt.lower()
        
        if "优化嵌入参数" in prompt or "layer" in prompt_lower:
            return '{"layer1_dwt": 33, "layer2_dct": 33, "layer3_lsb": 34, "recommendation": "使用默认的三层平均分配策略"}'
        elif "质量" in prompt or "quality" in prompt_lower:
            return '{"quality_score": 75, "suitable_for_embedding": true, "recommended_method": "dwt", "capacity_estimate": 1000, "risk_factors": []}'
        elif "报告" in prompt or "report" in prompt_lower:
            return "音频信息隐藏操作已完成。技术指标良好，SNR和PSNR值在可接受范围内。建议进行安全性测试。"
        return ""

    def chat_completion(self, messages: List[Dict], temperature: float = 0.7,
                       max_tokens: int = 500) -> str:
        """聊天补全接口"""
        if self._model_type != self.MODEL_TYPE_FALLBACK and self._model:
            return self._model.chat_completion(messages, temperature, max_tokens)
        return ""

    def optimize_embedding_parameters(self, audio_info: Dict, message_length: int) -> Dict:
        """优化嵌入参数"""
        # 使用AI模型
        if self._model_type != self.MODEL_TYPE_FALLBACK and self._model:
            try:
                return self._model.optimize_embedding_parameters(audio_info, message_length)
            except Exception as e:
                logger.error(f"AI优化失败，使用回退: {e}")
        
        # 回退到默认分配
        return self._get_default_distribution(message_length)

    def analyze_audio_quality(self, audio_info: Dict) -> Dict:
        """分析音频质量"""
        # 使用AI模型
        if self._model_type != self.MODEL_TYPE_FALLBACK and self._model:
            try:
                return self._model.analyze_audio_quality(audio_info)
            except Exception as e:
                logger.error(f"AI分析失败，使用回退: {e}")
        
        # 回退到默认分析
        return {
            "quality_score": 75,
            "suitable_for_embedding": True,
            "recommended_method": "dwt",
            "capacity_estimate": 1000,
            "risk_factors": []
        }

    def generate_embedding_report(self, embedding_result: Dict) -> str:
        """生成嵌入报告"""
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
5. 建议
"""
        
        return self.generate_response(prompt, temperature=0.5)

    def check_model_availability(self) -> bool:
        """检查模型是否可用"""
        return self._model_type != self.MODEL_TYPE_FALLBACK and self._model is not None

    def get_model_status(self) -> Dict:
        """获取模型状态信息"""
        status = {
            "model_name": self.model_name,
            "model_type": self._model_type,
            "is_loaded": self.check_model_availability(),
            "cache_size": len(self._cache._cache) if hasattr(self._cache, '_cache') else 0,
            "stats": self._stats
        }
        
        if self._model and hasattr(self._model, 'get_model_info'):
            status.update(self._model.get_model_info())
        
        return status

    def clear_cache(self):
        """清空响应缓存"""
        self._cache.clear()

    def _get_default_distribution(self, total_length: int) -> Dict:
        """获取默认分配策略"""
        layer1 = total_length // 3
        layer2 = total_length // 3
        layer3 = total_length - layer1 - layer2
        
        return {
            "layer1_dwt": layer1,
            "layer2_dct": layer2,
            "layer3_lsb": layer3,
            "recommendation": "使用默认的三层平均分配策略"
        }
