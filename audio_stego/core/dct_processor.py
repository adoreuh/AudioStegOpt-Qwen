import numpy as np
from scipy.fftpack import dct, idct
from typing import Tuple

class DCTProcessor:
    def __init__(self, block_size=512):
        self.block_size = block_size

    def apply_dct(self, signal: np.ndarray) -> np.ndarray:
        dct_coeffs = dct(signal, type=2, norm='ortho')
        return dct_coeffs

    def apply_idct(self, dct_coeffs: np.ndarray) -> np.ndarray:
        reconstructed = idct(dct_coeffs, type=2, norm='ortho')
        return reconstructed

    def process_blocks(self, signal: np.ndarray) -> np.ndarray:
        self.original_length = len(signal)
        num_blocks = len(signal) // self.block_size
        if num_blocks == 0:
            return self.apply_dct(signal)
        
        padded_length = num_blocks * self.block_size
        dct_result = np.zeros(len(signal))
        
        for i in range(num_blocks):
            block = signal[i*self.block_size:(i+1)*self.block_size]
            dct_block = self.apply_dct(block)
            dct_result[i*self.block_size:(i+1)*self.block_size] = dct_block
        
        if padded_length < len(signal):
            remaining = signal[padded_length:]
            dct_remaining = self.apply_dct(remaining)
            dct_result[padded_length:] = dct_remaining
        
        return dct_result

    def reconstruct_blocks(self, dct_coeffs: np.ndarray) -> np.ndarray:
        num_blocks = len(dct_coeffs) // self.block_size
        if num_blocks == 0:
            return self.apply_idct(dct_coeffs)
        
        reconstructed = np.zeros(len(dct_coeffs))
        
        for i in range(num_blocks):
            block = dct_coeffs[i*self.block_size:(i+1)*self.block_size]
            idct_block = self.apply_idct(block)
            reconstructed[i*self.block_size:(i+1)*self.block_size] = idct_block
        
        remaining_start = num_blocks * self.block_size
        if remaining_start < len(dct_coeffs):
            remaining = dct_coeffs[remaining_start:]
            idct_remaining = self.apply_idct(remaining)
            reconstructed[remaining_start:] = idct_remaining
        
        return reconstructed

    def embed_in_mid_frequency(self, dct_coeffs: np.ndarray, data: str, 
                              start_pos: int = 100, step: int = 10) -> np.ndarray:
        modified_coeffs = dct_coeffs.copy()
        
        binary_data = ''.join(format(ord(char), '08b') for char in data)
        
        data_idx = 0
        coeff_idx = start_pos
        
        while data_idx < len(binary_data) and coeff_idx < len(modified_coeffs):
            bit = int(binary_data[data_idx])
            modified_coeffs[coeff_idx] = self._modify_coefficient(modified_coeffs[coeff_idx], bit)
            data_idx += 1
            coeff_idx += step
        
        if data_idx < len(binary_data):
            raise ValueError("Data too large for embedding in DCT coefficients")
        
        return modified_coeffs

    def extract_from_mid_frequency(self, dct_coeffs: np.ndarray, data_length: int,
                                   start_pos: int = 100, step: int = 10) -> str:
        binary_data = ''
        
        data_idx = 0
        coeff_idx = start_pos
        
        while data_idx < data_length * 8 and coeff_idx < len(dct_coeffs):
            bit = self._extract_bit(dct_coeffs[coeff_idx])
            binary_data += str(bit)
            data_idx += 1
            coeff_idx += step
        
        extracted_text = ''
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            if len(byte) == 8:
                extracted_text += chr(int(byte, 2))
        
        return extracted_text

    def _modify_coefficient(self, coeff: float, bit: int) -> float:
        if bit == 1:
            return abs(coeff)
        else:
            return -abs(coeff)

    def _extract_bit(self, coeff: float) -> int:
        return 1 if coeff >= 0 else 0