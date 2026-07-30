"""
Models package — Real model management (PRD Section 39, 46).

Includes both:
1. RealModelManager: Uses pre-trained distilgpt2 from HuggingFace (FREE)
2. ScratchModelManager: Builds a Transformer completely from scratch (NO pre-trained)
"""

from ibr_platform.models.manager import FineTuningResult, InferenceResult, RealModelManager
from ibr_platform.models.scratch import (
    BPETokenizer,
    MultiHeadSelfAttention,
    ScratchGPT,
    ScratchModelManager,
    TransformerBlock,
)

__all__ = [
    "BPETokenizer",
    "FineTuningResult",
    "InferenceResult",
    "MultiHeadSelfAttention",
    "RealModelManager",
    "ScratchGPT",
    "ScratchModelManager",
    "TransformerBlock",
]