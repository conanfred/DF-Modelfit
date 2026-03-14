"""Tests pour api/runtimes.py — détection et gestion des runtimes IA."""
from unittest.mock import patch, MagicMock
from api.runtimes import (
    RuntimeInfo,
    LocalModel,
    detect_ollama,
    detect_lmstudio,
    detect_llamacpp,
    detect_all_runtimes,
    list_all_local_models,
    match_local_to_hf,
)


class TestRuntimeInfo:
    def test_dataclass_fields(self):
        rt = RuntimeInfo(
            name="test", installed=True, running=False,
        )
        assert rt.name == "test"
        assert rt.installed is True
        assert rt.running is False
        assert rt.version is None
        assert rt.models_count == 0


class TestLocalModel:
    def test_dataclass_fields(self):
        m = LocalModel(name="llama3:8b", runtime="ollama")
        assert m.name == "llama3:8b"
        assert m.runtime == "ollama"
        assert m.size_gb is None


class TestDetectOllama:
    @patch("api.runtimes.shutil.which", return_value=None)
    @patch("api.runtimes._http_get_json", return_value=None)
    def test_not_installed(self, mock_http, mock_which):
        info = detect_ollama()
        assert info.name == "Ollama"
        assert info.installed is False
        assert info.running is False

    @patch("api.runtimes.shutil.which", return_value="/usr/bin/ollama")
    @patch("api.runtimes._http_get_json")
    def test_installed_running(self, mock_http, mock_which):
        def side_effect(url, **kwargs):
            if "version" in url:
                return {"version": "0.5.0"}
            if "tags" in url:
                return {"models": [
                    {"name": "llama3:8b", "size": 4_000_000_000},
                ]}
            return None
        mock_http.side_effect = side_effect
        info = detect_ollama()
        assert info.installed is True
        assert info.running is True
        assert info.version == "0.5.0"
        assert info.models_count == 1

    @patch("api.runtimes.shutil.which", return_value="/usr/bin/ollama")
    @patch("api.runtimes._http_get_json", return_value=None)
    @patch("api.runtimes.subprocess.run")
    def test_installed_not_running(self, mock_run, mock_http, mock_which):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ollama version 0.4.0"
        )
        info = detect_ollama()
        assert info.installed is True
        assert info.running is False
        assert info.error is not None


class TestDetectLmStudio:
    @patch("api.runtimes._http_get_json", return_value=None)
    def test_not_running(self, mock_http):
        info = detect_lmstudio()
        assert info.name == "LM Studio"
        assert info.running is False

    @patch("api.runtimes._http_get_json")
    def test_running(self, mock_http):
        mock_http.return_value = {
            "data": [{"id": "model1"}, {"id": "model2"}]
        }
        info = detect_lmstudio()
        assert info.running is True
        assert info.models_count == 2


class TestDetectLlamaCpp:
    @patch("api.runtimes.shutil.which", return_value=None)
    @patch("api.runtimes._http_get_json", return_value=None)
    def test_not_installed(self, mock_http, mock_which):
        info = detect_llamacpp()
        assert info.name == "llama.cpp"
        assert info.installed is False


class TestDetectAllRuntimes:
    @patch("api.runtimes.detect_ollama")
    @patch("api.runtimes.detect_lmstudio")
    @patch("api.runtimes.detect_llamacpp")
    def test_returns_list(self, mock_llama, mock_lms, mock_ollama):
        mock_ollama.return_value = RuntimeInfo(
            name="Ollama", installed=True, running=True,
        )
        mock_lms.return_value = RuntimeInfo(
            name="LM Studio", installed=False, running=False,
        )
        mock_llama.return_value = RuntimeInfo(
            name="llama.cpp", installed=False, running=False,
        )
        result = detect_all_runtimes()
        assert len(result) == 3
        assert result[0]["name"] == "Ollama"
        assert result[0]["installed"] is True


class TestMatchLocalToHf:
    def test_matching(self):
        local = [
            {"name": "llama3.2:3b", "runtime": "ollama"},
            {"name": "mistral:7b", "runtime": "ollama"},
        ]
        hf = [
            {"name": "meta-llama/Llama-3.2-3B"},
            {"name": "mistralai/Mistral-7B-Instruct"},
            {"name": "microsoft/Phi-3.5-mini"},
        ]
        matched = match_local_to_hf(local, hf)
        assert len(matched) >= 1

    def test_no_matches(self):
        local = [{"name": "custom-model:latest", "runtime": "ollama"}]
        hf = [{"name": "totally/different-model"}]
        matched = match_local_to_hf(local, hf)
        assert len(matched) == 0

    def test_empty_inputs(self):
        assert match_local_to_hf([], []) == {}
        assert match_local_to_hf([], [{"name": "a/b"}]) == {}


class TestListAllLocalModels:
    @patch("api.runtimes.ollama_list_models", return_value=[])
    @patch("api.runtimes.lmstudio_list_models", return_value=[])
    def test_empty(self, mock_lms, mock_ollama):
        result = list_all_local_models()
        assert result == []

    @patch("api.runtimes.ollama_list_models")
    @patch("api.runtimes.lmstudio_list_models", return_value=[])
    def test_with_ollama_models(self, mock_lms, mock_ollama):
        mock_ollama.return_value = [
            LocalModel(
                name="llama3:8b", runtime="ollama",
                size_gb=4.0, quantization="Q4_K_M",
            ),
        ]
        result = list_all_local_models()
        assert len(result) == 1
        assert result[0]["name"] == "llama3:8b"
        assert result[0]["size_gb"] == 4.0
