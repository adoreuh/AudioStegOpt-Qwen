"""
Qwen模型下载脚本
用于下载Qwen2.5-0.5B-Instruct模型到本地项目目录
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 60)
    print("Qwen2.5-0.5B-Instruct 模型下载工具")
    print("=" * 60)
    print()
    
    print("此脚本将下载Qwen2.5-0.5B-Instruct模型到本地项目目录。")
    print("模型大小约1GB，下载时间取决于网络速度。")
    print()
    
    response = input("是否继续下载? (y/n): ").strip().lower()
    if response != 'y':
        print("已取消下载。")
        return
    
    print()
    
    try:
        from utils.local_qwen import download_model
        if download_model():
            print()
            print("=" * 60)
            print("模型下载成功！")
            print("=" * 60)
            print()
            print("现在可以使用本地模型运行系统，无需Ollama服务。")
        else:
            print()
            print("模型下载失败，请检查网络连接后重试。")
    except ImportError as e:
        print(f"错误: 缺少必要的库 - {e}")
        print("请先安装依赖: pip install transformers torch")
    except Exception as e:
        print(f"下载过程出错: {e}")

if __name__ == "__main__":
    main()
