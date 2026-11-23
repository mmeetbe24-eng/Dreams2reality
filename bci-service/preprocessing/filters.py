# bci-service/preprocessing/filters.py
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch
from typing import Tuple, List, Optional

class SignalPreprocessor:
    """
    Digital Signal Conditioning for dual-channel EEG (T7, T8).
    - 4th-order zero-phase Butterworth IIR bandpass (0.5 - 45.0 Hz)
    - 50.0 Hz powerline IIR notch filter (Q=30)
    - Amplitude gating (> +/-250 uV) to discard gross movement artifacts
    - Sliding window epoch extraction (2.0s duration, 0.5s stride at 128 Hz)
    """

    def __init__(self, sampling_rate: int = 128, artifact_threshold: float = 250.0):
        self.fs = sampling_rate
        self.artifact_threshold = artifact_threshold
        
        # 4th-order Butterworth bandpass (0.5 - 45 Hz)
        lowcut = 0.5
        highcut = 45.0
        nyq = 0.5 * self.fs
        low = lowcut / nyq
        high = highcut / nyq
        self.bp_b, self.bp_a = butter(4, [low, high], btype='bandpass')
        
        # 50 Hz Notch filter (Q=30)
        self.notch_b, self.notch_a = iirnotch(50.0, 30.0, self.fs)

    def bandpass_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Apply 4th-order zero-phase Butterworth bandpass filter.
        data: shape (channels, samples) or (samples,)
        """
        if data.shape[-1] < 15:
            return data
        return filtfilt(self.bp_b, self.bp_a, data, axis=-1)

    def notch_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Apply 50 Hz IIR notch filter.
        """
        if data.shape[-1] < 15:
            return data
        return filtfilt(self.notch_b, self.notch_a, data, axis=-1)

    def preprocess_stream(self, data: np.ndarray) -> np.ndarray:
        """
        Combined zero-phase bandpass + notch filtering.
        data: shape (2, N) where channel 0 is T7 and channel 1 is T8.
        """
        filtered = self.bandpass_filter(data)
        filtered = self.notch_filter(filtered)
        return filtered

    def detect_artifact(self, epoch: np.ndarray) -> Tuple[bool, float]:
        """
        Checks if absolute microvolt amplitude exceeds artifact threshold.
        Returns (is_artifact, max_amplitude)
        """
        max_val = float(np.max(np.abs(epoch)))
        is_artifact = max_val > self.artifact_threshold
        return is_artifact, max_val

    def sliding_windows(self, data: np.ndarray, window_size_sec: float = 2.0, stride_sec: float = 0.5) -> List[np.ndarray]:
        """
        Partitions multi-channel continuous signal into overlapping epochs.
        window_size_sec = 2.0 (256 samples @ 128 Hz)
        stride_sec = 0.5 (64 samples @ 128 Hz) -> 75% overlap
        """
        win_samples = int(window_size_sec * self.fs)
        stride_samples = int(stride_sec * self.fs)
        total_samples = data.shape[-1]

        epochs = []
        start = 0
        while start + win_samples <= total_samples:
            epoch = data[:, start:start + win_samples]
            epochs.append(epoch)
            start += stride_samples
            
        return epochs
