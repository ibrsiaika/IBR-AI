"""
IBR Platform CLI — Command-line interface for the IBR Platform.

Provides commands for training, generating, inspecting, and serving
the from-scratch IBR-GPT-Code model.

Usage:
    ibr --help
    ibr train --data code.txt --epochs 10 --output model.pt
    ibr generate --model model.pt --prompt "def hello" --max-tokens 30
    ibr info --model model.pt
    ibr serve --host 0.0.0.0 --port 8000
    ibr version

The `ibr` console script is declared in pyproject.toml as:
    [project.scripts]
    ibr = "ibr_platform.cli:main"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click


@click.group(invoke_without_command=True)
@click.version_option(package_name="ibr-platform", prog_name="ibr")
@click.pass_context
def main(ctx: click.Context) -> None:
    """IBR Platform CLI — train, generate, and serve the from-scratch IBR-GPT-Code model.

    A from-scratch Transformer language model. No pre-trained weights.
    All training and inference on CPU.

    Quick start:
        ibr train --data code.txt --epochs 10 --output model.pt
        ibr generate --model model.pt --prompt "def scan"
        ibr info --model model.pt
        ibr serve

    See: https://github.com/ibrsiaika/IBR-AI
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option("--data", required=True, type=click.Path(exists=True, dir_okay=False),
              help="Path to training data (text file, one doc per line, or .json list of strings).")
@click.option("--epochs", default=10, show_default=True, type=int,
              help="Number of training epochs.")
@click.option("--output", "-o", default="model.pt", show_default=True, type=click.Path(dir_okay=False),
              help="Path to save the trained model.")
@click.option("--mode", default="pretrain", show_default=True,
              type=click.Choice(["pretrain", "finetune"]),
              help="Training mode: pretrain (from scratch) or finetune (extend an existing model).")
@click.option("--lr", default=3e-4, show_default=True, type=float,
              help="Learning rate.")
@click.option("--batch-size", default=8, show_default=True, type=int,
              help="Mini-batch size.")
@click.option("--seq-len", default=64, show_default=True, type=int,
              help="Sequence length.")
@click.option("--vocab-size", default=1000, show_default=True, type=int,
              help="BPE vocabulary size.")
def train(data: str, epochs: int, output: str, mode: str,
          lr: float, batch_size: int, seq_len: int, vocab_size: int) -> None:
    """Train the from-scratch IBR-GPT-Code model.

    Loads training data, builds a BPE tokenizer from scratch, builds a
    Transformer from scratch (random init), and trains it.

    Example:
        ibr train --data code.txt --epochs 10 --output model.pt
    """
    from ibr_platform.models.scratch import ScratchModelManager

    # Load data
    click.echo(f"Loading data from: {data}")
    texts = _load_training_data(data)
    click.echo(f"  {len(texts)} samples loaded")

    if mode == "finetune" and not Path(output).exists():
        raise click.ClickException(
            f"Finetune mode requires an existing model at --output path. "
            f"Run `ibr train --mode pretrain` first."
        )

    # Build manager
    mgr = ScratchModelManager(
        embed_dim=128, num_layers=4, num_heads=4,
        max_seq_len=seq_len, vocab_size=vocab_size,
    )

    if mode == "pretrain":
        click.echo(f"Pre-training from scratch ({epochs} epochs, lr={lr})...")
        result = mgr.pretrain(texts, epochs=epochs, learning_rate=lr,
                              batch_size=batch_size, seq_len=seq_len)
    else:
        # Finetune: load existing model first
        click.echo(f"Loading existing model from {output}...")
        mgr.load(output)
        click.echo(f"Fine-tuning ({epochs} epochs, lr={lr})...")
        result = mgr.fine_tune(texts, epochs=epochs, learning_rate=lr,
                               batch_size=batch_size, seq_len=seq_len)

    if "error" in result:
        raise click.ClickException(f"Training failed: {result['error']}")

    click.echo(f"\nTraining complete:")
    click.echo(f"  Initial loss: {result.get('initial_loss', 0):.4f}")
    click.echo(f"  Final loss:   {result.get('final_loss', 0):.4f}")
    if result.get("initial_loss", 0) > 0:
        reduction = (result["initial_loss"] - result["final_loss"]) / result["initial_loss"] * 100
        click.echo(f"  Reduction:    {reduction:.1f}%")
    click.echo(f"  Time:         {result.get('training_time_seconds', 0):.1f}s")

    # Save
    mgr.save(output)
    click.echo(f"\nModel saved to: {output}")


@main.command()
@click.option("--model", required=True, type=click.Path(exists=True, dir_okay=False),
              help="Path to trained model file (.pt).")
@click.option("--prompt", required=True, type=str,
              help="Text prompt to condition generation.")
@click.option("--max-tokens", default=30, show_default=True, type=int,
              help="Maximum tokens to generate.")
