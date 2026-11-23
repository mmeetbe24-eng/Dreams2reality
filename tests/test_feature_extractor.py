# tests/test_feature_extractor.py
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bci-service"))

from features.feature_extractor import FeatureExtractor

def test_feature_extraction_dimension():
    extractor = FeatureExtractor(sampling_rate=128)
    dummy_epoch = np.random.normal(0, 15.0, size=(2, 256))

    vector_16d, stats = extractor.extract_features(dummy_epoch)

    assert isinstance(vector_16d, np.ndarray)
    assert vector_16d.shape == (16,)
    assert "t7_powers" in stats
    assert "t8_powers" in stats
    assert "dasm" in stats
    assert "rasm" in stats
    assert len(stats["dasm"]) == 4
    assert len(stats["rasm"]) == 4

# tests/test_dc_cta_net.py
from models.dc_cta_net import DCTANet, DCTANetClassifier
import torch

def test_dc_cta_net_forward_and_prediction():
    classifier = DCTANetClassifier()

    dummy_feat = np.random.normal(0, 1.0, size=(16,))
    pred = classifier.predict_epoch(dummy_feat)

    assert "stage" in pred
    assert pred["stage"] in DCTANet.SLEEP_STAGES
    assert "dream_archetype" in pred
    assert pred["dream_archetype"] in DCTANet.HVDC_ARCHETYPES
    assert "valence" in pred
    assert "arousal" in pred
    assert -1.0 <= pred["valence"] <= 1.0
    assert 0.0 <= pred["arousal"] <= 1.0
    assert "trauma_alert" in pred
