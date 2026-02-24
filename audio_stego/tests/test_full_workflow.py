import requests
import os
import json
import tempfile

BASE_URL = "http://127.0.0.1:5000"

def test_embed_and_extract(audio_path, message):
    print("=" * 60)
    print(f"完整嵌入-提取测试")
    print(f"音频文件: {audio_path}")
    print(f"原始消息: {message}")
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        return False
    
    try:
        print("\n1. 嵌入消息...")
        with open(audio_path, 'rb') as f:
            files = {'audio': (os.path.basename(audio_path), f)}
            data = {'message': message}
            response = requests.post(f"{BASE_URL}/api/embed", files=files, data=data, timeout=60)
        
        embed_result = response.json()
        if not embed_result.get('success'):
            print(f"嵌入失败: {embed_result.get('error')}")
            return False
        
        print(f"嵌入成功!")
        print(f"输出文件: {embed_result['output_file']}")
        print(f"嵌入信息: {embed_result['metrics']['embedding_info']}")
        
        print("\n2. 下载嵌入后的音频...")
        download_response = requests.get(
            f"{BASE_URL}/api/download/{embed_result['output_file']}", 
            timeout=30
        )
        
        if download_response.status_code != 200:
            print(f"下载失败: {download_response.status_code}")
            return False
        
        print(f"下载成功! 文件大小: {len(download_response.content)} 字节")
        
        print("\n3. 提取消息...")
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, embed_result['output_file'])
        
        with open(temp_file, 'wb') as f:
            f.write(download_response.content)
        
        with open(temp_file, 'rb') as f:
            files = {'audio': (embed_result['output_file'], f)}
            data = {'embedding_info': json.dumps(embed_result['metrics']['embedding_info'])}
            response = requests.post(f"{BASE_URL}/api/extract", files=files, data=data, timeout=60)
        
        extract_result = response.json()
        
        os.remove(temp_file)
        os.rmdir(temp_dir)
        
        if not extract_result.get('success'):
            print(f"提取失败: {extract_result.get('error')}")
            return False
        
        extracted_message = extract_result['message']
        print(f"提取的消息: {extracted_message}")
        
        if extracted_message == message:
            print("\n✓ 测试通过! 消息完整匹配!")
            return True
        else:
            print(f"\n✗ 测试失败! 消息不匹配!")
            print(f"原始: {message}")
            print(f"提取: {extracted_message}")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("音频隐写系统完整功能测试")
    print("=" * 60 + "\n")
    
    test_cases = [
        (r"C:\Users\shg\Music\许嵩 - 有何不可.mp3", "这是一条中文测试消息"),
        (r"C:\Users\shg\Music\许嵩 - 有何不可.mp3", "English test message with numbers 12345"),
        (r"C:\Users\shg\Music\许嵩 - 有何不可.mp3", "混合测试Mixed Test中英文123!@#"),
        (r"C:\Users\shg\Music\许嵩,何曼婷 - 素颜.mp3", "测试不同音频文件的隐写效果"),
    ]
    
    results = []
    
    for audio_path, message in test_cases:
        if os.path.exists(audio_path):
            result = test_embed_and_extract(audio_path, message)
            results.append((os.path.basename(audio_path), message[:20] + "...", result))
        else:
            print(f"跳过: 文件不存在 {audio_path}")
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for audio, msg, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{audio} | {msg}: {status}")
    
    passed = sum(1 for _, _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    print("=" * 60)

if __name__ == "__main__":
    main()
