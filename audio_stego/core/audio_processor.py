import numpy as np
import soundfile as sf
from scipy.io import wavfile
from typing import Tuple, Optional
import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.flac', '.ogg', '.aac']

    def __init__(self):
        self.sample_rate = None
        self.audio_data = None
        self.channels = None

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        if not file_path:
            raise ValueError("文件路径不能为空")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的音频格式: {file_ext}。支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")
        
        try:
            logger.info(f"正在加载音频文件: {file_path}")
            
            if file_ext == '.mp3':
                return self._load_mp3(file_path)
            elif file_ext == '.flac':
                return self._load_flac(file_path)
            else:
                return self._load_wav(file_path)
            
        except Exception as e:
            logger.error(f"加载音频文件失败: {file_path}, 错误: {str(e)}")
            raise Exception(f"加载音频文件失败: {str(e)}")
    
    def _load_wav(self, file_path: str) -> Tuple[np.ndarray, int]:
        sample_rate, audio_data = wavfile.read(file_path)
        
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        elif audio_data.dtype == np.uint8:
            audio_data = (audio_data.astype(np.float32) - 128) / 128.0
        else:
            audio_data = audio_data.astype(np.float32)
        
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.channels = 1
        
        return self.audio_data, self.sample_rate
    
    def _load_flac(self, file_path: str) -> Tuple[np.ndarray, int]:
        audio_data, sample_rate = sf.read(file_path)
        
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.channels = 1
        
        return self.audio_data, self.sample_rate
    
    def _load_mp3(self, file_path: str) -> Tuple[np.ndarray, int]:
        try:
            audio_data, sample_rate = sf.read(file_path)
            
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            audio_data = audio_data.astype(np.float32)
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            self.audio_data = audio_data
            self.sample_rate = sample_rate
            self.channels = 1
            
            return self.audio_data, self.sample_rate
        except Exception:
            return self._load_mp3_via_command(file_path)
    
    def _load_mp3_via_command(self, file_path: str) -> Tuple[np.ndarray, int]:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            
            cmd = ['ffmpeg', '-i', file_path, '-ac', '1', '-ar', '44100', '-y', tmp_path]
            result = subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            
            audio_data, sample_rate = self._load_wav(tmp_path)
            return audio_data, sample_rate
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg处理超时: {file_path}")
            raise Exception("音频转换超时，文件可能过大或损坏")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg处理失败: {e.stderr.decode() if e.stderr else str(e)}")
            raise Exception(f"无法加载MP3文件，请确保已安装ffmpeg")
        except Exception as e:
            logger.error(f"MP3加载失败: {str(e)}")
            raise Exception(f"无法加载MP3文件: {str(e)}。请安装ffmpeg。")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as e:
                    logger.warning(f"无法删除临时文件 {tmp_path}: {e}")

    def save_audio(self, file_path: str, audio_data: Optional[np.ndarray] = None, 
                   sample_rate: Optional[int] = None) -> None:
        if audio_data is None:
            audio_data = self.audio_data
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        if audio_data is None or sample_rate is None:
            raise ValueError("没有可保存的音频数据")
        
        if not file_path:
            raise ValueError("文件路径不能为空")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            logger.info(f"正在保存音频文件: {file_path}")
            sf.write(file_path, audio_data, sample_rate)
            logger.info(f"音频文件保存成功: {file_path}")
        except Exception as e:
            logger.error(f"保存音频文件失败: {file_path}, 错误: {str(e)}")
            raise Exception(f"保存音频文件失败: {str(e)}")

    def get_audio_info(self) -> dict:
        if self.audio_data is None:
            return {}
        
        duration = len(self.audio_data) / self.sample_rate if self.sample_rate else 0
        
        return {
            'duration': duration,
            'sample_rate': self.sample_rate,
            'length': len(self.audio_data),
            'channels': self.channels,
            'max_amplitude': float(np.max(np.abs(self.audio_data))),
            'rms': float(np.sqrt(np.mean(self.audio_data ** 2)))
        }

    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val
        return audio_data

    def add_noise(self, audio_data: np.ndarray, noise_level: float = 0.001) -> np.ndarray:
        noise = np.random.normal(0, noise_level, audio_data.shape)
        return audio_data + noise

    def calculate_snr(self, original: np.ndarray, modified: np.ndarray) -> float:
        signal_power = np.mean(original ** 2)
        noise_power = np.mean((original - modified) ** 2)
        
        if noise_power == 0:
            return float('inf')
        
        snr = 10 * np.log10(signal_power / noise_power)
        return float(snr)

    def calculate_psnr(self, original: np.ndarray, modified: np.ndarray) -> float:
        mse = np.mean((original - modified) ** 2)
        
        if mse == 0:
            return float('inf')
        
        max_pixel = 1.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        return float(psnr)

    def convert_to_mono(self, audio_data: np.ndarray) -> np.ndarray:
        if len(audio_data.shape) == 1:
            return audio_data
        return np.mean(audio_data, axis=1)

    def resample(self, audio_data: np.ndarray, original_sr: int, target_sr: int) -> np.ndarray:
        from scipy import signal as scipy_signal
        
        if original_sr == target_sr:
            return audio_data
        
        number_of_samples = round(len(audio_data) * float(target_sr) / original_sr)
        resampled_audio = scipy_signal.resample(audio_data, number_of_samples)
        
        return resampled_audio