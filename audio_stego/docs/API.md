# API 接口文档

## 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `multipart/form-data` (文件上传)
- **响应格式**: JSON

---

## 接口列表

### 1. 健康检查

检查系统状态和模型可用性。

**请求**
```http
GET /api/health
```

**响应**
```json
{
  "success": true,
  "status": "healthy",
  "ai_model_available": true,
  "version": "1.0.0"
}
```

---

### 2. 嵌入信息

将秘密信息嵌入到音频文件中。

**请求**
```http
POST /api/embed
Content-Type: multipart/form-data

参数:
- audio: 音频文件 (必需)
- message: 要嵌入的信息 (必需)
- encryption_key: 加密密钥 (可选)
```

**响应**
```json
{
  "success": true,
  "output_file": "stego_xxx.wav",
  "download_url": "/api/download/stego_xxx.wav",
  "message_length": 100,
  "metrics": {
    "snr": 32.5,
    "psnr": 32.5,
    "capacity": 41343,
    "embedding_info": {
      "data_length": 100,
      "encrypted": false,
      "method": "dwt_haar_level3",
      "audio_length": 2646000
    }
  }
}
```

**错误响应**
```json
{
  "success": false,
  "error": "消息长度超出容量: 需要 50000 字节, 最大容量约 41343 字节"
}
```

---

### 3. 提取信息

从隐写音频中提取秘密信息。

**请求**
```http
POST /api/extract
Content-Type: multipart/form-data

参数:
- audio: 隐写音频文件 (必需)
- encryption_key: 解密密钥 (可选)
- embedding_info: 嵌入信息JSON (可选)
```

**响应**
```json
{
  "success": true,
  "message": "这是隐藏的秘密信息",
  "extraction_info": {
    "success": true,
    "extracted_length": 25
  }
}
```

---

### 4. 获取容量

计算音频文件可嵌入的最大容量。

**请求**
```http
POST /api/capacity
Content-Type: multipart/form-data

参数:
- audio: 音频文件 (必需)
```

**响应**
```json
{
  "success": true,
  "capacity": {
    "total": 41343
  },
  "audio_length": 2646000,
  "input_file": "audio.mp3"
}
```

---

### 5. 获取音频信息

获取音频文件的基本信息。

**请求**
```http
POST /api/audio-info
Content-Type: multipart/form-data

参数:
- audio: 音频文件 (必需)
```

**响应**
```json
{
  "success": true,
  "info": {
    "duration": 60.0,
    "sample_rate": 44100,
    "length": 2646000,
    "channels": 1,
    "max_amplitude": 0.95,
    "rms": 0.25
  }
}
```

---

### 6. AI优化

使用AI模型优化嵌入参数。

**请求**
```http
POST /api/ai/optimize
Content-Type: multipart/form-data

参数:
- audio: 音频文件 (必需)
- message: 要嵌入的信息 (必需)
```

**响应**
```json
{
  "success": true,
  "optimization": {
    "layer1_dwt": 33,
    "layer2_dct": 33,
    "layer3_lsb": 34,
    "recommendation": "建议使用三层平均分配策略"
  },
  "quality_analysis": {
    "quality_score": 85,
    "suitable_for_embedding": true,
    "recommended_method": "dwt",
    "capacity_estimate": 1000
  }
}
```

---

### 7. 下载文件

下载处理后的音频文件。

**请求**
```http
GET /api/download/{filename}
```

**响应**
- Content-Type: `audio/wav`
- 文件二进制流

---

### 8. 历史记录

获取操作历史记录。

**请求**
```http
GET /api/history
```

**响应**
```json
{
  "success": true,
  "history": [
    {
      "timestamp": "2026-02-24T10:00:00",
      "operation": "embed",
      "input_file": "audio.mp3",
      "output_file": "stego_xxx.wav",
      "message_length": 100
    }
  ]
}
```

**清除历史**
```http
POST /api/history/clear
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 文件不存在 |
| 413 | 文件过大 |
| 500 | 服务器内部错误 |

## 请求示例

### Python
```python
import requests

# 嵌入信息
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/embed',
        files={'audio': f},
        data={'message': '秘密信息'}
    )
    result = response.json()
    print(f"下载链接: {result['download_url']}")

# 提取信息
with open('stego_audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/extract',
        files={'audio': f}
    )
    result = response.json()
    print(f"提取的消息: {result['message']}")
```

### JavaScript
```javascript
// 嵌入信息
const formData = new FormData();
formData.append('audio', audioFile);
formData.append('message', '秘密信息');

fetch('/api/embed', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// 提取信息
const extractData = new FormData();
extractData.append('audio', stegoFile);

fetch('/api/extract', {
    method: 'POST',
    body: extractData
})
.then(response => response.json())
.then(data => console.log(data.message));
```

### curl
```bash
# 嵌入信息
curl -X POST http://localhost:5000/api/embed \
  -F "audio=@audio.mp3" \
  -F "message=秘密信息"

# 提取信息
curl -X POST http://localhost:5000/api/extract \
  -F "audio=@stego_audio.wav"

# 获取容量
curl -X POST http://localhost:5000/api/capacity \
  -F "audio=@audio.mp3"
```

---

## 注意事项

1. **文件大小**: 默认限制50MB
2. **消息长度**: 不能超过音频容量
3. **加密密钥**: 提取时需使用相同密钥
4. **音频格式**: 推荐使用WAV格式以获得最佳效果
