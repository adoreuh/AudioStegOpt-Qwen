import requests
import json
import os

BASE_URL = "http://127.0.0.1:5000"

def test_audio_info(audio_path):
    print("=" * 60)
    print(f"Testing audio-info endpoint with: {os.path.basename(audio_path)}")
    
    if not os.path.exists(audio_path):
        print(f"ERROR: File not found: {audio_path}")
        return None
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': (os.path.basename(audio_path), f)}
            response = requests.post(f"{BASE_URL}/api/audio-info", files=files, timeout=60)
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_capacity(audio_path):
    print("=" * 60)
    print(f"Testing capacity endpoint with: {os.path.basename(audio_path)}")
    
    if not os.path.exists(audio_path):
        print(f"ERROR: File not found: {audio_path}")
        return None
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': (os.path.basename(audio_path), f)}
            response = requests.post(f"{BASE_URL}/api/capacity", files=files, timeout=60)
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("\n" + "=" * 60)
    print("Audio Loading Diagnosis Test")
    print("=" * 60 + "\n")
    
    test_files = [
        r"C:\Users\shg\Music\许嵩 - 有何不可.mp3",
        r"C:\Users\shg\Music\许嵩,何曼婷 - 素颜.mp3",
    ]
    
    for audio_path in test_files:
        if os.path.exists(audio_path):
            print(f"\n{'='*60}")
            print(f"Testing: {os.path.basename(audio_path)}")
            print(f"Size: {os.path.getsize(audio_path) / (1024*1024):.2f} MB")
            
            audio_info = test_audio_info(audio_path)
            capacity = test_capacity(audio_path)
            
            if audio_info and audio_info.get('success'):
                print("[OK] Audio info loaded successfully")
            else:
                print("[FAIL] Audio info loading failed")
            
            if capacity and capacity.get('success'):
                print("[OK] Capacity loaded successfully")
            else:
                print("[FAIL] Capacity loading failed")
        else:
            print(f"[SKIP] File not found: {audio_path}")

if __name__ == "__main__":
    main()
