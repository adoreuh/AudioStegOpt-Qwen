import numpy as np
import pywt
from scipy.fftpack import dct, idct
from typing import Tuple

class DWTProcessor:
    def __init__(self, wavelet='haar', level=3):
        self.wavelet = wavelet
        self.level = level

    def decompose(self, signal: np.ndarray) -> list:
        self.original_length = len(signal)
        coeffs = pywt.wavedec(signal, self.wavelet, level=self.level)
        return coeffs

    def reconstruct(self, coeffs: list) -> np.ndarray:
        reconstructed = pywt.waverec(coeffs, self.wavelet)
        if hasattr(self, 'original_length') and len(reconstructed) != self.original_length:
            if len(reconstructed) > self.original_length:
                reconstructed = reconstructed[:self.original_length]
            else:
                reconstructed = np.pad(reconstructed, (0, self.original_length - len(reconstructed)), 'constant')
        return reconstructed

    def get_subbands(self, coeffs: list) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        cA = coeffs[0]
        cD = coeffs[1]
        return cA, cD

    def embed_in_coefficients(self, coeffs: list, data: str, position: int = 0) -> list:
        modified_coeffs = coeffs.copy()
        cA = modified_coeffs[0]
        
        binary_data = ''.join(format(ord(char), '08b') for char in data)
        
        if position + len(binary_data) > len(cA):
            raise ValueError("Data too large for embedding position")
        
        for i, bit in enumerate(binary_data):
            idx = position + i
            if idx < len(cA):
                cA[idx] = self._modify_coefficient(cA[idx], int(bit))
        
        modified_coeffs[0] = cA
        return modified_coeffs

    def extract_from_coefficients(self, coeffs: list, data_length: int, position: int = 0) -> str:
        cA = coeffs[0]
        binary_data = ''
        
        for i in range(data_length * 8):
            idx = position + i
            if idx < len(cA):
                bit = self._extract_bit(cA[idx])
                binary_data += str(bit)
        
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