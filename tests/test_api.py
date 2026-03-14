"""Tests pour les routes API de main.py (FastAPI TestClient)."""
import json

import pytest
from fastapi.testclient import TestClient

from main import app, MODELS, load_models


@pytest.fixture(autouse=True)
def _load_models():
    """Charge les modèles avant chaque test."""
    import main
    main.MODELS = load_models()


client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["app"] == "DF Modelfit"


class TestSystem:
    def test_system_returns_specs(self):
        resp = client.get("/api/system")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_ram_gb" in data
        assert "cpu_cores" in data
        assert "backend" in data
        assert data["total_ram_gb"] > 0

    def test_system_custom(self):
        body = {
            "total_ram_gb": 64.0,
            "cpu_cores": 16,
            "gpu_vram_gb": 24.0,
            "backend": "cuda",
        }
        resp = client.post("/api/system/custom", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["custom"] is True
        assert data["system"]["total_ram_gb"] == 64.0
        assert data["system"]["has_gpu"] is True
        assert len(data["models"]) > 0

    def test_system_custom_validation_error(self):
        body = {"total_ram_gb": -1, "cpu_cores": 0}
        resp = client.post("/api/system/custom", json=body)
        assert resp.status_code == 422


class TestModels:
    def test_models_returns_list(self):
        resp = client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "system" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0

    def test_models_search_filter(self):
        resp = client.get("/api/models?search=llama")
        assert resp.status_code == 200
        data = resp.json()
        for m in data["models"]:
            name = (m["model"]["name"] or "").lower()
            provider = (m["model"]["provider"] or "").lower()
            assert "llama" in name or "llama" in provider

    def test_models_fit_filter(self):
        resp = client.get("/api/models?fit=parfait")
        assert resp.status_code == 200
        data = resp.json()
        for m in data["models"]:
            assert m["fit_level"] == "parfait"


class TestModelsTop:
    def test_top_returns_runnable(self):
        resp = client.get("/api/models/top?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["models"]) <= 5
        for m in data["models"]:
            assert m["fit_level"] != "trop_juste"


class TestRecommend:
    def test_recommend_default(self):
        resp = client.get("/api/recommend")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) <= 20

    def test_recommend_with_use_case(self):
        resp = client.get("/api/recommend?use_case=chat&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["models"]) <= 5

    def test_recommend_with_params_filter(self):
        resp = client.get("/api/recommend?max_params=3&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        for m in data["models"]:
            params_raw = m["model"].get("parameters_raw")
            if params_raw:
                assert params_raw / 1e9 <= 3.0


class TestExport:
    def test_export_json(self):
        resp = client.get("/api/export/json")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "fit_level" in data[0]

    def test_export_csv(self):
        resp = client.get("/api/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        lines = resp.text.strip().split("\n")
        assert len(lines) > 1
        headers = lines[0].split(",")
        assert "name" in headers[0]


class TestChangelog:
    def test_changelog_returns_entries(self):
        resp = client.get("/api/changelog")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)


class TestStaticPages:
    def test_index_page(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "DF Modelfit" in resp.text

    def test_license_page(self):
        resp = client.get("/license")
        assert resp.status_code == 200


class TestRefreshRateLimit:
    def test_refresh_rate_limit(self):
        import main
        main._refresh_last_by_ip["testclient"] = __import__("time").time()
        resp = client.post("/api/refresh")
        assert resp.status_code == 429
        main._refresh_last_by_ip.clear()
