# 音频信息隐藏系统 | Audio Steganography System

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**基于DWT小波变换的音频信息隐藏系统，集成Qwen3:0.6b大语言模型进行智能优化**

**Audio Steganography System based on DWT Wavelet Transform with Qwen3:0.6b LLM Integration**

[中文](#中文文档) | [English](#english-documentation)

</div>

---

<a name="中文文档"></a>
## 中文文档

### 项目简介

本项目是一个基于离散小波变换(DWT)的音频信息隐藏系统，支持将秘密信息嵌入到音频文件中，并能够完整提取。系统集成Qwen3:0.6b大语言模型，提供智能参数优化功能。

**核心特性：**
- 🔒 **DWT隐写算法**：使用Haar小波进行3级分解，高鲁棒性
- 🤖 **AI智能优化**：本地加载GGUF模型，无需外部服务
- 📁 **多格式支持**：WAV、MP3、FLAC、OGG、AAC
- 🔐 **可选加密**：SHA-256密钥加密保护
- 📊 **质量评估**：SNR/PSNR音频质量指标
- 🌐 **Web界面**：直观的可视化操作界面
- 🔌 **REST API**：完整的API接口支持

### 快速开始

#### 环境要求
- Python 3.8+
- 4GB+ 内存
- (可选) CUDA支持用于GPU加速

#### 安装步骤

```bash
# 1. 克隆项目
# Clone the repository
git clone <repository-url>
cd Mamba

# 2. 安装依赖
# Install dependencies
pip install -r audio_stego/requirements.txt

# 3. 启动服务
# Start the service
cd audio_stego
python api/app.py

# 4. 访问Web界面
# Access the web interface
# http://localhost:5000
```

#### 一键启动

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 模型配置

#### 方式1: 使用Ollama模型（推荐）

```bash
ollama pull qwen3:0.6b
```

配置模型路径（`audio_stego/utils/gguf_qwen.py`）:
```python
OLLAMA_MODEL_PATH = r"D:\models\blobs\sha256-..."
```

#### 方式2: 本地模型文件

```bash
cd audio_stego
python -m utils.gguf_qwen --copy
```

#### 方式3: 无模型运行

系统支持无模型回退模式，使用预设算法进行参数优化。

### 使用指南

#### 嵌入信息
1. 选择"嵌入模式"
2. 上传载体音频文件
3. 输入要隐藏的秘密信息
4. 可选：设置加密密钥
5. 可选：启用AI智能优化
6. 点击"开始嵌入"
7. 下载含密音频

#### 提取信息
1. 选择"提取模式"
2. 上传含密音频文件
3. 可选：输入解密密钥
4. 点击"开始提取"
5. 查看提取出的信息

### API接口

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

### 项目结构

```
audio_stego/
├── api/              # API服务层
├── core/             # 核心算法层
├── frontend/         # 前端界面
├── utils/            # 工具模块
├── docs/             # 文档
└── tests/            # 测试文件
```

### 技术细节

#### DWT隐写算法
1. **分解**：使用Haar小波进行3级分解
2. **嵌入**：在近似系数(cA3)中修改符号位
   - bit=1: 正值
   - bit=0: 负值
3. **重构**：逆小波变换生成隐写音频

#### 容量计算
```
容量 = (音频长度 / 2^分解层数) / 8

示例: 60秒音频, 44100Hz
容量 = (60 × 44100 / 8) / 8 ≈ 41,343 字节
```

### 故障排除

| 问题 | 解决方案 |
|------|----------|
| 模型加载失败 | 检查模型路径，确保llama-cpp-python已安装 |
| 音频加载失败 | 安装ffmpeg: `winget install ffmpeg` |
| 端口被占用 | `netstat -ano \| findstr :5000` 然后终止进程 |

### 许可证

MIT License

---

<a name="english-documentation"></a>
## English Documentation

### Project Overview

This project is an audio steganography system based on Discrete Wavelet Transform (DWT), supporting embedding secret messages into audio files and complete extraction. The system integrates the Qwen3:0.6b large language model for intelligent parameter optimization.

**Key Features:**
- 🔒 **DWT Steganography**: 3-level Haar wavelet decomposition, high robustness
- 🤖 **AI Optimization**: Local GGUF model loading, no external services required
- 📁 **Multi-format Support**: WAV, MP3, FLAC, OGG, AAC
- 🔐 **Optional Encryption**: SHA-256 key encryption protection
- 📊 **Quality Assessment**: SNR/PSNR audio quality metrics
- 🌐 **Web Interface**: Intuitive visual operation interface
- 🔌 **REST API**: Complete API interface support

### Quick Start

#### Requirements
- Python 3.8+
- 4GB+ RAM
- (Optional) CUDA support for GPU acceleration

#### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd Mamba

# 2. Install dependencies
pip install -r audio_stego/requirements.txt

# 3. Start the service
cd audio_stego
python api/app.py

# 4. Access the web interface
# http://localhost:5000
```

#### One-Click Start

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### Model Configuration

#### Method 1: Using Ollama Model (Recommended)

```bash
ollama pull qwen3:0.6b
```

Configure model path (`audio_stego/utils/gguf_qwen.py`):
```python
OLLAMA_MODEL_PATH = r"D:\models\blobs\sha256-..."
```

#### Method 2: Local Model File

```bash
cd audio_stego
python -m utils.gguf_qwen --copy
```

#### Method 3: Run Without Model

The system supports fallback mode without model, using preset algorithms for parameter optimization.

### Usage Guide

#### Embedding Messages
1. Select "Embed Mode"
2. Upload carrier audio file
3. Enter secret message to hide
4. Optional: Set encryption key
5. Optional: Enable AI optimization
6. Click "Start Embedding"
7. Download stego audio

#### Extracting Messages
1. Select "Extract Mode"
2. Upload stego audio file
3. Optional: Enter decryption key
4. Click "Start Extraction"
5. View extracted message

### API Reference

```http
# Health Check
GET /api/health

# Embed Message
POST /api/embed
Content-Type: multipart/form-data
Parameters: audio, message, encryption_key(optional)

# Extract Message
POST /api/extract
Content-Type: multipart/form-data
Parameters: audio, encryption_key(optional)

# Get Capacity
POST /api/capacity
Parameters: audio

# AI Optimization
POST /api/ai/optimize
Parameters: audio, message
```

### Project Structure

```
audio_stego/
├── api/              # API service layer
├── core/             # Core algorithm layer
├── frontend/         # Frontend interface
├── utils/            # Utility modules
├── docs/             # Documentation
└── tests/            # Test files
```

### Technical Details

#### DWT Steganography Algorithm
1. **Decomposition**: 3-level Haar wavelet decomposition
2. **Embedding**: Modify sign bits in approximation coefficients (cA3)
   - bit=1: positive value
   - bit=0: negative value
3. **Reconstruction**: Inverse wavelet transform to generate stego audio

#### Capacity Calculation
```
Capacity = (Audio Length / 2^Decomposition Level) / 8

Example: 60 seconds audio, 44100Hz
Capacity = (60 × 44100 / 8) / 8 ≈ 41,343 bytes
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Model loading failed | Check model path, ensure llama-cpp-python is installed |
| Audio loading failed | Install ffmpeg: `winget install ffmpeg` |
| Port occupied | `netstat -ano \| findstr :5000` then kill process |

### License

MIT License

---

## Acknowledgments | 致谢

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - GGUF model inference
- [Qwen](https://github.com/QwenLM/Qwen) - Large language model
- [PyWavelets](https://pywavelets.readthedocs.io/) - Wavelet transform library