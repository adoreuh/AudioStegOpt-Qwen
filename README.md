# 音频信息隐藏系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**基于DWT小波变换的音频信息隐藏系统，集成Qwen3:0.6b大语言模型进行智能优化**

</div>

---

## 项目简介

本项目是一个基于离散小波变换(DWT)的音频信息隐藏系统，支持将秘密信息嵌入到音频文件中，并能够完整提取。系统集成Qwen3:0.6b大语言模型，提供智能参数优化功能。

**核心特性：**
- 🔒 **DWT隐写算法**：使用Haar小波进行3级分解，高鲁棒性
- 🤖 **AI智能优化**：本地加载GGUF模型，无需外部服务
- 📁 **多格式支持**：WAV、MP3、FLAC
- 📊 **质量评估**：SNR/PSNR音频质量指标
- 🌐 **Web界面**：直观的可视化操作界面
- 🔌 **REST API**：完整的API接口支持

## 快速开始

### 环境要求
- Python 3.8+
- 4GB+ 内存
- (可选) CUDA支持用于GPU加速

### 安装步骤

```bash
# 1. 克隆项目
git clone <仓库地址>
cd Mamba

# 2. 安装依赖
pip install -r audio_stego/requirements.txt

# 3. 启动服务
cd audio_stego
python api/app.py

# 4. 访问Web界面
# http://localhost:5000
```

### 一键启动

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

## 模型配置

### 方式1: 使用Ollama模型（推荐）

```bash
ollama pull qwen3:0.6b
```

配置模型路径（`audio_stego/utils/gguf_qwen.py`）:
```python
OLLAMA_MODEL_PATH = r"D:\models\blobs\sha256-..."
```

### 方式2: 本地模型文件

```bash
cd audio_stego
python -m utils.gguf_qwen --copy
```

### 方式3: 无模型运行

系统支持无模型回退模式，使用预设算法进行参数优化。

## 使用指南

### 嵌入信息
1. 选择"嵌入模式"
2. 上传载体音频文件
3. 输入要隐藏的秘密信息
4. 可选：设置加密密钥
5. 可选：启用AI智能优化
6. 点击"开始嵌入"
7. 下载含密音频

### 提取信息
1. 选择"提取模式"
2. 上传含密音频文件
3. 可选：输入解密密钥
4. 点击"开始提取"
5. 查看提取出的信息

## API接口

```http
# 健康检查
GET /api/health

# 嵌入信息
POST /api/embed
Content-Type: multipart/form-data
参数: audio, message, encryption_key(可选)

# 提取信息
POST /api/extract
Content-Type: multipart/form-data
参数: audio, encryption_key(可选)

# 获取容量
POST /api/capacity
参数: audio

# AI优化
POST /api/ai/optimize
参数: audio, message
```

## 项目结构

```
audio_stego/
├── api/              # API服务层
│   └── app.py       # Flask应用
├── core/             # 核心算法层
│   ├── improved_stego.py    # DWT隐写算法
│   ├── audio_processor.py   # 音频处理
│   ├── mamba_stego.py       # Mamba模块(可选)
│   └── ...
├── frontend/         # 前端界面
│   └── templates/
│       └── index.html
├── utils/            # 工具模块
│   ├── gguf_qwen.py         # GGUF模型加载
│   └── qwen_integration.py  # AI集成接口
├── docs/             # 文档
│   ├── FAQ.md
│   └── API.md
├── tests/            # 测试文件
└── requirements.txt
```

## 技术细节

### DWT隐写算法

1. **分解**：使用Haar小波进行3级分解
2. **嵌入**：在近似系数(cA3)中修改符号位
   - bit=1: 正值
   - bit=0: 负值
3. **重构**：逆小波变换生成隐写音频

### 容量计算

```
容量 = (音频长度 / 2^分解层数) / 8

示例: 60秒音频, 44100Hz
容量 = (60 × 44100 / 8) / 8 ≈ 41,343 字节
```

### 性能指标

| 指标 | 说明 | 典型值 |
|------|------|--------|
| SNR | 信噪比 | 20-40 dB |
| PSNR | 峰值信噪比 | 20-40 dB |
| 准确率 | 提取准确率 | 100% |

## 依赖包

```
flask>=3.0.0
flask-cors>=4.0.0
numpy>=1.26.3
scipy>=1.15.0
pydub>=0.25.1
librosa>=0.10.1
soundfile>=0.12.1
PyWavelets>=1.6.0
llama-cpp-python>=0.2.50
```

## 故障排除

### 模型加载失败
```
检查模型文件路径是否正确
确保llama-cpp-python已安装
```

### 音频加载失败
```
检查文件格式是否支持
安装ffmpeg: winget install ffmpeg
```

### 端口被占用
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### 依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 开发计划

- [x] DWT隐写算法
- [x] 本地GGUF模型支持
- [x] Web界面
- [ ] GPU加速支持
- [ ] 批量处理
- [ ] 移动端适配

## 许可证

MIT License

## 致谢

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - GGUF模型推理
- [Qwen](https://github.com/QwenLM/Qwen) - 大语言模型
- [PyWavelets](https://pywavelets.readthedocs.io/) - 小波变换库
