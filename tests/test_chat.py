"""Tests pour api/chat.py — chat avec modèles IA locaux."""
from unittest.mock import patch, MagicMock
from api.chat import (
    ollama_is_available,
    ollama_list_chat_models,
    get_model_defaults,
    get_system_presets,
)


class TestOllamaIsAvailable:
    @patch("api.chat.urllib.request.urlopen")
    def test_available(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        assert ollama_is_available() is True

    @patch("api.chat.urllib.request.urlopen",
           side_effect=Exception("refused"))
    def test_not_available(self, mock_urlopen):
        assert ollama_is_available() is False


class TestOllamaListChatModels:
    @patch("api.chat.urllib.request.urlopen")
    def test_returns_models(self, mock_urlopen):
        import json
        data = {
            "models": [
                {
                    "name": "llama3:8b",
                    "size": 4_000_000_000,
                    "details": {
                        "family": "llama",
                        "parameter_size": "8B",
                        "quantization_level": "Q4_K_M",
                        "families": ["llama"],
                    },
                },
                {
                    "name": "llava:7b",
                    "size": 4_500_000_000,
                    "details": {
                        "family": "llava",
                        "parameter_size": "7B",
                        "families": ["llama", "clip"],
                    },
                },
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        result = ollama_list_chat_models()
        assert len(result) == 2
        assert result[0]["name"] == "llama3:8b"
        assert result[0]["supports_vision"] is False
        assert result[1]["name"] == "llava:7b"
        assert result[1]["supports_vision"] is True

    @patch("api.chat.urllib.request.urlopen",
           side_effect=Exception("connection refused"))
    def test_returns_empty_on_error(self, mock_urlopen):
        assert ollama_list_chat_models() == []


class TestGetModelDefaults:
    def test_code_model_lower_temp(self):
        model_info = {"family": "phi3", "supports_code": True, "supports_vision": False}
        defaults = get_model_defaults(model_info)
        assert defaults["temperature"] == 0.3
        assert defaults["suggested_preset"] == "coder"

    def test_vision_model(self):
        model_info = {"family": "llava", "supports_vision": True, "supports_code": False}
        defaults = get_model_defaults(model_info)
        assert defaults["suggested_preset"] == "vision"

    def test_default_model(self):
        model_info = {"family": "llama", "supports_vision": False, "supports_code": False}
        defaults = get_model_defaults(model_info)
        assert defaults["suggested_preset"] == "default"
        assert defaults["temperature"] == 0.7


class TestGetSystemPresets:
    def test_returns_all_presets(self):
        presets = get_system_presets()
        assert len(presets) == 5
        assert "default" in presets
        assert "coder" in presets
        assert "analyst" in presets
        assert "vision" in presets
        assert "creative" in presets

    def test_presets_have_fr_en(self):
        presets = get_system_presets()
        for key, val in presets.items():
            assert "fr" in val, f"Preset {key} missing 'fr'"
            assert "en" in val, f"Preset {key} missing 'en'"
