import hashlib
import base64
from typing import Optional

class EncryptionManager:
    def __init__(self):
        self.key = None

    def set_key(self, key: str) -> None:
        self.key = key

    def generate_key(self, password: str, salt: Optional[str] = None) -> str:
        if salt is None:
            salt = 'default_salt'
        
        key = hashlib.sha256((password + salt).encode()).hexdigest()
        self.key = key
        return key

    def encrypt_data(self, data: str) -> str:
        if self.key is None:
            return data
        
        key_bytes = self.key.encode()
        data_bytes = data.encode()
        
        encrypted = bytearray()
        for i, byte in enumerate(data_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            encrypted.append(byte ^ key_byte)
        
        return base64.b64encode(encrypted).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        if self.key is None:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            key_bytes = self.key.encode()
            
            decrypted = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                decrypted.append(byte ^ key_byte)
            
            return decrypted.decode()
        except Exception:
            raise ValueError("Decryption failed. Invalid key or corrupted data.")

    def verify_key(self, data: str, encrypted_data: str) -> bool:
        try:
            decrypted = self.decrypt_data(encrypted_data)
            return decrypted == data
        except Exception:
            return False

    def hash_data(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def create_signature(self, data: str) -> str:
        signature = self.hash_data(data)[:16]
        return signature

    def verify_signature(self, data: str, signature: str) -> bool:
        calculated_signature = self.create_signature(data)
        return calculated_signature == signature