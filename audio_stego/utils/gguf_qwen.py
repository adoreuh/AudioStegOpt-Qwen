import os
import json
import logging
import shutil
import time
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# 模型配置
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "qwen3-0.6b.gguf")

# 性能优化参数 - 针对音频隐写任务调优
MODEL_PARAMS = {
    "n_ctx": 1024,          # 上下文长度降至1024，节省内存
    "n_batch": 256,         # 批处理大小降至256
    "n_threads": None,      # 自动检测CPU核心数
    "n_gpu_layers": 0,      # CPU模式，如需GPU可调整
    "verbose": False,       # 关闭详细日志
    "use_mmap": True,       # 使用内存映射加速加载
    "use_mlock": False,     # 不锁定内存
    "seed": -1,             # 随机种子
    "f16_kv": True,         # 使用FP16存储KV缓存
}

# Qwen模型对话模板
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

# 生成参数 - 针对音频隐写任务优化
GENERATION_PARAMS = {
    "repeat_penalty": 1.1,   # 增加重复惩罚
    "stop": ["<|im_start|>", "<|im_end|>", "\n\n"],
    "temperature": 0.3,      # 降低温度提高确定性
    "top_k": 10,             # 降低top_k
    "top_p": 0.9,            # 降低top_p
    "frequency_penalty": 0.1,
    "presence_penalty": 0.0
}


class QwenGGUFModel:
    """Qwen3:0.6b GGUF模型管理器 - 高性能本地推理"""
    
    _instance = None
    _model = None
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
    
    def _get_optimal_threads(self) -> int:
        """获取最优线程数"""
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        # 保留一个核心给系统，其余用于推理
        return max(1, cpu_count - 1)
    
    def _find_model_path(self) -> Optional[str]:
        """查找模型文件路径"""
        # 优先查找项目目录下的模型
        if os.path.exists(DEFAULT_MODEL_PATH):
            logger.info(f"找到项目内模型: {DEFAULT_MODEL_PATH}")
            return DEFAULT_MODEL_PATH
        
        # 查找MODEL_DIR下的任何.gguf文件
        if os.path.exists(MODEL_DIR):
            gguf_files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.gguf')]
            if gguf_files:
                model_path = os.path.join(MODEL_DIR, gguf_files[0])
                logger.info(f"找到模型文件: {model_path}")
                return model_path
        
        logger.warning("未找到模型文件")
        return None
    
    def _initialize_model(self):
        """初始化模型 - 优化加载性能"""
        start_time = time.time()
        
        try:
            logger.info("正在初始化Qwen3:0.6b GGUF模型...")
            
            from llama_cpp import Llama
            
            model_path = self._find_model_path()
            
            if model_path is None:
                logger.warning("模型文件不存在，请确保模型已放置在正确位置")
                logger.info(f"期望路径: {DEFAULT_MODEL_PATH}")
                self._initialized = False
                return
            
            self._model_path = model_path
            file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
            logger.info(f"模型路径: {model_path}")
            logger.info(f"模型大小: {file_size_mb:.1f} MB")
            
            # 自动检测最优线程数
            n_threads = MODEL_PARAMS["n_threads"] or self._get_optimal_threads()
            logger.info(f"使用线程数: {n_threads}")
            
            # 使用内存映射加速大模型加载
            self._model = Llama(
                model_path=model_path,
                n_ctx=MODEL_PARAMS["n_ctx"],
                n_batch=MODEL_PARAMS["n_batch"],
                n_threads=n_threads,
                n_gpu_layers=MODEL_PARAMS["n_gpu_layers"],
                verbose=MODEL_PARAMS["verbose"],
                use_mmap=MODEL_PARAMS["use_mmap"],
                use_mlock=MODEL_PARAMS["use_mlock"]
            )
            
            self._initialized = True
            self._load_time = time.time() - start_time
            logger.info(f"✓ 模型初始化完成，加载耗时: {self._load_time:.2f}秒")
            
        except ImportError as e:
            logger.warning(f"llama-cpp-python库未安装: {e}")
            logger.info("请运行: pip install llama-cpp-python")
            self._initialized = False
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self._initialized and self._model is not None
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        if not self.is_available():
            return {"status": "未加载"}
        
        return {
            "status": "已加载",
            "model_path": self._model_path,
            "load_time": f"{self._load_time:.2f}s",
            "context_length": MODEL_PARAMS["n_ctx"],
            "batch_size": MODEL_PARAMS["n_batch"],
            "threads": self._get_optimal_threads()
        }
    
    def format_chat_prompt(self, messages: List[Dict], system: str = None) -> str:
        """格式化对话提示词"""
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
    
    def generate(self, prompt: str, max_tokens: int = 500, 
                 temperature: float = 0.6, stop_sequences: List[str] = None) -> str:
        """生成文本 - 优化推理性能"""
        if not self.is_available():
            return ""
        
        try:
            start_time = time.time()
            
            # 合并停止序列
            stop = GENERATION_PARAMS["stop"]
            if stop_sequences:
                stop = stop + stop_sequences
            
            response = self._model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=GENERATION_PARAMS["top_p"],
                top_k=GENERATION_PARAMS["top_k"],
                repeat_penalty=GENERATION_PARAMS["repeat_penalty"],
                stop=stop
            )
            
            inference_time = time.time() - start_time
            generated_text = response["choices"][0]["text"].strip()
            
            logger.debug(f"推理耗时: {inference_time:.2f}s, 生成长度: {len(generated_text)}字符")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            return ""
    
    def chat(self, messages: List[Dict], system: str = None, 
             max_tokens: int = 500, temperature: float = 0.6) -> str:
        """对话接口"""
        if not self.is_available():
            return ""
        
        prompt = self.format_chat_prompt(messages, system)
        return self.generate(prompt, max_tokens, temperature)
    
    def unload(self):
        """卸载模型释放内存"""
        if self._model is not None:
            del self._model
            self._model = None
            self._initialized = False
            logger.info("模型已卸载，内存已释放")


