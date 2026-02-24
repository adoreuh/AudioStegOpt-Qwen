@echo off
chcp 936 >nul
echo ========================================
echo Audio Steganography System - Launcher
echo ========================================
echo.

echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python environment check passed
echo.

echo [2/4] Installing dependencies...
pip install -r audio_stego/requirements.txt -q
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies failed to install
)
echo [OK] Dependencies installed
echo.

echo [3/4] Checking AI model...
python -c "import sys; sys.path.insert(0, 'audio_stego/utils'); from gguf_qwen import QwenGGUFModel; m = QwenGGUFModel(); print('[OK] GGUF model available' if m.is_available() else '[!] GGUF model not found')" 2>nul
if %errorlevel% neq 0 (
    echo [!] GGUF model not found, will use fallback mode
    echo     Model path: D:\models\blobs\sha256-7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa
)
echo.

echo [4/4] Checking port 5000...
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo WARNING: Port 5000 is already in use
    echo Please close the program using this port or change the port in app.py
    pause
    exit /b 1
)
echo [OK] Port 5000 is available
echo.

echo ========================================
echo Starting system...
echo ========================================
echo.
echo Access URL: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

cd audio_stego
python api/app.py

pause
