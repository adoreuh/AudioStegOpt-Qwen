#!/bin/bash

echo "========================================"
echo "音频信息隐藏系统 - 启动脚本"
echo "========================================"
echo ""

echo "[1/2] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi
echo "✓ Python环境检查通过"
echo ""

echo "[2/2] 安装依赖包..."
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
