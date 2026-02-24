import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    print("=" * 50)
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ai_optimize():
    print("=" * 50)
    print("Testing AI optimize endpoint...")
    
    audio_path = r"C:\Users\shg\Music\许嵩 - 有何不可.mp3"
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': ('test.mp3', f)}
            data = {'message': 'Test AI optimization'}
            response = requests.post(f"{BASE_URL}/api/ai/optimize", files=files, data=data, timeout=120)
        
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("GGUF Model Integration Verification Test")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Health Check", test_health()))
    results.append(("AI Optimize", test_ai_optimize()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{len(results)} tests passed")

if __name__ == "__main__":
    main()
