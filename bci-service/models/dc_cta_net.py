# bci-service/models/dc_cta_net.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 100):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, d_model)
        return x + self.pe[:, :x.size(1)]

class DCTANet(nn.Module):
    """
    DC-CTA Net: Dual-Channel Cross-Temporal Attention Network
    
    Architecture:
    1. Input Projection: Projects 16-D Differential Entropy/Asymmetry features to d_model (64)
    2. Positional Encoding + Multi-Head Self-Attention over temporal sequence (epochs)
    3. Feed-Forward Residual Layer with LayerNorm and Dropout
    4. Dual Classification Heads:
       - Sleep-Stage Head: 5 classes (Wake, N1, N2, N3, REM)
       - Dream Mentation Head: 5 HVdC archetypes (Restful Baseline, Vivid Sensory, Cognitive Mentation, Motor Agitation, Threat Simulation)
    """

    SLEEP_STAGES = ["Wake", "N1", "N2", "N3", "REM"]
    HVDC_ARCHETYPES = [
        "Restful Baseline",
        "Vivid Sensory",
        "Cognitive Mentation",
        "Motor Agitation",
        "Threat Simulation"
    ]

    def __init__(self, input_dim: int = 16, d_model: int = 64, nhead: int = 4, num_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.input_dim = input_dim
        self.d_model = d_model

        # Linear projection
        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model)

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 2,
            dropout=dropout,
            batch_first=True,
            activation='gelu'
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Sleep-stage classification head
        self.stage_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(32, len(self.SLEEP_STAGES))
        )

        # Dream mentation classification head (Hall-Van de Castle Archetypes)
        self.dream_head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(32, len(self.HVDC_ARCHETYPES))
        )

        # Valence / Arousal regression head
        self.affect_head = nn.Sequential(
            nn.Linear(d_model, 16),
            nn.GELU(),
            nn.Linear(16, 2) # [Valence (-1 to +1), Arousal (0 to 1)]
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        x: shape (batch_size, seq_len, 16) or (batch_size, 16)
        Returns:
            stage_logits: (batch_size, 5)
            dream_logits: (batch_size, 5)
            affect_coords: (batch_size, 2) -> [valence, arousal]
        """
        if x.dim() == 2:
            x = x.unsqueeze(1) # Add seq_len dimension = 1

        # Project and encode
        h = self.input_proj(x)
        h = self.pos_encoder(h)
        h = self.transformer_encoder(h)

        # Global temporal pooling (last token or mean pooling)
        h_pool = h[:, -1, :] # focus on most recent temporal epoch

        stage_logits = self.stage_head(h_pool)
        dream_logits = self.dream_head(h_pool)
        raw_affect = self.affect_head(h_pool)

        # Valence between -1 and +1, Arousal between 0 and 1
        valence = torch.tanh(raw_affect[:, 0:1])
        arousal = torch.sigmoid(raw_affect[:, 1:2])
        affect_coords = torch.cat([valence, arousal], dim=-1)

        return stage_logits, dream_logits, affect_coords

class DCTANetClassifier:
    """
    Inference wrapper for DC-CTA Net handling sliding temporal buffers, 
    posterior probability calculations, and acute nightmare trauma alerting.
    """

    def __init__(self, model_path: str = None, device: str = 'cpu'):
        self.device = torch.device(device)
        self.model = DCTANet().to(self.device)
        self.model.eval()
        self.history_buffer = []
        self.max_history = 5 # sliding sequence of 5 epochs (2.5 seconds context)

    def predict_epoch(self, feature_16d: torch.Tensor or list) -> Dict:
        """
        Takes a 16-D feature vector and predicts sleep stage and dream archetype.
        """
        if not isinstance(feature_16d, torch.Tensor):
            feat_tensor = torch.tensor(feature_16d, dtype=torch.float32, device=self.device)
        else:
            feat_tensor = feature_16d.to(self.device)

        self.history_buffer.append(feat_tensor)
        if len(self.history_buffer) > self.max_history:
            self.history_buffer.pop(0)

        # Stack temporal sequence
        seq_tensor = torch.stack(self.history_buffer).unsqueeze(0) # (1, seq_len, 16)

        with torch.no_grad():
            stage_logits, dream_logits, affect_coords = self.model(seq_tensor)

            stage_probs = F.softmax(stage_logits, dim=-1).squeeze(0).cpu().numpy()
            dream_probs = F.softmax(dream_logits, dim=-1).squeeze(0).cpu().numpy()
            affect = affect_coords.squeeze(0).cpu().numpy()

        stage_idx = int(stage_probs.argmax())
        dream_idx = int(dream_probs.argmax())

        current_stage = DCTANet.SLEEP_STAGES[stage_idx]
        current_archetype = DCTANet.HVDC_ARCHETYPES[dream_idx]
        valence = float(affect[0])
        arousal = float(affect[1])

        # Acute Nightmare / Trauma Alert conditions:
        # 1. Subject is in REM stage
        # 2. Threat Simulation probability >= 0.50 OR (Arousal > 0.75 and Valence < -0.30)
        threat_sim_prob = float(dream_probs[DCTANet.HVDC_ARCHETYPES.index("Threat Simulation")])
        is_trauma_alert = (current_stage == "REM" and threat_sim_prob >= 0.50) or (arousal > 0.80 and valence < -0.40)
        trauma_severity = float(threat_sim_prob * 0.6 + arousal * 0.4)

        return {
            "stage": current_stage,
            "stage_probabilities": {DCTANet.SLEEP_STAGES[i]: float(stage_probs[i]) for i in range(len(DCTANet.SLEEP_STAGES))},
            "dream_archetype": current_archetype,
            "dream_probabilities": {DCTANet.HVDC_ARCHETYPES[i]: float(dream_probs[i]) for i in range(len(DCTANet.HVDC_ARCHETYPES))},
            "valence": valence,
            "arousal": arousal,
            "trauma_alert": is_trauma_alert,
            "trauma_severity": trauma_severity,
            "threat_sim_prob": threat_sim_prob
        }
