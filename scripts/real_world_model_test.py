#!/usr/bin/env python3
"""
IBR Platform — Real World Model Test
Downloads a real pre-trained model (distilgpt2, ~85M params, FREE),
runs real inference, and implements real fine-tuning with PyTorch.

This is NOT a simulation — actual model weights are downloaded from HuggingFace
and actual training occurs with real loss computation.

Model: distilgpt2 (85M params, ~340MB in FP32)
  - FREE (Apache 2.0 license)
  - Small enough for CPU (runs in <2GB RAM)
  - Real GPT-2 architecture (distilled)
  - Can generate real text
  - Can be fine-tuned on CPU in minutes
"""
import os
import sys
import time
import json
import torch
import numpy as np
from datetime import datetime, timezone

RESULTS = {}

def log(name, value):
    RESULTS[name] = value
    print(f"  [RESULT] {name}: {value}")

print("=" * 70)
print("IBR PLATFORM — REAL WORLD MODEL TEST")
print("=" * 70)
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"Device: CPU (CPU-first strategy)")
print()

# ============================================
# STEP 1: Download Real Pre-trained Model
# ============================================
print("=" * 70)
print("STEP 1: Download Real Pre-trained Model (distilgpt2)")
print("=" * 70)
print("Model: distilgpt2 (85M parameters, distilled GPT-2)")
print("License: Apache 2.0 (FREE, open source)")
print("Source: HuggingFace Hub (free download)")
print()

from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "distilgpt2"

print(f"Downloading {model_name} from HuggingFace...")
t0 = time.perf_counter()

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

download_time = time.perf_counter() - t0
log("model_name", model_name)
log("model_download_time_seconds", round(download_time, 2))

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log("model_total_params", total_params)
log("model_trainable_params", trainable_params)
log("model_size_mb", round(total_params * 4 / 1024 / 1024, 2))  # FP32 = 4 bytes

print(f"  Downloaded in {download_time:.2f}s")
print(f"  Total parameters: {total_params:,}")
print(f"  Trainable parameters: {trainable_params:,}")
print(f"  Model size (FP32): {total_params * 4 / 1024 / 1024:.2f} MB")

# Set pad token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ============================================
# STEP 2: Real Inference (Text Generation)
# ============================================
print("\n" + "=" * 70)
print("STEP 2: Real Inference — Text Generation on CPU")
print("=" * 70)

prompts = [
    "The future of artificial intelligence is",
    "Machine learning models can be",
    "Python is a programming language that",
]

model.eval()

for prompt in prompts:
    print(f"\n  Prompt: '{prompt}'")
    t0 = time.perf_counter()

    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=30,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )

    inference_time = time.perf_counter() - t0
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    tokens_generated = len(outputs[0]) - len(inputs["input_ids"][0])
    tokens_per_sec = tokens_generated / inference_time if inference_time > 0 else 0

    log(f"inference_time_{prompt[:20].replace(' ', '_')}", round(inference_time, 3))
    log(f"inference_tokens_per_sec_{prompt[:20].replace(' ', '_')}", round(tokens_per_sec, 2))
    log(f"inference_output_{prompt[:20].replace(' ', '_')}", generated_text)

    print(f"  Generated: '{generated_text}'")
    print(f"  Time: {inference_time:.3f}s | Tokens: {tokens_generated} | Rate: {tokens_per_sec:.2f} tok/s")

# ============================================
# STEP 3: Real Fine-Tuning (SFT with PyTorch)
# ============================================
print("\n" + "=" * 70)
print("STEP 3: Real Fine-Tuning — Supervised Fine-Tuning (SFT)")
print("=" * 70)

# Create a small training dataset (FREE — synthetic data)
training_data = [
    "The IBR Platform is an autonomous AI research system.",
    "Artificial intelligence transforms how we process information.",
    "Machine learning models learn patterns from training data.",
    "Deep learning uses neural networks with multiple layers.",
    "Natural language processing helps computers understand text.",
    "Transformers are a type of neural network architecture.",
    "Fine-tuning adapts a pre-trained model to specific tasks.",
    "Quantization reduces model size with minimal quality loss.",
    "Vector databases enable similarity search at scale.",
    "Knowledge graphs store entities and their relationships.",
    "Retrieval augmented generation improves factual accuracy.",
    "Multi-agent systems coordinate specialized AI agents.",
    "Reinforcement learning trains models through rewards.",
    "Data quality matters more than data quantity for training.",
    "CPU-first deployment makes AI accessible on commodity hardware.",
]

print(f"Training dataset: {len(training_data)} examples (synthetic, FREE)")
print(f"Training method: Supervised Fine-Tuning (SFT)")
print(f"Optimizer: AdamW (learning_rate=5e-5)")
print(f"Epochs: 3")
print(f"Device: CPU")
print()

# Prepare training data
def encode_text(texts, tokenizer, max_length=64):
    encodings = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt",
    )
    return encodings

# Training configuration
learning_rate = 5e-5
epochs = 3
batch_size = 4

# Enable training mode
model.train()
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

# Training loop
all_losses = []
t0 = time.perf_counter()

