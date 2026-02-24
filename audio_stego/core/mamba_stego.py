import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional, Dict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../RawBMamba-main'))

try:
    from mamba_ssm.modules.mamba_simple import Mamba
    MAMBA_AVAILABLE = True
except ImportError:
    MAMBA_AVAILABLE = False
    print("Warning: Mamba SSM not available, using fallback implementation")

class MambaAudioFeatureExtractor(nn.Module):
    def __init__(self, d_model: int = 64, n_layer: int = 4, bidirectional: bool = True):
        super().__init__()
        self.d_model = d_model
        self.bidirectional = bidirectional
        
        self.conv_front = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=128, stride=64, padding=32),
            nn.BatchNorm1d(32),
            nn.SELU(),
            nn.Dropout(0.1)
        )
        
        self.conv_layers = nn.Sequential(
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.SELU(),
            nn.Conv1d(64, d_model, kernel_size=3, padding=1),
            nn.BatchNorm1d(d_model),
            nn.SELU()
        )
        
        if MAMBA_AVAILABLE:
            self.mamba_layers = nn.ModuleList([
                Mamba(d_model=d_model, d_state=16, d_conv=4, expand=2)
                for _ in range(n_layer)
            ])
        else:
            self.mamba_layers = nn.ModuleList([
                nn.TransformerEncoderLayer(d_model=d_model, nhead=4, dim_feedforward=d_model*4)
                for _ in range(n_layer)
            ])
        
        self.feature_proj = nn.Linear(d_model, d_model)
        self.quality_scorer = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        self.embedding_analyzer = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Linear(64, 3),
            nn.Softmax(dim=-1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict]:
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        x = self.conv_front(x)
        x = self.conv_layers(x)
        
        x = x.permute(0, 2, 1)
        
        for mamba_layer in self.mamba_layers:
            if MAMBA_AVAILABLE:
                x = x + mamba_layer(x)
            else:
                x = mamba_layer(x)
        
        if self.bidirectional:
            x_rev = torch.flip(x, dims=[1])
            for mamba_layer in self.mamba_layers:
                if MAMBA_AVAILABLE:
                    x_rev = x_rev + mamba_layer(x_rev)
                else:
                    x_rev = mamba_layer(x_rev)
            x = (x + torch.flip(x_rev, dims=[1])) / 2
        
        features = self.feature_proj(x)
        
        global_features = torch.mean(features, dim=1)
        
        quality_score = self.quality_scorer(global_features)
        embedding_distribution = self.embedding_analyzer(global_features)
        
        return features, {
            'quality_score': quality_score,
            'embedding_distribution': embedding_distribution,
            'global_features': global_features
        }

class AdaptiveEmbeddingController(nn.Module):
    def __init__(self, d_model: int = 64):
        super().__init__()
        
        self.strength_predictor = nn.Sequential(
            nn.Linear(d_model + 3, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
        self.position_scorer = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, features: torch.Tensor, 
                message_length: int, 
                capacity_info: Dict) -> Dict:
        
        batch_size, seq_len, d_model = features.shape
        
        capacity_tensor = torch.tensor([
            capacity_info.get('layer1_dwt', 0),
            capacity_info.get('layer2_dct', 0),
            capacity_info.get('layer3_lsb', 0)
        ], dtype=torch.float32).unsqueeze(0).expand(batch_size, -1)
        
        global_feat = torch.mean(features, dim=1)
        strength_input = torch.cat([global_feat, capacity_tensor], dim=-1)
        strength = self.strength_predictor(strength_input)
        
        position_scores = self.position_scorer(features).squeeze(-1)
        
        return {
            'embedding_strength': strength,
            'position_scores': position_scores,
            'recommended_positions': self._get_top_positions(position_scores, message_length)
        }
    
    def _get_top_positions(self, scores: torch.Tensor, k: int) -> torch.Tensor:
        _, top_indices = torch.topk(scores, min(k, scores.shape[1]))
        return top_indices

class MambaStegoSystem:
    def __init__(self, use_mamba: bool = True, device: str = 'cpu'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.use_mamba = use_mamba and MAMBA_AVAILABLE
        
        if self.use_mamba:
            self.feature_extractor = MambaAudioFeatureExtractor().to(self.device)
            self.embedding_controller = AdaptiveEmbeddingController().to(self.device)
        else:
            self.feature_extractor = None
            self.embedding_controller = None
    
    def analyze_audio(self, audio_data: np.ndarray) -> Dict:
        if not self.use_mamba:
            return self._simple_analysis(audio_data)
        
        audio_tensor = torch.FloatTensor(audio_data).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            features, analysis = self.feature_extractor(audio_tensor)
        
        return {
            'quality_score': analysis['quality_score'].item(),
            'embedding_distribution': analysis['embedding_distribution'][0].cpu().numpy(),
            'feature_dim': features.shape,
            'global_features': analysis['global_features'][0].cpu().numpy()
        }
    
    def optimize_embedding(self, audio_data: np.ndarray, 
                          message_length: int,
                          capacity_info: Dict) -> Dict:
        if not self.use_mamba:
            return self._simple_optimization(message_length, capacity_info)
        
        audio_tensor = torch.FloatTensor(audio_data).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            features, analysis = self.feature_extractor(audio_tensor)
            control = self.embedding_controller(features, message_length, capacity_info)
        
        distribution = analysis['embedding_distribution'][0].cpu().numpy()
        total = message_length
        
        layer1 = int(total * distribution[0])
        layer2 = int(total * distribution[1])
        layer3 = total - layer1 - layer2
        
        return {
            'layer1_dwt': layer1,
            'layer2_dct': layer2,
            'layer3_lsb': layer3,
            'embedding_strength': control['embedding_strength'].item(),
            'quality_score': analysis['quality_score'].item(),
            'recommended_positions': control['recommended_positions'][0].cpu().numpy()
        }
    
    def _simple_analysis(self, audio_data: np.ndarray) -> Dict:
        rms = np.sqrt(np.mean(audio_data ** 2))
        max_amp = np.max(np.abs(audio_data))
        
        quality_score = min(1.0, (rms + max_amp) / 2)
        
        return {
            'quality_score': quality_score,
            'embedding_distribution': np.array([0.33, 0.33, 0.34]),
            'feature_dim': None,
            'global_features': None
        }
    
    def _simple_optimization(self, message_length: int, capacity_info: Dict) -> Dict:
        return {
            'layer1_dwt': message_length // 3,
            'layer2_dct': message_length // 3,
            'layer3_lsb': message_length - 2 * (message_length // 3),
            'embedding_strength': 0.5,
            'quality_score': 0.75,
            'recommended_positions': None
        }