"""Tests pour api/chat.py — chat avec modèles IA locaux."""
from unittest.mock import patch, MagicMock
from api.chat import (
    ChatMessage,
    ollama_is_available,
    ollama_list_chat_models,
    ollama_chat_sync,
    build_screen_context_prompt,
)


class TestChatMessage:
    def test_basic(self):
        msg = ChatMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.images is None

    def test_with_images(self):
        msg = ChatMessage(
            role="user", content="what is this?",
            images=["base64data"],
        )
        assert msg.images == ["base64data"]


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


class TestOllamaChatSync:
    @patch("api.chat.urllib.request.urlopen")
    def test_returns_response(self, mock_urlopen):
        import json
        resp_data = {
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True,
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        result = ollama_chat_sync(
            "llama3:8b",
            [{"role": "user", "content": "Hi"}],
        )
        assert result["message"]["content"] == "Hello!"

    @patch("api.chat.urllib.request.urlopen",
           side_effect=Exception("refused"))
    def test_returns_error_on_failure(self, mock_urlopen):
        result = ollama_chat_sync(
            "llama3:8b",
            [{"role": "user", "content": "Hi"}],
        )
        assert result["error"] is True


class TestBuildScreenContextPrompt:
    def test_french(self):
        prompt = build_screen_context_prompt("fr")
        assert "DF Modelfit" in prompt
        assert "captures d'écran" in prompt

    def test_english(self):
        prompt = build_screen_context_prompt("en")
        assert "DF Modelfit" in prompt
        assert "screenshots" in prompt