for epoch in range(epochs):
    epoch_losses = []

    # Process in mini-batches
    for i in range(0, len(training_data), batch_size):
        batch = training_data[i:i + batch_size]
        encodings = encode_text(batch, tokenizer)

        # Forward pass
        outputs = model(**encodings, labels=encodings["input_ids"])
        loss = outputs.loss

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_losses.append(loss.item())

    avg_loss = np.mean(epoch_losses)
    all_losses.append(avg_loss)
    print(f"  Epoch {epoch + 1}/{epochs} — Loss: {avg_loss:.4f}")

training_time = time.perf_counter() - t0
log("finetuning_epochs", epochs)
log("finetuning_training_examples", len(training_data))
log("finetuning_learning_rate", learning_rate)
log("finetuning_initial_loss", round(all_losses[0], 4))
log("finetuning_final_loss", round(all_losses[-1], 4))
log("finetuning_loss_reduction", round(all_losses[0] - all_losses[-1], 4))
log("finetuning_loss_reduction_pct", round((all_losses[0] - all_losses[-1]) / all_losses[0] * 100, 2))
log("finetuning_training_time_seconds", round(training_time, 2))

print(f"\n  Training complete in {training_time:.2f}s")
print(f"  Initial loss: {all_losses[0]:.4f}")
print(f"  Final loss: {all_losses[-1]:.4f}")
print(f"  Loss reduction: {((all_losses[0] - all_losses[-1]) / all_losses[0] * 100):.2f}%")

# ============================================
# STEP 4: Post-Fine-Tuning Inference
# ============================================
print("\n" + "=" * 70)
print("STEP 4: Post-Fine-Tuning Inference")
print("=" * 70)

model.eval()

test_prompt = "The IBR Platform is"
print(f"\n  Prompt: '{test_prompt}'")

inputs = tokenizer(test_prompt, return_tensors="pt")
t0 = time.perf_counter()

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=30,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id,
    )

post_ft_time = time.perf_counter() - t0
post_ft_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
log("post_finetuning_output", post_ft_text)
log("post_finetuning_inference_time", round(post_ft_time, 3))

print(f"  Generated: '{post_ft_text}'")
print(f"  Time: {post_ft_time:.3f}s")

# ============================================
# STEP 5: Quantization Simulation (INT8)
# ============================================
print("\n" + "=" * 70)
print("STEP 5: Quantization — INT8 Simulation")
print("=" * 70)

# Get model weights
weights = model.transformer.h[0].mlp.c_fc.weight.data.numpy()
log("quantization_original_shape", str(weights.shape))
log("quantization_original_size_mb", round(weights.nbytes / 1024 / 1024, 4))

# INT8 quantization
scale = np.abs(weights).max() / 127.0
int8_weights = np.round(weights / scale).clip(-127, 127).astype(np.int8)
log("quantization_int8_size_mb", round(int8_weights.nbytes / 1024 / 1024, 4))
log("quantization_compression_ratio", round(weights.nbytes / int8_weights.nbytes, 2))

# Dequantize and compute MSE
reconstructed = int8_weights.astype(np.float32) * scale
mse = np.mean((weights - reconstructed) ** 2)
log("quantization_int8_mse", round(float(mse), 8))

print(f"  Original size: {weights.nbytes / 1024 / 1024:.4f} MB (FP32)")
print(f"  INT8 size: {int8_weights.nbytes / 1024 / 1024:.4f} MB")
print(f"  Compression ratio: {weights.nbytes / int8_weights.nbytes:.2f}x")
print(f"  MSE: {mse:.8f}")

# ============================================
# STEP 6: Benchmark Summary
# ============================================
print("\n" + "=" * 70)
print("STEP 6: Benchmark Summary")
print("=" * 70)

# Inference benchmark
benchmark_prompt = "Artificial intelligence"
inputs = tokenizer(benchmark_prompt, return_tensors="pt")

times = []
for _ in range(5):
    t0 = time.perf_counter()
    with torch.no_grad():
        _ = model.generate(**inputs, max_new_tokens=10, do_sample=False, pad_token_id=tokenizer.pad_token_id)
    times.append(time.perf_counter() - t0)

avg_time = np.mean(times)
p99_time = np.percentile(times, 99)
log("benchmark_avg_inference_ms", round(avg_time * 1000, 2))
log("benchmark_p99_inference_ms", round(p99_time * 1000, 2))
log("benchmark_tokens_per_sec_avg", round(10 / avg_time, 2))

print(f"  Avg inference (10 tokens): {avg_time * 1000:.2f}ms")
print(f"  P99 inference: {p99_time * 1000:.2f}ms")
print(f"  Tokens/sec: {10 / avg_time:.2f}")

# ============================================
# Save Results
# ============================================
results_path = "/my-project/research/real_world_model_results.json"
with open(results_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)

print("\n" + "=" * 70)
print(f"ALL TESTS COMPLETE — {len(RESULTS)} measurements saved")
print(f"Results: {results_path}")
print("=" * 70)
print("\nKEY FINDINGS:")
print(f"  Model: {model_name} ({total_params:,} params, {total_params * 4 / 1024 / 1024:.1f} MB)")
print(f"  Inference: ~{10 / avg_time:.1f} tokens/sec on CPU")
print(f"  Fine-tuning: {all_losses[0]:.4f} → {all_losses[-1]:.4f} ({((all_losses[0] - all_losses[-1]) / all_losses[0] * 100):.1f}% reduction)")
print(f"  Quantization: 4.00x compression with MSE {mse:.8f}")
print(f"  ALL FREE — no paid APIs, no GPU required")
