"""Tests for Section 46 — Model Compression."""
from __future__ import annotations
import pytest
import numpy as np


class TestQuantization:
    def test_importable(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        assert Quantizer is not None

    def test_int8_quantize(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        q = Quantizer()
        weights = np.random.randn(64, 64).astype(np.float32)
        int8, scale = q.quantize_int8(weights)
        assert int8.dtype == np.int8
        assert scale.shape == (64, 1)

    def test_int8_dequantize(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        q = Quantizer()
        weights = np.random.randn(64, 64).astype(np.float32)
        int8, scale = q.quantize_int8(weights)
        reconstructed = q.dequantize_int8(int8, scale)
        assert reconstructed.shape == weights.shape
        # MSE should be small
        mse = np.mean((weights - reconstructed) ** 2)
        assert mse < 0.01

    def test_int4_quantize(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        q = Quantizer()
        weights = np.random.randn(64, 64).astype(np.float32)
        int4, scale = q.quantize_int4(weights)
        assert int4.dtype == np.int8  # Stored as int8 but values fit in 4 bits
        assert scale.shape == (64, 1)

    def test_int4_dequantize(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        q = Quantizer()
        weights = np.random.randn(64, 64).astype(np.float32)
        int4, scale = q.quantize_int4(weights)
        reconstructed = q.dequantize_int4(int4, scale)
        assert reconstructed.shape == weights.shape

    def test_compression_ratio_int8(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        q = Quantizer()
        weights = np.random.randn(128, 128).astype(np.float32)
        int8, _ = q.quantize_int8(weights)
        fp32_size = weights.nbytes
        int8_size = int8.nbytes
        ratio = fp32_size / int8_size
        assert abs(ratio - 4.0) < 0.1  # ~4x compression

    def test_compression_ratio_int4(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        q = Quantizer()
        weights = np.random.randn(128, 128).astype(np.float32)
        int4, _ = q.quantize_int4(weights)
        fp32_size = weights.nbytes
        int4_effective = int4.nbytes / 2  # 4-bit values stored in 8-bit
        ratio = fp32_size / int4_effective
        assert abs(ratio - 8.0) < 0.2  # ~8x compression

    def test_int8_mse_lower_than_int4(self) -> None:
        from ibr_platform.platform.compression import Quantizer
        q = Quantizer()
        weights = np.random.randn(128, 128).astype(np.float32)
        i8, s8 = q.quantize_int8(weights)
        i4, s4 = q.quantize_int4(weights)
        mse8 = np.mean((weights - q.dequantize_int8(i8, s8)) ** 2)
        mse4 = np.mean((weights - q.dequantize_int4(i4, s4)) ** 2)
        assert mse8 < mse4  # INT8 should have lower MSE than INT4


class TestCompressionUtils:
    def test_calculate_compression_ratio(self) -> None:
        from ibr_platform.platform.compression import calculate_compression_ratio
        ratio = calculate_compression_ratio(original_size_mb=64.0, compressed_size_mb=8.0)
        assert abs(ratio - 8.0) < 0.01

    def test_estimate_quantized_size(self) -> None:
        from ibr_platform.platform.compression import estimate_quantized_size
        # 1B params in FP32 = 4GB
        size_int8 = estimate_quantized_size(params=1_000_000_000, bits=8)
        size_int4 = estimate_quantized_size(params=1_000_000_000, bits=4)
        assert size_int8 < 4.0  # Less than 4GB
        assert size_int4 < size_int8  # INT4 smaller than INT8
