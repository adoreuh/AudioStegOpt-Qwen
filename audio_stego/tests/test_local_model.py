import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    print("=" * 50)
    print("测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result.get('success', False)
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_embed():
    print("=" * 50)
    print("测试嵌入接口...")
    
    audio_path = r"C:\Users\shg\Music\许嵩 - 有何不可.mp3"
    message = "测试本地模型集成"
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': ('test.mp3', f)}
            data = {'message': message}
            response = requests.post(f"{BASE_URL}/api/embed", files=files, data=data, timeout=60)
        
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result.get('success', False)
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("本地模型集成验证测试")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("健康检查", test_health()))
    results.append(("嵌入测试", test_embed()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    print(f"\n总计: {passed}/{len(results)} 测试通过")

if __name__ == "__main__":
    main()
