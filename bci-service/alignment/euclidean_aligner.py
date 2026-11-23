# bci-service/alignment/euclidean_aligner.py
import numpy as np
from typing import Optional, List

class EuclideanAligner:
    """
    Euclidean Covariance Alignment (EA) based on Riemannian geometry.
    Standardizes spatial covariance across subjects to mitigate skull bone 
    impedance drift and domain shift without requiring per-subject retraining.
    
    Formula:
        C_i = (1 / (N - 1)) * X_i * X_i^T in R^(2 x 2)
        R_ref = (1 / K) * sum_{k=1}^K C_k
        R_inv_sqrt = R_ref^(-1/2)
        X_tilde_i = R_inv_sqrt * X_i
    """

    def __init__(self, reg: float = 1e-5):
        self.reg = reg
        self.ref_mean_cov: Optional[np.ndarray] = None
        self.r_inv_sqrt: Optional[np.ndarray] = None
        self.is_calibrated: bool = False

    def compute_epoch_covariance(self, epoch: np.ndarray) -> np.ndarray:
        """
        Computes sample spatial covariance matrix for an epoch X in R^(channels, samples).
        """
        c, n = epoch.shape
        # Center epoch
        centered = epoch - np.mean(epoch, axis=1, keepdims=True)
        cov = np.dot(centered, centered.T) / max(n - 1, 1)
        # Regularization
        cov += self.reg * np.eye(c)
        return cov

    def calibrate(self, reference_epochs: List[np.ndarray]):
        """
        Calibrate reference mean covariance from a collection of baseline epochs.
        """
        if not reference_epochs:
            # Fallback to 2x2 identity matrix
            self.ref_mean_cov = np.eye(2)
            self.r_inv_sqrt = np.eye(2)
            self.is_calibrated = True
            return

        covs = [self.compute_epoch_covariance(ep) for ep in reference_epochs]
        self.ref_mean_cov = np.mean(covs, axis=0)
        self.r_inv_sqrt = self._matrix_inv_sqrt(self.ref_mean_cov)
        self.is_calibrated = True

    def _matrix_inv_sqrt(self, mat: np.ndarray) -> np.ndarray:
        """
        Computes inverse square root of a symmetric positive-definite matrix:
        mat = V * diag(eigenvals) * V.T
        mat^(-1/2) = V * diag(eigenvals^(-1/2)) * V.T
        """
        eigenvals, eigenvecs = np.linalg.eigh(mat)
        # Clip eigenvalues for numerical stability
        eigenvals = np.maximum(eigenvals, 1e-8)
        inv_sqrt_vals = 1.0 / np.sqrt(eigenvals)
        return eigenvecs @ np.diag(inv_sqrt_vals) @ eigenvecs.T

    def transform(self, epoch: np.ndarray) -> np.ndarray:
        """
        Applies Riemannian Euclidean Alignment to an epoch X:
        X_aligned = R^(-1/2) * X
        """
        if not self.is_calibrated or self.r_inv_sqrt is None:
            # Default to identity alignment if uncalibrated
            return epoch

        return self.r_inv_sqrt @ epoch

    def align_covariance(self, cov: np.ndarray) -> np.ndarray:
        """
        Projects covariance onto reference Riemannian origin:
        C_norm = R^(-1/2) * C * R^(-1/2)
        """
        if not self.is_calibrated or self.r_inv_sqrt is None:
            return cov
        return self.r_inv_sqrt @ cov @ self.r_inv_sqrt
