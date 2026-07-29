#!/usr/bin/env python3
"""
INT4 quantizer for IBR-GPT-Code models.
Converts fp32 weights to 4-bit (2 weights per byte) for 8x compression.
This is how we hit the 10-15MB target for the 40M model.

Method: Per-channel symmetric INT4 quantization
- For each weight tensor, find max abs value
- Scale = max_abs / 7
- Quantize: round(w / scale).clamp(-7, 7) → 4-bit signed int
- Pack 2 values per byte (high nibble + low nibble)
"""
import torch
import numpy as np
from typing import Dict, Tuple


def quantize_int4(tensor: torch.Tensor, block_size: int = 128) -> Tuple[np.ndarray, np.ndarray]:
    """Quantize a fp32 tensor to INT4 with per-block scales.
    
    Args:
        tensor: input fp32 tensor (1D or 2D)
        block_size: number of weights per quantization block (smaller = more accurate)
    
    Returns:
        (packed_int4_bytes, scales) — packed 2 values per byte, scales per block
    """
    flat = tensor.detach().cpu().float().numpy().ravel()
    # Pad to multiple of block_size * 2 (for packing)
    pad = (-len(flat)) % (block_size * 2)
    flat = np.pad(flat, (0, pad), mode='constant')
    
    # Reshape into blocks
    n_blocks = len(flat) // block_size
    blocks = flat.reshape(n_blocks, block_size)
    
    # Per-block scale (symmetric)
    max_abs = np.maximum(np.max(np.abs(blocks), axis=1), 1e-8)
    scales = max_abs / 7.0  # INT4 range: -7 to 7 (use -8..7 to avoid edge)
    
    # Quantize
    quantized = np.round(blocks / scales[:, None]).clip(-7, 7).astype(np.int8)
    
    # Pack 2 values per byte: high nibble = first, low nibble = second
    # Reshape to (n_blocks, block_size//2, 2) then pack
    q_pairs = quantized.reshape(n_blocks, block_size // 2, 2)
    # Convert to unsigned (0..15) for packing
    q_pairs_u = (q_pairs + 8).astype(np.uint8)
    packed = (q_pairs_u[:, :, 0] << 4) | q_pairs_u[:, :, 1]
    packed = packed.ravel().astype(np.uint8)
    
    return packed, scales.astype(np.float32)


def dequantize_int4(packed: np.ndarray, scales: np.ndarray, original_shape, block_size: int = 128) -> torch.Tensor:
    """Dequantize INT4 packed bytes back to fp32 tensor."""
    # Unpack
    high = (packed >> 4).astype(np.int8) - 8
    low = (packed & 0x0F).astype(np.int8) - 8
    flat = np.empty(len(packed) * 2, dtype=np.float32)
    flat[0::2] = high
    flat[1::2] = low
    
    # Reshape into blocks and dequantize
    n_blocks = len(scales)
    block_size = len(flat) // n_blocks
    blocks = flat.reshape(n_blocks, block_size)
    dequant = blocks * scales[:, None]
    flat_dq = dequant.ravel()
    
    # Truncate to original size
    total = 1
    for s in original_shape:
        total *= s
    return torch.from_numpy(flat_dq[:total].reshape(original_shape))


def quantize_model_int4(state_dict: Dict[str, torch.Tensor], block_size: int = 128) -> Dict:
    """Quantize entire model state dict to INT4.
    
    Returns dict with:
        'packed': {name: bytes}
        'scales': {name: float32 array}
        'shapes': {name: tuple}
        'block_size': int
    """
    packed_state: Dict[str, np.ndarray] = {}
    scales_state: Dict[str, np.ndarray] = {}
    shapes: Dict[str, tuple] = {}
    
    for name, tensor in state_dict.items():
        # Skip small tensors (LayerNorm, biases) — keep as fp32
        if tensor.numel() < 1000 or tensor.dtype != torch.float32:
            packed_state[name] = tensor.detach().cpu().numpy()
            scales_state[name] = None
            shapes[name] = tuple(tensor.shape)
            continue
        
        packed, scales = quantize_int4(tensor, block_size=block_size)
        packed_state[name] = packed
        scales_state[name] = scales
        shapes[name] = tuple(tensor.shape)
    
    return {
        'packed': packed_state,
        'scales': scales_state,
        'shapes': shapes,
        'block_size': block_size,
    }


def estimate_int4_size_bytes(quantized: Dict) -> int:
    """Estimate serialized size in bytes."""
    total = 0
    for name, packed in quantized['packed'].items():
        arr = packed if hasattr(packed, 'nbytes') else np.array(packed)
        total += arr.nbytes
        scales = quantized['scales'][name]
        if scales is not None:
            arr_s = scales if hasattr(scales, 'nbytes') else np.array(scales)
            total += arr_s.nbytes
    return total


if __name__ == "__main__":
    # Test: quantize & dequantize a tensor, measure error
    torch.manual_seed(42)
    t = torch.randn(1000, 1000) * 0.05  # typical weight scale
    
    packed, scales = quantize_int4(t)
    print(f"Original: {t.numel()*4/1024:.1f} KB")
    print(f"INT4 packed: {packed.nbytes/1024:.1f} KB + scales: {scales.nbytes/1024:.1f} KB")
    print(f"Compression: {t.numel()*4 / (packed.nbytes + scales.nbytes):.2f}x")
    
    t_dq = dequantize_int4(packed, scales, t.shape)
    err = (t - t_dq).abs().mean().item()
    rel_err = err / t.abs().mean().item()
    print(f"Mean abs error: {err:.6f} (relative: {rel_err*100:.2f}%)")
    print(f"Max abs error: {(t - t_dq).abs().max().item():.6f}")
    
    # Test full model quantization
    print("\n--- Full model test ---")
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from train_100m_v2 import ScratchGPTLarge
    
    # 40M model (compact)
    m = ScratchGPTLarge(vocab_size=1500, embed_dim=512, num_layers=12, num_heads=8,
                       max_seq_len=64, use_checkpointing=False)
    state = m.state_dict()
    orig_size = sum(v.numel() * v.element_size() for v in state.values())
    
    quant = quantize_model_int4(state)
    quant_size = estimate_int4_size_bytes(quant)
    
    p = m.count_parameters()
    print(f"Model params: {p:,} ({p/1e6:.2f}M)")
    print(f"Original (fp32): {orig_size/1024/1024:.1f} MB")
    print(f"INT4 quantized: {quant_size/1024/1024:.1f} MB")
    print(f"Compression: {orig_size/quant_size:.2f}x")
    
    # Verify dequantization works
    print("\nDequantization check:")
    name = 'token_embedding.weight'
    packed = quant['packed'][name]
    scales = quant['scales'][name]
    shape = quant['shapes'][name]
    t_dq = dequantize_int4(packed, scales, shape)
    err = (state[name] - t_dq).abs().mean().item()
    print(f"  {name}: err={err:.6f} (rel={err/state[name].abs().mean().item()*100:.2f}%)")
