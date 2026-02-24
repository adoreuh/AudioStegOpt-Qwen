#!/bin/bash

echo "========================================"
echo "音频信息隐藏系统 - 启动脚本"
echo "========================================"
echo ""

echo "[1/3] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi
echo "✓ Python环境检查通过"
echo ""

echo "[2/3] 检查Ollama服务..."
if ! curl -s http://127.0.0.1:11434/api/tags &> /dev/null; then
    echo "! Ollama服务未运行，正在启动..."
    ollama serve &
    sleep 3
    echo "✓ Ollama服务已启动"
else
    echo "✓ Ollama服务运行中"
fi
echo ""

echo "[3/3] 安装依赖包..."
pip3 install -r requirements.txt -q
echo "✓ 依赖包安装完成"
echo ""

echo "========================================"
echo "系统启动中..."
echo "========================================"
echo ""
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

cd audio_stego
python3 api/app.py