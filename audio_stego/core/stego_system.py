import numpy as np
from typing import Dict, Tuple, Optional
from .audio_processor import AudioProcessor
from .three_layer_stego import ThreeLayerStego
from .encryption import EncryptionManager
import json
import os

class AudioStegoSystem:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.stego_system = ThreeLayerStego()
        self.encryption_manager = EncryptionManager()
        
        self.history = []
        self.history_file = 'stego_history.json'
        self._load_history()

    def embed_message(self, audio_path: str, message: str, output_path: str,
                     encryption_key: Optional[str] = None,
                     layer_distribution: Optional[Dict[str, str]] = None) -> Dict:
        
        result = {
            'operation': 'embed',
            'input_file': os.path.basename(audio_path),
            'output_file': os.path.basename(output_path),
            'message_length': len(message),
            'success': False,
            'error': None,
            'metrics': {}
        }
        
        try:
            audio_data, sample_rate = self.audio_processor.load_audio(audio_path)
            
            if encryption_key:
                self.stego_system.set_encryption_key(encryption_key)
                encrypted_message = self.encryption_manager.encrypt_data(message)
                message_to_embed = encrypted_message
                result['encrypted'] = True
            else:
                message_to_embed = message
                result['encrypted'] = False
            
            modified_audio, embedding_info = self.stego_system.embed_data(
                audio_data, message_to_embed, layer_distribution
            )
            
            if not embedding_info['success']:
                result['error'] = embedding_info.get('error', 'Embedding failed')
                return result
            
            self.audio_processor.save_audio(output_path, modified_audio, sample_rate)
            
            snr = self.audio_processor.calculate_snr(audio_data, modified_audio)
            psnr = self.audio_processor.calculate_psnr(audio_data, modified_audio)
            
            result['success'] = True
            result['metrics'] = {
                'snr': snr,
                'psnr': psnr,
                'embedding_info': embedding_info
            }
            
            self._add_to_history(result)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def extract_message(self, audio_path: str, embedding_info: Dict,
                       encryption_key: Optional[str] = None,
                       use_key: bool = False) -> Dict:
        
        result = {
            'operation': 'extract',
            'input_file': os.path.basename(audio_path),
            'success': False,
            'error': None,
            'extracted_message': '',
            'decryption_success': False
        }
        
        try:
            audio_data, _ = self.audio_processor.load_audio(audio_path)
            
            if encryption_key:
                self.stego_system.set_encryption_key(encryption_key)
            
            extracted_message, extraction_info = self.stego_system.extract_data(
                audio_data, embedding_info, use_key=use_key
            )
            
            if not extraction_info['success']:
                result['error'] = extraction_info.get('error', 'Extraction failed')
                return result
            
            result['success'] = True
            result['extracted_message'] = extracted_message
            result['extraction_info'] = extraction_info
            result['decryption_success'] = extraction_info.get('decryption_success', False)
            
            self._add_to_history(result)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def get_capacity(self, audio_path: str) -> Dict:
        result = {
            'input_file': os.path.basename(audio_path),
            'success': False,
            'error': None,
            'capacity': {}
        }
        
        try:
            audio_data, _ = self.audio_processor.load_audio(audio_path)
            audio_length = len(audio_data)
            
            capacity = self.stego_system.calculate_capacity(audio_length)
            
            result['success'] = True
            result['capacity'] = capacity
            result['audio_length'] = audio_length
            
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def get_audio_info(self, audio_path: str) -> Dict:
        result = {
            'input_file': os.path.basename(audio_path),
            'success': False,
            'error': None,
            'info': {}
        }
        
        try:
            self.audio_processor.load_audio(audio_path)
            info = self.audio_processor.get_audio_info()
            
            result['success'] = True
            result['info'] = info
            
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def get_history(self, limit: int = 10) -> list:
        return self.history[-limit:]

    def clear_history(self) -> None:
        self.history = []
        self._save_history()

    def _add_to_history(self, operation_result: Dict) -> None:
        import time
        operation_result['timestamp'] = time.time()
        self.history.append(operation_result)
        self._save_history()

    def _load_history(self) -> None:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def _save_history(self) -> None:
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_layer_config(self) -> Dict:
        return self.stego_system.get_layer_info()