@click.option("--temperature", default=0.8, show_default=True, type=float,
              help="Sampling temperature (lower = more deterministic).")
@click.option("--top-k", default=None, type=int,
              help="If set, restrict sampling to top-K tokens.")
def generate(model: str, prompt: str, max_tokens: int, temperature: float, top_k: int | None) -> None:
    """Generate text from a trained model.

    Example:
        ibr generate --model model.pt --prompt "def hello" --max-tokens 30
    """
    from ibr_platform.models.scratch import ScratchModelManager

    click.echo(f"Loading model: {model}", err=True)
    mgr = ScratchModelManager()
    mgr.load(model)

    click.echo(f"Generating (max_tokens={max_tokens}, temp={temperature})...", err=True)
    text = mgr.generate(prompt, max_new_tokens=max_tokens,
                        temperature=temperature, top_k=top_k)
    click.echo(text)


@main.command()
@click.option("--model", required=True, type=click.Path(exists=True, dir_okay=False),
              help="Path to trained model file (.pt).")
def info(model: str) -> None:
    """Show model info: parameters, architecture, training history.

    Example:
        ibr info --model model.pt
    """
    import torch

    click.echo(f"Model: {model}")
    click.echo(f"Size:  {Path(model).stat().st_size / 1024 / 1024:.2f} MB")

    try:
        ckpt = torch.load(model, map_location='cpu', weights_only=False)
    except Exception as e:
        click.echo(f"Could not load checkpoint: {e}")
        return

    cfg = ckpt.get('model_config', {})
    meta = ckpt.get('meta', {})
    training = ckpt.get('training', [])

    click.echo(f"\nArchitecture:")
    click.echo(f"  Name:        {meta.get('name', 'unknown')}")
    click.echo(f"  Pretrained:  {meta.get('pretrained', 'unknown')}")
    click.echo(f"  Vocab size:  {cfg.get('vocab_size', '?')}")
    click.echo(f"  Embed dim:   {cfg.get('embed_dim', '?')}")
    click.echo(f"  Layers:      {cfg.get('num_layers', '?')}")
    click.echo(f"  Heads:       {cfg.get('num_heads', '?')}")
    click.echo(f"  Max seq:     {cfg.get('max_seq_len', '?')}")
    click.echo(f"  Params:      {meta.get('params', '?'):,}" if isinstance(meta.get('params'), int) else f"  Params:      ?")

    if training:
        click.echo(f"\nTraining history ({len(training)} epochs):")
        for i, loss in enumerate(training):
            click.echo(f"  Epoch {i+1}: loss={loss:.4f}")
        if len(training) >= 2:
            reduction = (training[0] - training[-1]) / training[0] * 100
            click.echo(f"\n  Loss reduction: {training[0]:.4f} -> {training[-1]:.4f} ({reduction:.1f}%)")


@main.command()
@click.option("--host", default="0.0.0.0", show_default=True,
              help="Bind host for the API server.")
@click.option("--port", default=8000, show_default=True, type=int,
              help="Bind port for the API server.")
def serve(host: str, port: int) -> None:
    """Start the FastAPI REST API server.

    Exposes endpoints:
      GET  /health
      GET  /api/v1/architecture
      POST /api/v1/model/train
      POST /api/v1/model/generate
      GET  /api/v1/model/info

    Example:
        ibr serve --port 8000
    """
    try:
        import uvicorn
    except ImportError:
        raise click.ClickException(
            "uvicorn is not installed. Install with: pip install 'ibr-platform[api]'"
        )

    click.echo(f"Starting API server on http://{host}:{port}")
    click.echo(f"  Docs:    http://{host}:{port}/docs")
    click.echo(f"  Health:  http://{host}:{port}/health")
    uvicorn.run("ibr_platform.api.server:app", host=host, port=port, reload=False)


@main.command()
def version() -> None:
    """Print version and environment info."""
    import torch

    try:
        from ibr_platform import __version__ as pkg_version
    except ImportError:
        pkg_version = "0.1.0"

    click.echo(f"ibr-platform: {pkg_version}")
    click.echo(f"python:       {sys.version.split()[0]}")
    click.echo(f"torch:        {torch.__version__}")
    click.echo(f"threads:      {torch.get_num_threads()}")


# ============================================
# Helpers
# ============================================

def _load_training_data(path: str) -> list[str]:
    """Load training texts from a file.

    Supports:
      - .txt: one document per line (empty lines skipped)
      - .json: a JSON list of strings
    """
    p = Path(path)
    if p.suffix == ".json":
        with open(p) as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"JSON file must contain a list of strings, got {type(data)}")
        return [str(s) for s in data if str(s).strip()]
    # Default: text file, one doc per line
    with open(p) as f:
        return [line.strip() for line in f if line.strip()]


if __name__ == "__main__":
    main()