class QwenLocalIntegration:
    """Qwen本地模型集成接口"""
    
    def __init__(self):
        self.model = QwenGGUFModel()
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
        
        messages = [{"role": "user", "content": prompt}]
        system = "你是一个专业的音频信息隐藏专家，擅长分析和优化音频隐写参数。"
        
        return self.model.chat(messages, system, max_tokens, temperature)
    
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7,
                       max_tokens: int = 500) -> str:
        """聊天补全"""
        if not self._initialized:
            return ""
        
        return self.model.chat(messages, max_tokens=max_tokens, temperature=temperature)
    
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


def setup_model(source_path: str = None) -> bool:
    """设置模型文件
    
    Args:
        source_path: 模型文件源路径，如果为None则提示用户输入
    
    Returns:
        bool: 是否设置成功
    """
    print("=" * 60)
    print("Qwen3:0.6b模型设置")
    print("=" * 60)
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    dest_path = DEFAULT_MODEL_PATH
    
    if source_path is None:
        print(f"\n请将模型文件放置在以下位置:")
        print(f"  {dest_path}")
        print(f"\n或者运行以下命令指定模型路径:")
        print(f"  python -m audio_stego.utils.gguf_qwen --setup <模型路径>")
        return False
    
    if not os.path.exists(source_path):
        print(f"错误: 源文件不存在: {source_path}")
        return False
    
    if os.path.exists(dest_path):
        print(f"模型文件已存在: {dest_path}")
        return True
    
    print(f"\n正在复制模型文件...")
    print(f"源路径: {source_path}")
    print(f"目标路径: {dest_path}")
    print(f"文件大小: {os.path.getsize(source_path) / (1024*1024):.1f} MB")
    
    try:
        shutil.copy2(source_path, dest_path)
        print("✓ 模型复制完成")
        return True
    except Exception as e:
        print(f"复制失败: {e}")
        return False


def test_model():
    """测试模型"""
    print("=" * 60)
    print("测试Qwen3:0.6b GGUF模型")
    print("=" * 60)
    
    model = QwenLocalIntegration()
    
    if not model.check_model_availability():
        print("✗ 模型不可用")
        print(f"\n请确保模型文件存在于: {DEFAULT_MODEL_PATH}")
        return False
    
    print("✓ 模型已加载")
    
    # 显示模型信息
    info = model.get_model_info()
    print(f"\n模型信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # 测试生成
    print("\n测试文本生成...")
    test_prompts = [
        "你好，请简单介绍一下你自己。",
        "1+1等于几？",
    ]
    
    for prompt in test_prompts:
        print(f"\n提示: {prompt}")
        response = model.generate_response(prompt, temperature=0.7, max_tokens=100)
        print(f"响应: {response}")
    
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Qwen3:0.6b GGUF模型管理工具")
    parser.add_argument("--setup", metavar="PATH", help="设置模型文件路径")
    parser.add_argument("--test", action="store_true", help="测试模型")
    parser.add_argument("--info", action="store_true", help="显示模型信息")
    args = parser.parse_args()
    
    if args.setup:
        setup_model(args.setup)
    elif args.test:
        test_model()
    elif args.info:
        model = QwenLocalIntegration()
        info = model.get_model_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
