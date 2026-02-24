import numpy as np
from typing import Tuple, Optional, Dict
import pywt
from scipy.fftpack import dct, idct
import hashlib
import base64

class RobustStegoSystem:
    def __init__(self):
        self.sync_marker = "STEGO"
    
    def embed_message_robust(self, audio_data: np.ndarray, message: str,
                            layer_distribution: Dict[str, int],
                            encryption_key: Optional[str] = None) -> Tuple[np.ndarray, Dict]:
        
        if encryption_key:
            message = self._encrypt_message(message, encryption_key)
        
        modified_audio = audio_data.copy()
        
        layer1_len = layer_distribution.get('layer1', 0)
        layer2_len = layer_distribution.get('layer2', 0)
        layer3_len = layer_distribution.get('layer3', 0)
        
        layer1_msg = message[:layer1_len]
        layer2_msg = message[layer1_len:layer1_len + layer2_len]
        layer3_msg = message[layer1_len + layer2_len:]
        
        if layer1_msg:
            modified_audio = self._embed_dwt_robust(modified_audio, layer1_msg)
        if layer2_msg:
            modified_audio = self._embed_dct_robust(modified_audio, layer2_msg)
        if layer3_msg:
            modified_audio = self._embed_lsb_robust(modified_audio, layer3_msg)
        
        embedding_info = {
            'layer1': {'data_length': len(layer1_msg), 'method': 'dwt'},
            'layer2': {'data_length': len(layer2_msg), 'method': 'dct'},
            'layer3': {'data_length': len(layer3_msg), 'method': 'lsb'},
            'total_length': len(message),
            'encrypted': encryption_key is not None
        }
        
        return modified_audio, embedding_info
    
    def extract_message_robust(self, audio_data: np.ndarray, 
                               embedding_info: Dict,
                               encryption_key: Optional[str] = None) -> Tuple[str, Dict]:
        
        layer1_len = embedding_info['layer1']['data_length']
        layer2_len = embedding_info['layer2']['data_length']
        layer3_len = embedding_info['layer3']['data_length']
        
        layer1_msg = self._extract_dwt_robust(audio_data, layer1_len)
        layer2_msg = self._extract_dct_robust(audio_data, layer2_len)
        layer3_msg = self._extract_lsb_robust(audio_data, layer3_len)
        
        extracted_message = layer1_msg + layer2_msg + layer3_msg
        
        if encryption_key:
            try:
                extracted_message = self._decrypt_message(extracted_message, encryption_key)
            except Exception as e:
                return "", {'success': False, 'error': f'Decryption failed: {e}'}
        
        return extracted_message, {
            'success': True,
            'extracted_length': len(extracted_message),
            'layer1_length': len(layer1_msg),
            'layer2_length': len(layer2_msg),
            'layer3_length': len(layer3_msg)
        }
    
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
    
    def _embed_dwt_robust(self, audio_data: np.ndarray, message: str) -> np.ndarray:
        if not message:
            return audio_data
            
        coeffs = pywt.wavedec(audio_data, 'haar', level=3)
        
        cA = coeffs[0]
        binary_data = ''.join(format(ord(char), '08b') for char in message)
        
        for i, bit in enumerate(binary_data):
            if i < len(cA):
                if bit == '1':
                    cA[i] = abs(cA[i]) + 0.001
                else:
                    cA[i] = -abs(cA[i]) - 0.001
        
        coeffs[0] = cA
        reconstructed = pywt.waverec(coeffs, 'haar')
        
        if len(reconstructed) != len(audio_data):
            if len(reconstructed) > len(audio_data):
                reconstructed = reconstructed[:len(audio_data)]
            else:
                reconstructed = np.pad(reconstructed, (0, len(audio_data) - len(reconstructed)), 'constant')
        
        return reconstructed
    
    def _extract_dwt_robust(self, audio_data: np.ndarray, length: int) -> str:
        if length == 0:
            return ""
            
        coeffs = pywt.wavedec(audio_data, 'haar', level=3)
        cA = coeffs[0]
        
        binary_data = ''
        for i in range(length * 8):
            if i < len(cA):
                bit = '1' if cA[i] >= 0 else '0'
                binary_data += bit
        
        message = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) == 8:
                char_code = int(byte, 2)
                if 0 <= char_code <= 255:
                    message += chr(char_code)
        
        return message
    
    def _embed_dct_robust(self, audio_data: np.ndarray, message: str) -> np.ndarray:
        if not message:
            return audio_data
            
        dct_coeffs = dct(audio_data, type=2, norm='ortho')
        
        binary_data = ''.join(format(ord(char), '08b') for char in message)
        
        mid_freq_start = len(dct_coeffs) // 4
        mid_freq_end = len(dct_coeffs) // 2
        
        available_range = mid_freq_end - mid_freq_start
        if len(binary_data) > 0:
            step = max(1, available_range // len(binary_data))
        else:
            step = 1
        
        for i, bit in enumerate(binary_data):
            idx = mid_freq_start + i * step
            if idx < mid_freq_end:
                if bit == '1':
                    dct_coeffs[idx] = abs(dct_coeffs[idx]) + 0.0001
                else:
                    dct_coeffs[idx] = -abs(dct_coeffs[idx]) - 0.0001
        
        reconstructed = idct(dct_coeffs, type=2, norm='ortho')
        
        return reconstructed
    
    def _extract_dct_robust(self, audio_data: np.ndarray, length: int) -> str:
        if length == 0:
            return ""
            
        dct_coeffs = dct(audio_data, type=2, norm='ortho')
        
        mid_freq_start = len(dct_coeffs) // 4
        mid_freq_end = len(dct_coeffs) // 2
        
        available_range = mid_freq_end - mid_freq_start
        total_bits = length * 8
        if total_bits > 0:
            step = max(1, available_range // total_bits)
        else:
            step = 1
        
        binary_data = ''
        for i in range(total_bits):
            idx = mid_freq_start + i * step
            if idx < mid_freq_end:
                bit = '1' if dct_coeffs[idx] >= 0 else '0'
                binary_data += bit
        
        message = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) == 8:
                char_code = int(byte, 2)
                if 0 <= char_code <= 255:
                    message += chr(char_code)
        
        return message
    
    def _embed_lsb_robust(self, audio_data: np.ndarray, message: str) -> np.ndarray:
        if not message:
            return audio_data
            
        modified = audio_data.copy()
        
        binary_data = ''.join(format(ord(char), '08b') for char in message)
        
        for i, bit in enumerate(binary_data):
            if i < len(modified):
                sample = int(modified[i] * 32767)
                
                if bit == '1':
                    sample = sample | 1
                else:
                    sample = sample & ~1
                
                modified[i] = sample / 32767.0
        
        return modified
    
    def _extract_lsb_robust(self, audio_data: np.ndarray, length: int) -> str:
        if length == 0:
            return ""
            
        binary_data = ''
        
        for i in range(length * 8):
            if i < len(audio_data):
                sample = int(audio_data[i] * 32767)
                bit = str(sample & 1)
                binary_data += bit
        
        message = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) == 8:
                char_code = int(byte, 2)
                if 0 <= char_code <= 255:
                    message += chr(char_code)
        
        return message