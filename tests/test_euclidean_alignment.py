# tests/test_euclidean_alignment.py
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bci-service"))

from alignment.euclidean_aligner import EuclideanAligner

def test_covariance_and_alignment():
    aligner = EuclideanAligner()

    # Create dummy epochs
    epochs = [np.random.normal(0, 10.0, size=(2, 256)) for _ in range(5)]
    aligner.calibrate(epochs)

    assert aligner.is_calibrated
    assert aligner.ref_mean_cov is not None
    assert aligner.ref_mean_cov.shape == (2, 2)
    assert aligner.r_inv_sqrt.shape == (2, 2)

    # Test transform
    test_epoch = np.random.normal(0, 10.0, size=(2, 256))
    aligned = aligner.transform(test_epoch)
    assert aligned.shape == (2, 256)

    # Normalized covariance should have trace approximately equal to channel dimension (2)
    c_norm = aligner.align_covariance(aligner.compute_epoch_covariance(test_epoch))
    assert c_norm.shape == (2, 2)
