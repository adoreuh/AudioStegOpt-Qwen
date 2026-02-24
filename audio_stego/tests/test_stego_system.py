import unittest
import os
import sys
import tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.improved_stego import ImprovedStegoSystem, CapacityExceededError, ExtractionError
from core.audio_processor import AudioProcessor


class TestImprovedStegoSystem(unittest.TestCase):
    
    def setUp(self):
        self.stego = ImprovedStegoSystem()
        self.sample_rate = 44100
        self.duration = 5
        self.audio_data = np.random.randn(self.sample_rate * self.duration).astype(np.float32)
    
    def test_embed_and_extract_simple_message(self):
        message = "Hello, World!"
        modified_audio, embedding_info = self.stego.embed_message(self.audio_data, message)
        
        self.assertEqual(len(modified_audio), len(self.audio_data))
        self.assertEqual(embedding_info['data_length'], len(message.encode('utf-8')))
        self.assertEqual(embedding_info['method'], 'dwt_haar_level3')
        
        extracted_message, result_info = self.stego.extract_message(modified_audio, embedding_info)
        
        self.assertEqual(extracted_message, message)
        self.assertTrue(result_info['success'])
    
    def test_embed_chinese_message(self):
        message = "这是一条中文测试消息，包含特殊字符：！@#￥%"
        modified_audio, embedding_info = self.stego.embed_message(self.audio_data, message)
        
        extracted_message, result_info = self.stego.extract_message(modified_audio, embedding_info)
        
        self.assertEqual(extracted_message, message)
    
    def test_embed_long_message(self):
        message = "A" * 1000
        modified_audio, embedding_info = self.stego.embed_message(self.audio_data, message)
        
        extracted_message, result_info = self.stego.extract_message(modified_audio, embedding_info)
        
        self.assertEqual(extracted_message, message)
    
    def test_capacity_exceeded_error(self):
        capacity = self.stego.calculate_capacity(len(self.audio_data))
        oversized_message = "X" * (capacity + 1000)
        
        with self.assertRaises(CapacityExceededError):
            self.stego.embed_message(self.audio_data, oversized_message)
    
    def test_empty_message_error(self):
        with self.assertRaises(ValueError):
            self.stego.embed_message(self.audio_data, "")
    
    def test_empty_audio_error(self):
        with self.assertRaises(ValueError):
            self.stego.embed_message(np.array([]), "test message")
    
    def test_extract_empty_audio_error(self):
        with self.assertRaises(ExtractionError):
            self.stego.extract_message(np.array([]), {'data_length': 10})
    
    def test_extract_missing_embedding_info(self):
        with self.assertRaises(ExtractionError):
            self.stego.extract_message(self.audio_data, {})
    
    def test_extract_invalid_data_length(self):
        with self.assertRaises(ExtractionError):
            self.stego.extract_message(self.audio_data, {'data_length': -1})
    
    def test_calculate_capacity(self):
        capacity = self.stego.calculate_capacity(len(self.audio_data))
        
        self.assertGreater(capacity, 0)
        self.assertIsInstance(capacity, int)
    
    def test_calculate_capacity_zero_length(self):
        capacity = self.stego.calculate_capacity(0)
        
        self.assertEqual(capacity, 0)
    
    def test_audio_quality_preserved(self):
        message = "Test message"
        modified_audio, _ = self.stego.embed_message(self.audio_data, message)
        
        diff = np.abs(self.audio_data - modified_audio)
        mean_diff = np.mean(diff)
        
        self.assertLess(mean_diff, 0.1, "音频修改幅度应在合理范围内")


class TestAudioProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = AudioProcessor()
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_load_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            self.processor.load_audio("nonexistent_file.wav")
    
    def test_load_empty_path(self):
        with self.assertRaises(ValueError):
            self.processor.load_audio("")
    
    def test_save_without_data(self):
        output_path = os.path.join(self.test_dir, "test_output.wav")
        
        with self.assertRaises(ValueError):
            self.processor.save_audio(output_path)
    
    def test_save_with_empty_path(self):
        audio_data = np.random.randn(44100).astype(np.float32)
        
        with self.assertRaises(ValueError):
            self.processor.save_audio("", audio_data, 44100)
    
    def test_normalize_audio(self):
        audio_data = np.array([0.1, 0.5, 0.3, -0.2])
        normalized = self.processor.normalize_audio(audio_data)
        
        self.assertAlmostEqual(np.max(np.abs(normalized)), 1.0, places=5)
    
    def test_normalize_zero_audio(self):
        audio_data = np.zeros(100)
        normalized = self.processor.normalize_audio(audio_data)
        
        np.testing.assert_array_equal(normalized, audio_data)
    
    def test_convert_to_mono_stereo(self):
        stereo_audio = np.random.randn(100, 2)
        mono_audio = self.processor.convert_to_mono(stereo_audio)
        
        self.assertEqual(len(mono_audio.shape), 1)
        self.assertEqual(len(mono_audio), 100)
    
    def test_convert_to_mono_already_mono(self):
        mono_audio = np.random.randn(100)
        result = self.processor.convert_to_mono(mono_audio)
        
        np.testing.assert_array_equal(result, mono_audio)
    
    def test_calculate_snr(self):
        original = np.array([1.0, 2.0, 3.0, 4.0])
        modified = np.array([1.1, 2.1, 3.1, 4.1])
        
        snr = self.processor.calculate_snr(original, modified)
        
        self.assertGreater(snr, 0)
        self.assertIsInstance(snr, float)
    
    def test_calculate_snr_identical(self):
        audio = np.random.randn(100)
        snr = self.processor.calculate_snr(audio, audio)
        
        self.assertEqual(snr, float('inf'))
    
    def test_calculate_psnr(self):
        original = np.array([1.0, 2.0, 3.0, 4.0])
        modified = np.array([1.1, 2.1, 3.1, 4.1])
        
        psnr = self.processor.calculate_psnr(original, modified)
        
        self.assertGreater(psnr, 0)
        self.assertIsInstance(psnr, float)
    
    def test_calculate_psnr_identical(self):
        audio = np.random.randn(100)
        psnr = self.processor.calculate_psnr(audio, audio)
        
        self.assertEqual(psnr, float('inf'))
    
    def test_get_audio_info_no_data(self):
        info = self.processor.get_audio_info()
        
        self.assertEqual(info, {})
    
    def test_supported_formats(self):
        self.assertIn('.wav', AudioProcessor.SUPPORTED_FORMATS)
        self.assertIn('.mp3', AudioProcessor.SUPPORTED_FORMATS)
        self.assertIn('.flac', AudioProcessor.SUPPORTED_FORMATS)


class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        self.stego = ImprovedStegoSystem()
        self.processor = AudioProcessor()
        self.sample_rate = 44100
        self.duration = 10
        self.audio_data = np.random.randn(self.sample_rate * self.duration).astype(np.float32)
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        message = "Integration test message"
        
        modified_audio, embedding_info = self.stego.embed_message(self.audio_data, message)
        
        extracted_message, result_info = self.stego.extract_message(modified_audio, embedding_info)
        
        self.assertEqual(extracted_message, message)
    
    def test_file_save_load_workflow(self):
        message = "File workflow test"
        
        modified_audio, embedding_info = self.stego.embed_message(self.audio_data, message)
        
        output_path = os.path.join(self.test_dir, "test_stego.wav")
        self.processor.save_audio(output_path, modified_audio, self.sample_rate)
        
        self.assertTrue(os.path.exists(output_path))
        
        loaded_audio, loaded_sr = self.processor.load_audio(output_path)
        
        self.assertEqual(loaded_sr, self.sample_rate)
        self.assertGreater(len(loaded_audio), 0)
    
    def test_multiple_embed_extract_cycles(self):
        messages = [
            "First message",
            "第二条消息",
            "Third message with numbers 12345",
            "第四条消息包含特殊字符！@#￥%"
        ]
        
        for message in messages:
            audio_data = np.random.randn(self.sample_rate * self.duration).astype(np.float32)
            modified_audio, embedding_info = self.stego.embed_message(audio_data, message)
            extracted_message, _ = self.stego.extract_message(modified_audio, embedding_info)
            self.assertEqual(extracted_message, message)


if __name__ == '__main__':
    unittest.main(verbosity=2)
