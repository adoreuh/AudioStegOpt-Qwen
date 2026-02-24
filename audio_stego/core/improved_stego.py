import numpy as np
from typing import Tuple, Optional, Dict
import pywt
from scipy.fftpack import dct, idct
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)

class CapacityExceededError(Exception):
    pass

class ExtractionError(Exception):
    pass

class ImprovedStegoSystem:
    def __init__(self):
        pass
    
    def calculate_capacity(self, audio_length: int) -> int:
        if audio_length <= 0:
            return 0
        max_level = pywt.dwt_max_level(audio_length, pywt.Wavelet('haar').dec_len)
        level = min(3, max_level)
        if level < 1:
            return 0
        coeffs_length = audio_length // (2 ** level)
        return max(0, coeffs_length // 8)
    
    def embed_message(self, audio_data: np.ndarray, message: str,
                     encryption_key: Optional[str] = None) -> Tuple[np.ndarray, Dict]:
        
        if audio_data is None or len(audio_data) == 0:
            raise ValueError("音频数据不能为空")
        
        if not message:
            raise ValueError("嵌入消息不能为空")
        
        if encryption_key:
            message = self._encrypt_message(message, encryption_key)
        
        modified_audio = audio_data.copy()
        
        coeffs = pywt.wavedec(modified_audio, 'haar', level=3)
        cA = coeffs[0]
        
        message_bytes = message.encode('utf-8')
        binary_data = ''.join(format(byte, '08b') for byte in message_bytes)
        
        if len(binary_data) > len(cA):
            max_capacity = self.calculate_capacity(len(audio_data))
            raise CapacityExceededError(
                f"消息长度超出容量: 需要 {len(message_bytes)} 字节, "
                f"最大容量约 {max_capacity} 字节"
            )
        
        for i, bit in enumerate(binary_data):
            if i < len(cA):
                if bit == '1':
                    cA[i] = abs(cA[i]) + 0.001
                else:
                    cA[i] = -abs(cA[i]) - 0.001
        
        coeffs[0] = cA
        modified_audio = pywt.waverec(coeffs, 'haar')
        
        if len(modified_audio) != len(audio_data):
            if len(modified_audio) > len(audio_data):
                modified_audio = modified_audio[:len(audio_data)]
            else:
                modified_audio = np.pad(modified_audio, (0, len(audio_data) - len(modified_audio)), 'constant')
        
        embedding_info = {
            'data_length': len(message_bytes),
            'encrypted': encryption_key is not None,
            'method': 'dwt_haar_level3',
            'audio_length': len(audio_data)
        }
        
        return modified_audio, embedding_info
    
    def extract_message(self, audio_data: np.ndarray, 
                       embedding_info: Dict,
                       encryption_key: Optional[str] = None) -> Tuple[str, Dict]:
        
        if audio_data is None or len(audio_data) == 0:
            raise ExtractionError("音频数据不能为空")
        
        if embedding_info is None:
            raise ExtractionError("嵌入信息不能为空")
        
        if 'data_length' not in embedding_info:
            raise ExtractionError("嵌入信息缺少data_length字段")
        
        length = embedding_info['data_length']
        
        if length <= 0:
            raise ExtractionError(f"无效的消息长度: {length}")
        
        coeffs = pywt.wavedec(audio_data, 'haar', level=3)
        cA = coeffs[0]
        
        required_bits = length * 8
        if required_bits > len(cA):
            raise ExtractionError(
                f"音频数据不足以提取消息: 需要 {required_bits} 位, "
                f"可用 {len(cA)} 位"
            )
        
        binary_data = ''
        for i in range(required_bits):
            if i < len(cA):
                bit = '1' if cA[i] >= 0 else '0'
                binary_data += bit
        
        message_bytes = bytearray()
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) == 8:
                message_bytes.append(int(byte, 2))
        
        try:
            message = message_bytes.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"UTF-8解码失败: {e}")
            raise ExtractionError(
                f"消息解码失败，可能是音频文件损坏或不是有效的隐写音频: {e}"
            )
        
        if encryption_key:
            try:
                message = self._decrypt_message(message, encryption_key)
            except Exception as e:
                raise ExtractionError(f'解密失败: {e}')
        
        return message, {'success': True, 'extracted_length': len(message)}
    
    def _encrypt_message(self, message: str, key: str) -> str:
        key_hash = hashlib.sha256(key.encode()).digest()
        
        message_bytes = message.encode('utf-8')
        encrypted_bytes = bytearray()
        
        for i, byte in enumerate(message_bytes):
            key_byte = key_hash[i % len(key_hash)]
            encrypted_bytes.append(byte ^ key_byte)
        
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode('ascii')
        return encrypted_b64
    
    def _decrypt_message(self, encrypted: str, key: str) -> str:
        key_hash = hashlib.sha256(key.encode()).digest()
        
        try:
            encrypted_bytes = base64.b64decode(encrypted.encode('ascii'))
            decrypted_bytes = bytearray()
            
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_hash[i % len(key_hash)]
                decrypted_bytes.append(byte ^ key_byte)
            
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")