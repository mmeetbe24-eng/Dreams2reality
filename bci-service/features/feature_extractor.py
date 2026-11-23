# bci-service/features/feature_extractor.py
import numpy as np
from scipy.signal import welch
from typing import Dict, Tuple, List

class FeatureExtractor:
    """
    Multiband Spectral and Asymmetry Feature Extractor for T7 and T8 channels.
    Extracts:
    1. Welch Power Spectral Density (PSD) across physiological bands:
       - Delta (0.5 - 4.0 Hz)
       - Theta (4.0 - 8.0 Hz)
       - Alpha (8.0 - 12.0 Hz)
       - Beta (12.0 - 30.0 Hz)
       - Gamma (30.0 - 45.0 Hz)
    2. Differential Entropy (DE) for Gaussian distribution:
       DE = 0.5 * ln(2 * pi * e * variance)
    3. Differential Asymmetry (DASM = DE_T8 - DE_T7)
    4. Rational Asymmetry (RASM = DE_T8 / DE_T7)
    Total 16-D feature representation:
    [DE_T7(theta,alpha,beta,gamma), DE_T8(theta,alpha,beta,gamma), DASM(4 bands), RASM(4 bands)]
    """

    BANDS = {
        'delta': (0.5, 4.0),
        'theta': (4.0, 8.0),
        'alpha': (8.0, 12.0),
        'beta': (12.0, 30.0),
        'gamma': (30.0, 45.0)
    }

    CORE_4_BANDS = ['theta', 'alpha', 'beta', 'gamma']

    def __init__(self, sampling_rate: int = 128):
        self.fs = sampling_rate

    def compute_band_powers(self, signal_1d: np.ndarray) -> Dict[str, float]:
        """
        Computes absolute band powers using Welch's PSD method.
        """
        nperseg = min(len(signal_1d), self.fs)
        freqs, psd = welch(signal_1d, fs=self.fs, nperseg=nperseg)
        powers = {}

        for band_name, (low, high) in self.BANDS.items():
            idx = np.logical_and(freqs >= low, freqs <= high)
            if np.any(idx):
                # Trapezoidal integration for band power
                bp = np.trapezoid(psd[idx], freqs[idx]) if hasattr(np, 'trapezoid') else np.trapz(psd[idx], freqs[idx])
            else:
                bp = 1e-6
            powers[band_name] = max(float(bp), 1e-6)

        return powers

    def compute_differential_entropy(self, variance: float) -> float:
        """
        h(X) = 0.5 * ln(2 * pi * e * sigma^2)
        """
        var_clipped = max(variance, 1e-6)
        return float(0.5 * np.log(2 * np.pi * np.e * var_clipped))

    def extract_features(self, epoch: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Extracts 16-D feature vector and detailed spectral statistics.
        epoch: shape (2, N) where channel 0 is T7 and channel 1 is T8.
        
        Returns:
            feature_vector: np.ndarray of shape (16,)
            stats: dict with band powers, DASM, RASM, and ratio metrics
        """
        t7_signal = epoch[0]
        t8_signal = epoch[1]

        t7_powers = self.compute_band_powers(t7_signal)
        t8_powers = self.compute_band_powers(t8_signal)

        # Compute Differential Entropy across Core 4 Bands
        t7_de = {b: self.compute_differential_entropy(t7_powers[b]) for b in self.CORE_4_BANDS}
        t8_de = {b: self.compute_differential_entropy(t8_powers[b]) for b in self.CORE_4_BANDS}

        # DASM & RASM
        dasm = {}
        rasm = {}
        for b in self.CORE_4_BANDS:
            dasm[b] = float(t8_de[b] - t7_de[b])
            # Epsilon smoothing to prevent div by zero
            denom = t7_de[b] if abs(t7_de[b]) > 1e-4 else 1e-4
            rasm[b] = float(t8_de[b] / denom)

        # Assemble standardized 16-D feature vector
        vector_16d = np.array([
            t7_de['theta'], t7_de['alpha'], t7_de['beta'], t7_de['gamma'],
            t8_de['theta'], t8_de['alpha'], t8_de['beta'], t8_de['gamma'],
            dasm['theta'], dasm['alpha'], dasm['beta'], dasm['gamma'],
            rasm['theta'], rasm['alpha'], rasm['beta'], rasm['gamma']
        ], dtype=np.float32)

        stats = {
            't7_powers': t7_powers,
            't8_powers': t8_powers,
            't7_de': t7_de,
            't8_de': t8_de,
            'dasm': dasm,
            'rasm': rasm,
            'delta_ratio': (t7_powers['delta'] + t8_powers['delta']) / (sum(t7_powers.values()) + sum(t8_powers.values()) + 1e-6)
        }

        return vector_16d, stats
