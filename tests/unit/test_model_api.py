"""Tests for Model API endpoints (from-scratch AI)."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from ibr_platform.api.server import create_app
    app = create_app()
    return TestClient(app)


class TestModelInfo:
    def test_model_info_not_trained(self, client: TestClient) -> None:
        """Model info returns not_trained status when no model exists."""
        response = client.get("/api/v1/model/info")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_trained"
        assert data["pretrained"] is False

    def test_model_info_has_architecture(self, client: TestClient) -> None:
        """Model info includes architecture name."""
        response = client.get("/api/v1/model/info")
        assert response.json()["architecture"] == "ScratchGPT"


class TestModelTrain:
    def test_train_pretrain(self, client: TestClient) -> None:
        """POST /api/v1/model/train with mode=pretrain trains from scratch."""
        response = client.post("/api/v1/model/train", json={
            "texts": [
                "artificial intelligence is the future of technology and machine learning models learn from data to make predictions about the world around us",
                "neural networks process information in layers using attention mechanisms that weigh the importance of different tokens in the input sequence",
                "deep learning uses multiple hidden layers for feature extraction from raw data without manual feature engineering or domain expertise",
                "transformer architecture was introduced in two thousand seventeen and has become the dominant approach for natural language processing tasks",
            ],
            "epochs": 3,
            "mode": "pretrain",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["mode"] == "pretrain"
        assert data["pretrained"] is False
        assert "initial_loss" in data
        assert "final_loss" in data

    def test_train_finetune_without_pretrain_raises(self, client: TestClient) -> None:
        """POST /api/v1/model/train with mode=finetune without pretrain raises 400."""
        response = client.post("/api/v1/model/train", json={
            "texts": ["test"],
            "mode": "finetune",
        })
        assert response.status_code == 400

    def test_train_finetune_after_pretrain(self, client: TestClient) -> None:
        """Fine-tune works after pretraining."""
        # Pretrain first with enough data to generate sequences
        client.post("/api/v1/model/train", json={
            "texts": [
                "hello world this is a test of the model training system for natural language processing",
                "the quick brown fox jumps over the lazy dog in the morning sun shining brightly",
                "machine learning models can be trained on large datasets to make accurate predictions",
            ],
            "epochs": 2,
            "mode": "pretrain",
        })
        # Fine-tune
        response = client.post("/api/v1/model/train", json={
            "texts": [
                "the ibr platform is an autonomous ai system for research and development",
                "this fine tuning data helps the model learn new patterns and behaviors",
            ],
            "epochs": 2,
            "mode": "finetune",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "finetune"
        assert data["status"] == "complete"


class TestModelGenerate:
    def test_generate_without_training_raises(self, client: TestClient) -> None:
        """POST /api/v1/model/generate without training raises 400."""
        response = client.post("/api/v1/model/generate", json={
            "prompt": "hello",
        })
        assert response.status_code == 400

    def test_generate_after_training(self, client: TestClient) -> None:
        """Generate works after training and returns text."""
        # Train first with enough data to generate sequences
        client.post("/api/v1/model/train", json={
            "texts": [
                "artificial intelligence is transforming the world of technology and computing today",
                "machine learning enables computers to learn from data without explicit programming",
                "deep learning uses neural networks with many layers to process complex patterns",
                "natural language processing helps computers understand human language and text",
            ],
            "epochs": 3,
            "mode": "pretrain",
        })
        # Generate
        response = client.post("/api/v1/model/generate", json={
            "prompt": "artificial",
            "max_new_tokens": 10,
            "temperature": 0.5,
        })
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert len(data["text"]) > 0
        assert data["model"] == "ScratchGPT"
        assert data["pretrained"] is False

    def test_generate_with_custom_params(self, client: TestClient) -> None:
        """Generate accepts custom temperature and max_tokens."""
        client.post("/api/v1/model/train", json={
            "texts": [
                "test data for model training and generation of new text sequences here in this long sentence",
                "this is additional training data to ensure enough tokens are available for the model",
                "we need multiple long sentences so that the bpe tokenizer can learn patterns from the data",
                "the quick brown fox jumps over the lazy dog while the sun shines brightly in the sky above",
            ],
            "epochs": 2,
            "mode": "pretrain",
        })
        response = client.post("/api/v1/model/generate", json={
            "prompt": "test",
            "max_new_tokens": 5,
            "temperature": 1.0,
        })
        assert response.status_code == 200


class TestModelInfoAfterTraining:
    def test_model_info_shows_trained(self, client: TestClient) -> None:
        """After training, model info shows trained status with params."""
        client.post("/api/v1/model/train", json={
            "texts": [
                "the ibr platform is an autonomous ai research system that conducts research and builds models from scratch without any pre trained weights at all",
                "it uses free data sources like wikipedia and arxiv to gather knowledge and trains transformer models on cpu without requiring expensive gpu hardware",
                "the platform includes a bpe tokenizer built from scratch and a transformer architecture with multi head self attention and layer normalization",
                "all training is done using pytorch on commodity cpu hardware making ai accessible to everyone without the need for paid apis or expensive infrastructure",
            ],
            "epochs": 2,
            "mode": "pretrain",
        })
        response = client.get("/api/v1/model/info")
        data = response.json()
        assert data["status"] == "trained"
        assert data["total_params"] > 0
        assert data["is_trained"] is True
        assert data["pretrained"] is False
