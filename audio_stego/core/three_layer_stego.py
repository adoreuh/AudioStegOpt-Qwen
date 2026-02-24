import numpy as np
from typing import Dict, Tuple, Optional
from .dwt_processor import DWTProcessor
from .dct_processor import DCTProcessor
from .lsb_processor import LSBProcessor
from .encryption import EncryptionManager

class ThreeLayerStego:
    def __init__(self):
        self.dwt_processor = DWTProcessor(wavelet='haar', level=3)
        self.dct_processor = DCTProcessor(block_size=512)
        self.lsb_processor = LSBProcessor(bit_depth=1)
        self.encryption_manager = EncryptionManager()
        
        self.layer_config = {
            'layer1': {'method': 'dwt', 'robustness': 'high', 'capacity': 'low'},
            'layer2': {'method': 'dct', 'robustness': 'medium', 'capacity': 'medium'},
            'layer3': {'method': 'lsb', 'robustness': 'low', 'capacity': 'high'}
        }

    def set_encryption_key(self, key: Optional[str] = None) -> None:
        if key:
            self.encryption_manager.set_key(key)

    def embed_data(self, audio_data: np.ndarray, secret_data: str, 
                   layer_distribution: Optional[Dict[str, str]] = None) -> Tuple[np.ndarray, Dict]:
        
        if layer_distribution is None:
            layer_distribution = {
                'layer1': secret_data[:len(secret_data)//3],
                'layer2': secret_data[len(secret_data)//3:2*len(secret_data)//3],
                'layer3': secret_data[2*len(secret_data)//3:]
            }
        
        modified_audio = audio_data.copy()
        embedding_info = {
            'layer1': {'method': 'dwt', 'data_length': len(layer_distribution['layer1'])},
            'layer2': {'method': 'dct', 'data_length': len(layer_distribution['layer2'])},
            'layer3': {'method': 'lsb', 'data_length': len(layer_distribution['layer3'])}
        }
        
        try:
            modified_audio = self._embed_layer3(modified_audio, layer_distribution['layer3'])
            modified_audio = self._embed_layer2(modified_audio, layer_distribution['layer2'])
            modified_audio = self._embed_layer1(modified_audio, layer_distribution['layer1'])
            
            embedding_info['success'] = True
            embedding_info['total_data_length'] = len(secret_data)
            
        except Exception as e:
            embedding_info['success'] = False
            embedding_info['error'] = str(e)
        
        return modified_audio, embedding_info

    def extract_data(self, audio_data: np.ndarray, embedding_info: Dict, 
                    use_key: bool = False) -> Tuple[str, Dict]:
        
        extracted_data = ''
        extraction_info = {
            'layer1': {'method': 'dwt', 'success': False},
            'layer2': {'method': 'dct', 'success': False},
            'layer3': {'method': 'lsb', 'success': False}
        }
        
        try:
            layer1_data = self._extract_layer1(audio_data, embedding_info['layer1']['data_length'])
            extraction_info['layer1']['success'] = True
            extraction_info['layer1']['extracted_length'] = len(layer1_data)
            extracted_data += layer1_data
            
            layer2_data = self._extract_layer2(audio_data, embedding_info['layer2']['data_length'])
            extraction_info['layer2']['success'] = True
            extraction_info['layer2']['extracted_length'] = len(layer2_data)
            extracted_data += layer2_data
            
            layer3_data = self._extract_layer3(audio_data, embedding_info['layer3']['data_length'])
            extraction_info['layer3']['success'] = True
            extraction_info['layer3']['extracted_length'] = len(layer3_data)
            extracted_data += layer3_data
            
            if use_key and self.encryption_manager.key:
                try:
                    decrypted_data = self.encryption_manager.decrypt_data(extracted_data)
                    extraction_info['decryption_success'] = True
                    extracted_data = decrypted_data
                except Exception as e:
                    extraction_info['decryption_success'] = False
                    extraction_info['decryption_error'] = str(e)
            
            extraction_info['success'] = True
            extraction_info['total_extracted_length'] = len(extracted_data)
            
        except Exception as e:
            extraction_info['success'] = False
            extraction_info['error'] = str(e)
        
        return extracted_data, extraction_info

    def _embed_layer1(self, audio_data: np.ndarray, data: str) -> np.ndarray:
        coeffs = self.dwt_processor.decompose(audio_data)
        modified_coeffs = self.dwt_processor.embed_in_coefficients(coeffs, data, position=0)
        reconstructed = self.dwt_processor.reconstruct(modified_coeffs)
        return reconstructed

    def _embed_layer2(self, audio_data: np.ndarray, data: str) -> np.ndarray:
        dct_coeffs = self.dct_processor.process_blocks(audio_data)
        modified_coeffs = self.dct_processor.embed_in_mid_frequency(dct_coeffs, data, 
                                                                    start_pos=100, step=10)
        reconstructed = self.dct_processor.reconstruct_blocks(modified_coeffs)
        return reconstructed

    def _embed_layer3(self, audio_data: np.ndarray, data: str) -> np.ndarray:
        modified_audio = self.lsb_processor.embed_lsb(audio_data, data, start_pos=0)
        return modified_audio

    def _extract_layer1(self, audio_data: np.ndarray, data_length: int) -> str:
        coeffs = self.dwt_processor.decompose(audio_data)
        extracted_data = self.dwt_processor.extract_from_coefficients(coeffs, data_length, position=0)
        return extracted_data

    def _extract_layer2(self, audio_data: np.ndarray, data_length: int) -> str:
        dct_coeffs = self.dct_processor.process_blocks(audio_data)
        extracted_data = self.dct_processor.extract_from_mid_frequency(dct_coeffs, data_length,
                                                                       start_pos=100, step=10)
        return extracted_data

    def _extract_layer3(self, audio_data: np.ndarray, data_length: int) -> str:
        extracted_data = self.lsb_processor.extract_lsb(audio_data, data_length, start_pos=0)
        return extracted_data

    def calculate_capacity(self, audio_length: int) -> Dict[str, int]:
        dwt_capacity = audio_length // 8
        dct_capacity = (audio_length - 100) // 80
        lsb_capacity = audio_length // 8
        
        return {
            'layer1_dwt': dwt_capacity,
            'layer2_dct': dct_capacity,
            'layer3_lsb': lsb_capacity,
            'total': dwt_capacity + dct_capacity + lsb_capacity
        }

    def get_layer_info(self) -> Dict:
        return self.layer_config