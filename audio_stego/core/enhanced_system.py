import numpy as np
from typing import Dict, Tuple, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.robust_stego import RobustStegoSystem
from core.audio_processor import AudioProcessor
from utils.qwen_integration import QwenModelIntegration

try:
    from core.mamba_stego import MambaStegoSystem
    MAMBA_AVAILABLE = True
except ImportError:
    MAMBA_AVAILABLE = False

class EnhancedStegoSystem:
    def __init__(self, use_mamba: bool = True, use_ai: bool = True):
        self.audio_processor = AudioProcessor()
        self.robust_stego = RobustStegoSystem()
        
        self.use_mamba = use_mamba and MAMBA_AVAILABLE
        if self.use_mamba:
            try:
                self.mamba_system = MambaStegoSystem(use_mamba=True)
            except Exception as e:
                print(f"Mamba initialization failed: {e}")
                self.use_mamba = False
                self.mamba_system = None
        else:
            self.mamba_system = None
        
        self.use_ai = use_ai
        if use_ai:
            self.qwen_model = QwenModelIntegration()
        else:
            self.qwen_model = None
    
    def embed_message(self, audio_path: str, message: str, output_path: str,
                     encryption_key: Optional[str] = None,
                     use_ai_optimization: bool = True) -> Dict:
        
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
            
            capacity = self._calculate_capacity(len(audio_data))
            
            if len(message) > capacity['total']:
                result['error'] = f"Message too long. Max capacity: {capacity['total']}"
                return result
            
            layer_distribution = self._optimize_distribution(
                audio_data, message, capacity, use_ai_optimization
            )
            
            modified_audio, embedding_info = self.robust_stego.embed_message_robust(
                audio_data, message, layer_distribution, encryption_key
            )
            
            self.audio_processor.save_audio(output_path, modified_audio, sample_rate)
            
            snr = self.audio_processor.calculate_snr(audio_data, modified_audio)
            psnr = self.audio_processor.calculate_psnr(audio_data, modified_audio)
            
            result['success'] = True
            result['encrypted'] = encryption_key is not None
            result['metrics'] = {
                'snr': snr,
                'psnr': psnr,
                'embedding_info': embedding_info,
                'layer_distribution': layer_distribution
            }
            
        except Exception as e:
            result['error'] = str(e)
            import traceback
            traceback.print_exc()
        
        return result
    
    def extract_message(self, audio_path: str, embedding_info: Dict,
                       encryption_key: Optional[str] = None) -> Dict:
        
        result = {
            'operation': 'extract',
            'input_file': os.path.basename(audio_path),
            'success': False,
            'error': None,
            'extracted_message': ''
        }
        
        try:
            audio_data, _ = self.audio_processor.load_audio(audio_path)
            
            message, extract_info = self.robust_stego.extract_message_robust(
                audio_data, embedding_info, encryption_key
            )
            
            result['success'] = extract_info['success']
            result['extracted_message'] = message
            result['extraction_info'] = extract_info
            
        except Exception as e:
            result['error'] = str(e)
            import traceback
            traceback.print_exc()
        
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
            capacity = self._calculate_capacity(len(audio_data))
            
            result['success'] = True
            result['capacity'] = capacity
            result['audio_length'] = len(audio_data)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def analyze_audio(self, audio_path: str) -> Dict:
        result = {
            'input_file': os.path.basename(audio_path),
            'success': False,
            'error': None,
            'analysis': {}
        }
        
        try:
            audio_data, _ = self.audio_processor.load_audio(audio_path)
            
            audio_info = self.audio_processor.get_audio_info()
            
            if self.use_mamba and self.mamba_system:
                mamba_analysis = self.mamba_system.analyze_audio(audio_data)
                result['analysis']['mamba'] = mamba_analysis
            
            if self.use_ai and self.qwen_model and self.qwen_model.check_model_availability():
                ai_analysis = self.qwen_model.analyze_audio_quality(audio_info)
                result['analysis']['ai'] = ai_analysis
            
            result['analysis']['basic'] = audio_info
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _calculate_capacity(self, audio_length: int) -> Dict:
        dwt_capacity = audio_length // 16
        dct_capacity = audio_length // 32
        lsb_capacity = audio_length // 8
        
        return {
            'layer1_dwt': dwt_capacity,
            'layer2_dct': dct_capacity,
            'layer3_lsb': lsb_capacity,
            'total': dwt_capacity + dct_capacity + lsb_capacity
        }
    
    def _optimize_distribution(self, audio_data: np.ndarray, message: str,
                               capacity: Dict, use_ai: bool) -> Dict:
        
        if use_ai and self.qwen_model and self.qwen_model.check_model_availability():
            try:
                audio_info = self.audio_processor.get_audio_info()
                optimization = self.qwen_model.optimize_embedding_parameters(
                    audio_info, len(message)
                )
                
                return {
                    'layer1': optimization.get('layer1_dwt', len(message) // 3),
                    'layer2': optimization.get('layer2_dct', len(message) // 3),
                    'layer3': optimization.get('layer3_lsb', len(message) - 2 * (len(message) // 3))
                }
            except Exception as e:
                print(f"AI optimization failed: {e}")
        
        if self.use_mamba and self.mamba_system:
            try:
                mamba_opt = self.mamba_system.optimize_embedding(
                    audio_data, len(message), capacity
                )
                
                return {
                    'layer1': mamba_opt['layer1_dwt'],
                    'layer2': mamba_opt['layer2_dct'],
                    'layer3': mamba_opt['layer3_lsb']
                }
            except Exception as e:
                print(f"Mamba optimization failed: {e}")
        
        total = len(message)
        layer1 = min(total // 3, capacity['layer1_dwt'])
        layer2 = min(total // 3, capacity['layer2_dct'])
        layer3 = total - layer1 - layer2
        
        return {
            'layer1': layer1,
            'layer2': layer2,
            'layer3': layer3
        }