"""Tests for Section 20 — APIs (FastAPI REST endpoints)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from ibr_platform.api.server import create_app
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_has_timestamp(self, client: TestClient) -> None:
        response = client.get("/health")
        assert "timestamp" in response.json()


class TestArchitectureEndpoint:
    def test_get_architecture(self, client: TestClient) -> None:
        response = client.get("/api/v1/architecture")
        assert response.status_code == 200
        data = response.json()
        assert "layers" in data
        assert len(data["layers"]) == 10


class TestResearchEndpoints:
    def test_submit_research(self, client: TestClient) -> None:
        response = client.post("/api/v1/research", json={
            "query": "What is machine learning?",
            "user_id": "test_user",
        })
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"

    def test_submit_empty_query_raises_400(self, client: TestClient) -> None:
        response = client.post("/api/v1/research", json={"query": ""})
        assert response.status_code == 400

    def test_get_research_result(self, client: TestClient) -> None:
        # Submit first
        submit = client.post("/api/v1/research", json={"query": "test query"})
        request_id = submit.json()["request_id"]
        # Get result
        response = client.get(f"/api/v1/research/{request_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == request_id
        assert data["query"] == "test query"

    def test_get_nonexistent_research_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/research/nonexistent-id")
        assert response.status_code == 404

    def test_list_research_requests(self, client: TestClient) -> None:
        client.post("/api/v1/research", json={"query": "query 1"})
        client.post("/api/v1/research", json={"query": "query 2"})
        response = client.get("/api/v1/research")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2


class TestMemoryEndpoints:
    def test_write_memory(self, client: TestClient) -> None:
        response = client.post("/api/v1/memory/write", json={
            "content": "Test memory content",
            "tier": "long_term",
            "scope": "project",
            "scope_id": "proj1",
            "confidence": 0.9,
        })
        assert response.status_code == 200
        assert "memory_id" in response.json()

    def test_search_memory(self, client: TestClient) -> None:
        # Write first
        client.post("/api/v1/memory/write", json={
            "content": "machine learning basics",
            "tier": "long_term",
            "scope": "project",
            "scope_id": "proj1",
        })
        # Search
        response = client.post("/api/v1/memory/search", json={
            "query": "machine",
            "scope": "project",
            "scope_id": "proj1",
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "machine" in data[0]["content"].lower()

    def test_read_memory(self, client: TestClient) -> None:
        # Write
        write_resp = client.post("/api/v1/memory/write", json={
            "content": "Read me",
            "tier": "long_term",
            "scope": "project",
            "scope_id": "p1",
        })
        memory_id = write_resp.json()["memory_id"]
        # Read
        response = client.get(f"/api/v1/memory/{memory_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Read me"

    def test_read_nonexistent_memory_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/memory/nonexistent")
        assert response.status_code == 404

    def test_delete_memory(self, client: TestClient) -> None:
        # Write
        write_resp = client.post("/api/v1/memory/write", json={
            "content": "Delete me",
            "tier": "working",
            "scope": "project",
            "scope_id": "p1",
        })
        memory_id = write_resp.json()["memory_id"]
        # Delete
        response = client.delete(f"/api/v1/memory/{memory_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True
        # Verify deleted
        response = client.get(f"/api/v1/memory/{memory_id}")
        assert response.status_code == 404

    def test_memory_stats(self, client: TestClient) -> None:
        client.post("/api/v1/memory/write", json={
            "content": "stat test",
            "tier": "long_term",
            "scope": "project",
            "scope_id": "p1",
        })
        response = client.get("/api/v1/memory/stats")
        assert response.status_code == 200
        data = response.json()
        assert "long_term" in data


class TestOrchestratorHealth:
    def test_orchestrator_health(self, client: TestClient) -> None:
        response = client.get("/api/v1/orchestrator/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_requests" in data
        assert "total_requests" in data


class TestAPIsDocs:
    def test_swagger_docs_available(self, client: TestClient) -> None:
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_spec_available(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "IBR Platform API"
        assert data["info"]["version"] == "0.1.0"
