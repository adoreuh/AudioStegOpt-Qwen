import numpy as np
from typing import Dict, Tuple, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.improved_stego import ImprovedStegoSystem
from core.audio_processor import AudioProcessor
from utils.qwen_integration import QwenModelIntegration

try:
    from core.mamba_stego import MambaStegoSystem
    MAMBA_AVAILABLE = True
except ImportError:
    MAMBA_AVAILABLE = False

class FinalStegoSystem:
    def __init__(self, use_mamba: bool = True, use_ai: bool = True):
        self.audio_processor = AudioProcessor()
        self.stego = ImprovedStegoSystem()
        
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
            
            capacity = self.stego.calculate_capacity(len(audio_data))
            
            if len(message) > capacity:
                result['error'] = f"Message too long. Max capacity: {capacity}"
                return result
            
            modified_audio, embedding_info = self.stego.embed_message(
                audio_data, message, encryption_key
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
                'capacity': capacity
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
            
            message, extract_info = self.stego.extract_message(
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
            capacity = self.stego.calculate_capacity(len(audio_data))
            
            result['success'] = True
            result['capacity'] = {'total': capacity}
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
            
            if self.use_ai and self.qwen_model and self.qwen_model.check_model_availability():
                ai_analysis = self.qwen_model.analyze_audio_quality(audio_info)
                result['analysis']['ai'] = ai_analysis
            
            result['analysis']['basic'] = audio_info
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result