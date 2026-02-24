import numpy as np
from typing import Tuple

class LSBProcessor:
    def __init__(self, bit_depth: int = 1):
        self.bit_depth = bit_depth

    def embed_lsb(self, signal: np.ndarray, data: str, start_pos: int = 0) -> np.ndarray:
        modified_signal = signal.copy()
        
        binary_data = ''.join(format(ord(char), '08b') for char in data)
        
        if start_pos + len(binary_data) > len(modified_signal):
            raise ValueError("Data too large for LSB embedding")
        
        for i, bit in enumerate(binary_data):
            idx = start_pos + i
            if idx < len(modified_signal):
                modified_signal[idx] = self._modify_sample(modified_signal[idx], int(bit))
        
        return modified_signal

    def extract_lsb(self, signal: np.ndarray, data_length: int, start_pos: int = 0) -> str:
        binary_data = ''
        
        for i in range(data_length * 8):
            idx = start_pos + i
            if idx < len(signal):
                bit = self._extract_bit(signal[idx])
                binary_data += str(bit)
        
        extracted_text = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) == 8:
                extracted_text += chr(int(byte, 2))
        
        return extracted_text

    def embed_multi_lsb(self, signal: np.ndarray, data: str, 
                       start_pos: int = 0, bits_per_sample: int = 2) -> np.ndarray:
        modified_signal = signal.copy()
        
        binary_data = ''.join(format(ord(char), '08b') for char in data)
        
        total_bits_needed = len(binary_data)
        samples_needed = (total_bits_needed + bits_per_sample - 1) // bits_per_sample
        
        if start_pos + samples_needed > len(modified_signal):
            raise ValueError("Data too large for multi-bit LSB embedding")
        
        bit_idx = 0
        sample_idx = start_pos
        
        while bit_idx < len(binary_data) and sample_idx < len(modified_signal):
            sample = modified_signal[sample_idx]
            
            for bit_pos in range(bits_per_sample):
                if bit_idx < len(binary_data):
                    bit = int(binary_data[bit_idx])
                    sample = self._modify_sample_bit(sample, bit, bit_pos)
                    bit_idx += 1
            
            modified_signal[sample_idx] = sample
            sample_idx += 1
        
        return modified_signal

    def extract_multi_lsb(self, signal: np.ndarray, data_length: int,
                         start_pos: int = 0, bits_per_sample: int = 2) -> str:
        binary_data = ''
        
        total_bits_needed = data_length * 8
        samples_needed = (total_bits_needed + bits_per_sample - 1) // bits_per_sample
        
        bit_idx = 0
        sample_idx = start_pos
        
        while bit_idx < total_bits_needed and sample_idx < len(signal):
            sample = signal[sample_idx]
            
            for bit_pos in range(bits_per_sample):
                if bit_idx < total_bits_needed:
                    bit = self._extract_sample_bit(sample, bit_pos)
                    binary_data += str(bit)
                    bit_idx += 1
            
            sample_idx += 1
        
        extracted_text = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) == 8:
                extracted_text += chr(int(byte, 2))
        
        return extracted_text

    def _modify_sample(self, sample: float, bit: int) -> float:
        int_sample = int(sample * (2**15))
        mask = ~(1 << 0)
        int_sample = (int_sample & mask) | (bit << 0)
        return float(int_sample) / (2**15)

    def _extract_bit(self, sample: float) -> int:
        int_sample = int(sample * (2**15))
        return (int_sample >> 0) & 1

    def _modify_sample_bit(self, sample: float, bit: int, bit_pos: int) -> float:
        int_sample = int(sample * (2**15))
        mask = ~(1 << bit_pos)
        int_sample = (int_sample & mask) | (bit << bit_pos)
        return float(int_sample) / (2**15)

    def _extract_sample_bit(self, sample: float, bit_pos: int) -> int:
        int_sample = int(sample * (2**15))
        return (int_sample >> bit_pos) & 1

    def calculate_capacity(self, signal_length: int, bits_per_sample: int = 1) -> int:
        return (signal_length * bits_per_sample) // 8