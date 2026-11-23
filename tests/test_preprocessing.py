# tests/test_preprocessing.py
import pytest
import numpy as np
import sys
from pathlib import Path

# Add bci-service path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bci-service"))

from preprocessing.filters import SignalPreprocessor

def test_bandpass_and_notch_filtering():
    fs = 128
    preprocessor = SignalPreprocessor(sampling_rate=fs)

    # Create synthetic signal with 10 Hz (in band), 50 Hz (powerline hum), and 60 Hz (out of band)
    t = np.linspace(0, 2.0, 256, endpoint=False)
    sig_10hz = 20.0 * np.sin(2 * np.pi * 10.0 * t)
    sig_50hz = 15.0 * np.sin(2 * np.pi * 50.0 * t)
    raw = np.array([sig_10hz + sig_50hz, sig_10hz + sig_50hz], dtype=np.float32)

    filtered = preprocessor.preprocess_stream(raw)

    assert filtered.shape == (2, 256)
    # 50 Hz powerline hum should be significantly attenuated
    assert np.std(filtered) < np.std(raw)

def test_artifact_detection():
    preprocessor = SignalPreprocessor(sampling_rate=128, artifact_threshold=250.0)

    # Normal epoch under 250 uV
    normal_epoch = np.random.uniform(-50.0, 50.0, size=(2, 256))
    is_art, max_val = preprocessor.detect_artifact(normal_epoch)
    assert not is_art
    assert max_val < 250.0

    # Motion artifact epoch exceeding 250 uV
    artifact_epoch = np.copy(normal_epoch)
    artifact_epoch[0, 100] = 340.0
    is_art, max_val = preprocessor.detect_artifact(artifact_epoch)
    assert is_art
    assert max_val >= 340.0
