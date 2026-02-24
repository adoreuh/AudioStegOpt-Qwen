# 常见问题解答 (FAQ)

## 安装与配置

### Q1: 系统支持哪些操作系统?
**A**: 支持 Windows、Linux 和 macOS。推荐使用 Windows 10/11 或 Ubuntu 20.04+。

### Q2: Python版本要求是什么?
**A**: Python 3.8 或更高版本。推荐使用 Python 3.10 或 3.11。

### Q3: 如何安装依赖?
```bash
pip install -r audio_stego/requirements.txt
```

如果安装缓慢，可以使用国内镜像：
```bash
pip install -r audio_stego/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q4: llama-cpp-python安装失败怎么办?
**A**: Windows用户可以使用预编译包：
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

如有NVIDIA GPU，可安装CUDA版本：
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

---

## 模型相关

### Q5: 必须要有Qwen模型吗?
**A**: 不是必须的。系统支持三种模式：
1. **GGUF模型模式**: 直接加载本地模型文件
2. **Ollama服务模式**: 通过Ollama API调用模型
3. **回退模式**: 无模型时使用预设算法

### Q6: 如何配置模型路径?
**A**: 编辑 `audio_stego/utils/gguf_qwen.py` 文件：
```python
OLLAMA_MODEL_PATH = r"D:\models\blobs\sha256-..."
```

### Q7: 模型加载很慢怎么办?
**A**: 
- 首次加载需要初始化，约5-10秒
- 使用GPU加速可提升加载速度
- 减小 `n_ctx` 参数可减少内存占用

### Q8: 支持哪些模型?
**A**: 支持所有GGUF格式的模型：
- Qwen系列 (推荐 qwen3:0.6b)
- Llama系列
- 其他llama.cpp兼容模型

---

## 音频处理

### Q9: 支持哪些音频格式?
**A**: 
- WAV (推荐)
- MP3
- FLAC
- OGG
- AAC

### Q10: 音频文件大小限制?
**A**: 默认限制50MB。可在 `app.py` 中修改：
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

### Q11: MP3文件加载失败?
**A**: 需要安装ffmpeg：
```bash
# Windows
winget install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### Q12: 如何计算嵌入容量?
**A**: 容量计算公式：
```
容量(字节) = (音频采样点数 / 8) / 8
```

示例：
- 10秒音频 (44.1kHz): ~6.7 KB
- 60秒音频 (44.1kHz): ~40 KB
- 180秒音频 (44.1kHz): ~121 KB

---

## 隐写功能

### Q13: 嵌入后音质会下降吗?
**A**: 会有轻微影响，但通常不可察觉：
- SNR通常在20-40 dB
- 人耳难以分辨差异
- 消息越长，影响越大

### Q14: 提取信息失败怎么办?
**A**: 检查以下事项：
1. 确认是隐写音频文件
2. 检查是否使用了正确的密钥
3. 确认音频未被修改或压缩
4. 查看embedding_info是否正确

### Q15: 支持中文消息吗?
**A**: 支持。系统使用UTF-8编码，支持中文、英文、特殊字符等。

### Q16: 加密功能安全吗?
**A**: 使用SHA-256密钥进行XOR加密，适合一般安全需求。如需更高安全性，建议先加密消息再嵌入。

---

## 系统运行

### Q17: 端口5000被占用怎么办?
**A**: 
```bash
# Windows - 查找并终止进程
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F

# 或修改app.py中的端口
app.run(host='0.0.0.0', port=5001)
```

### Q18: 服务启动后无法访问?
**A**: 检查：
1. 防火墙是否放行端口
2. 服务是否正常启动
3. 访问地址是否正确 (http://localhost:5000)

### Q19: 内存占用过高?
**A**: 
- 模型加载需要约500MB内存
- 处理大文件时内存会增加
- 可减小 `n_ctx` 参数降低内存占用

### Q20: 如何查看日志?
**A**: 日志会输出到控制台。可调整日志级别：
```python
logging.basicConfig(level=logging.DEBUG)
```

---

## 性能优化

### Q21: 如何提升推理速度?
**A**: 
1. 使用GPU加速 (安装CUDA版本的llama-cpp-python)
2. 减小 `max_tokens` 参数
3. 使用更小的模型

### Q22: 如何处理大音频文件?
**A**: 
- 系统会自动处理，但可能需要更多时间
- 建议文件大小控制在50MB以内
- 可实现分块处理（需自行开发）

### Q23: 支持批量处理吗?
**A**: 当前版本不支持批量处理，可通过API自行实现：
```python
import requests

files = ['audio1.mp3', 'audio2.mp3', 'audio3.mp3']
for f in files:
    with open(f, 'rb') as audio:
        response = requests.post(
            'http://localhost:5000/api/embed',
            files={'audio': audio},
            data={'message': 'secret message'}
        )
```

---

## 开发相关

### Q24: 如何扩展API功能?
**A**: 在 `audio_stego/api/app.py` 中添加新的路由：
```python
@app.route('/api/custom', methods=['POST'])
def custom_function():
    # 自定义逻辑
    return jsonify({'success': True})
```

### Q25: 如何修改前端界面?
**A**: 编辑 `audio_stego/frontend/templates/index.html` 文件。

### Q26: 如何添加新的音频格式支持?
**A**: 在 `audio_stego/core/audio_processor.py` 中添加加载方法：
```python
SUPPORTED_FORMATS = ['.wav', '.mp3', '.flac', '.ogg', '.aac', '.new_format']

def _load_new_format(self, file_path):
    # 实现加载逻辑
    pass
```

---

## 故障排除

### Q27: 启动时提示模块找不到?
**A**: 
```bash
# 确保在正确目录
cd audio_stego

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### Q28: 音频处理报错?
**A**: 常见原因：
1. 文件损坏 - 尝试其他文件
2. 格式不支持 - 转换为WAV格式
3. 内存不足 - 使用更小的文件

### Q29: AI优化无响应?
**A**: 
1. 检查模型是否正确加载
2. 查看控制台错误信息
3. 尝试使用回退模式

### Q30: 如何重置系统?
**A**: 
```bash
# 清除缓存
rm -rf audio_stego/__pycache__
rm -rf audio_stego/*/__pycache__

# 清除输出文件
rm -rf audio_stego/outputs/*
rm -rf audio_stego/uploads/*
```

---

## 联系支持

如有其他问题，请：
1. 查看项目README.md
2. 查看技术文档 TECHNICAL_DOCUMENTATION.md
3. 提交Issue到项目仓库
