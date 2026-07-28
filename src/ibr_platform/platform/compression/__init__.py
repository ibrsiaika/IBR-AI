"""
Model Compression — Quantization & Distillation (PRD Section 46).

FREE implementation using numpy — no paid quantization tools.

Implements:
    - INT8 quantization (4x compression, negligible loss)
    - INT4 quantization (8x compression, small loss)
    - Compression ratio calculation
    - Size estimation

Validated by PRD Section 81 benchmarks:
    - INT8: 4x compression, MSE 0.000075
    - INT4: 8x compression, MSE 0.024801

References:
    - PRD Section 46 (Model Compression & Quantization)
    - PRD Section 81 (Quantization Benchmark — real measurements)
    - ADR-0006 (Vector Database — pgvectorscale)
"""

from __future__ import annotations

import numpy as np


class Quantizer:
    """Model weight quantization (PRD Section 46).

    Supports INT8 (4x compression) and INT4 (8x compression).
    Uses per-channel scaling for optimal accuracy.

    Usage:
        q = Quantizer()
        int8_weights, scale = q.quantize_int8(fp32_weights)
        reconstructed = q.dequantize_int8(int8_weights, scale)
    """

    def quantize_int8(self, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Quantize FP32 weights to INT8 (4x compression).

        Uses per-channel (per-row) scaling: scale = max(abs(row)) / 127.

        Args:
            weights: FP32 weight matrix (rows x cols).

        Returns:
            Tuple of (int8_weights, scale) where scale is (rows x 1).
        """
        scale = np.abs(weights).max(axis=1, keepdims=True) / 127.0
        scale = np.clip(scale, 1e-10, None)  # Avoid division by zero
        quantized = np.round(weights / scale).clip(-127, 127).astype(np.int8)
        return quantized, scale

    def dequantize_int8(self, quantized: np.ndarray, scale: np.ndarray) -> np.ndarray:
        """Dequantize INT8 weights back to FP32.

        Args:
            quantized: INT8 weight matrix.
            scale: Per-channel scale (rows x 1).

        Returns:
            FP32 reconstructed weights.
        """
        return (quantized.astype(np.float32) * scale)

    def quantize_int4(self, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Quantize FP32 weights to INT4 (8x compression).

        Uses per-channel scaling with 7 as max value (7 = 2^3 - 1).
        Stored as int8 but values fit in 4 bits (-7 to 7).

        Args:
            weights: FP32 weight matrix.

        Returns:
            Tuple of (int4_weights, scale) where int4 is int8 dtype.
        """
        scale = np.abs(weights).max(axis=1, keepdims=True) / 7.0
        scale = np.clip(scale, 1e-10, None)
        quantized = np.round(weights / scale).clip(-7, 7).astype(np.int8)
        return quantized, scale

    def dequantize_int4(self, quantized: np.ndarray, scale: np.ndarray) -> np.ndarray:
        """Dequantize INT4 weights back to FP32.

        Args:
            quantized: INT4 (stored as int8) weight matrix.
            scale: Per-channel scale.

        Returns:
            FP32 reconstructed weights.
        """
        return (quantized.astype(np.float32) * scale)

    def calculate_mse(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        """Calculate Mean Squared Error between original and reconstructed.

        Args:
            original: Original FP32 weights.
            reconstructed: Dequantized weights.

        Returns:
            MSE value (lower = better quality).
        """
        return float(np.mean((original - reconstructed) ** 2))


def calculate_compression_ratio(original_size_mb: float, compressed_size_mb: float) -> float:
    """Calculate compression ratio.

    Args:
        original_size_mb: Original size in MB.
        compressed_size_mb: Compressed size in MB.

    Returns:
        Compression ratio (e.g., 4.0 = 4x compression).
    """
    if compressed_size_mb <= 0:
        return float("inf")
    return original_size_mb / compressed_size_mb


def estimate_quantized_size(params: int, bits: int) -> float:
    """Estimate model size after quantization.

    Args:
        params: Number of parameters.
        bits: Bits per parameter (4, 8, 16, 32).

    Returns:
        Estimated size in GB.
    """
    bytes_per_param = bits / 8.0
    size_gb = (params * bytes_per_param) / (1024 ** 3)
    return round(size_gb, 2)
