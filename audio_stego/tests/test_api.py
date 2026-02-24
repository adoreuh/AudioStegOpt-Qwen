import requests
import os
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    print("=" * 50)
    print("测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_embed(audio_path, message):
    print("=" * 50)
    print(f"测试嵌入接口...")
    print(f"音频文件: {audio_path}")
    print(f"消息: {message}")
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        return None
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': (os.path.basename(audio_path), f)}
            data = {'message': message}
            response = requests.post(f"{BASE_URL}/api/embed", files=files, data=data, timeout=60)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            return result
        return None
    except Exception as e:
        print(f"错误: {e}")
        return None

def test_extract(audio_path, embedding_info=None):
    print("=" * 50)
    print(f"测试提取接口...")
    print(f"音频文件: {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        return None
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': (os.path.basename(audio_path), f)}
            data = {}
            if embedding_info:
                data['embedding_info'] = json.dumps(embedding_info)
            response = requests.post(f"{BASE_URL}/api/extract", files=files, data=data, timeout=60)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        print(f"错误: {e}")
        return None

def test_capacity(audio_path):
    print("=" * 50)
    print(f"测试容量查询接口...")
    print(f"音频文件: {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        return None
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': (os.path.basename(audio_path), f)}
            response = requests.post(f"{BASE_URL}/api/capacity", files=files, timeout=60)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        print(f"错误: {e}")
        return None

def test_download(output_file):
    print("=" * 50)
    print(f"测试下载接口...")
    print(f"文件: {output_file}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/download/{output_file}", timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"内容类型: {response.headers.get('Content-Type', 'unknown')}")
        print(f"内容长度: {len(response.content)} 字节")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("音频隐写系统功能测试")
    print("=" * 60 + "\n")
    
    test_results = []
    
    test_results.append(("健康检查", test_health()))
    
    audio_files = [
        r"C:\Users\shg\Music\许嵩 - 有何不可.mp3",
        r"C:\Users\shg\Music\许嵩,何曼婷 - 素颜.mp3"
    ]
    
    test_messages = [
        "这是一条测试消息",
        "Hello, this is a test message with special characters: !@#$%",
        "中文测试：隐写术是一种将信息隐藏在载体中的技术"
    ]
    
    for audio_path in audio_files:
        if os.path.exists(audio_path):
            print(f"\n测试音频: {os.path.basename(audio_path)}")
            
            capacity_result = test_capacity(audio_path)
            test_results.append((f"容量查询-{os.path.basename(audio_path)}", capacity_result is not None and capacity_result.get('success')))
            
            for i, message in enumerate(test_messages[:2]):
                embed_result = test_embed(audio_path, message)
                test_results.append((f"嵌入测试-{os.path.basename(audio_path)}-{i+1}", embed_result is not None))
                
                if embed_result and embed_result.get('success'):
                    download_ok = test_download(embed_result['output_file'])
                    test_results.append((f"下载测试-{i+1}", download_ok))
            break
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("=" * 60)

if __name__ == "__main__":
    main()
