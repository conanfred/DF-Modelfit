"""Tests pour api/huggingface.py — parsing et utilitaires."""
from api.huggingface import (
    _format_param_count,
    _estimate_ram,
    _estimate_vram,
    _infer_context_length,
    _extract_provider,
    _infer_use_case,
    _parse_next_cursor,
    _smart_select,
    model_info_to_entry,
)


class TestFormatParamCount:
    def test_billions(self):
        assert _format_param_count(7_000_000_000) == "7B"

    def test_billions_decimal(self):
        assert _format_param_count(14_770_000_000) == "14.8B"

    def test_millions(self):
        assert _format_param_count(350_000_000) == "350M"

    def test_thousands(self):
        assert _format_param_count(500_000) == "500K"


class TestEstimateRam:
    def test_small_model(self):
        min_gb, rec_gb = _estimate_ram(1_000_000_000)
        assert min_gb >= 1.0
        assert rec_gb >= min_gb

    def test_large_model(self):
        min_gb, rec_gb = _estimate_ram(70_000_000_000)
        assert min_gb > 10
        assert rec_gb > min_gb


class TestEstimateVram:
    def test_positive(self):
        vram = _estimate_vram(7_000_000_000)
        assert vram > 0

    def test_minimum(self):
        vram = _estimate_vram(100_000)
        assert vram >= 0.5


class TestInferContextLength:
    def test_max_position_embeddings(self):
        config = {"max_position_embeddings": 131072}
        assert _infer_context_length(config) == 131072

    def test_n_positions(self):
        config = {"n_positions": 2048}
        assert _infer_context_length(config) == 2048

    def test_text_config_nested(self):
        config = {"text_config": {"max_position_embeddings": 65536}}
        assert _infer_context_length(config) == 65536

    def test_default_fallback(self):
        assert _infer_context_length(None) == 4096
        assert _infer_context_length({}) == 4096


class TestExtractProvider:
    def test_known_providers(self):
        assert _extract_provider("meta-llama/Llama-3") == "Meta"
        assert _extract_provider("mistralai/Mistral-7B") == "Mistral AI"
        assert _extract_provider("qwen/Qwen2.5") == "Alibaba (Qwen)"
        assert _extract_provider("microsoft/Phi-3") == "Microsoft"
        assert _extract_provider("google/gemma-2") == "Google"
        assert _extract_provider("deepseek-ai/DeepSeek") == "DeepSeek"

    def test_unknown_provider(self):
        result = _extract_provider("my-org/my-model")
        assert result == "My Org"


class TestInferUseCase:
    def test_code_model(self):
        assert "Code" in _infer_use_case("bigcode/starcoder2", None)

    def test_instruct_model(self):
        assert "Chat" in _infer_use_case("meta-llama/Llama-3-Instruct", None)

    def test_embed_model(self):
        assert "Embed" in _infer_use_case("nomic-ai/nomic-embed", None)

    def test_default(self):
        assert _infer_use_case("some/model", "text-generation") == "Génération de texte"
        assert _infer_use_case("some/model", None) == "Général"


class TestParseNextCursor:
    def test_valid_link(self):
        header = '<https://huggingface.co/api/models?cursor=abc123>; rel="next"'
        assert _parse_next_cursor(header) == "abc123"

    def test_no_next(self):
        header = '<https://huggingface.co/api/models?cursor=abc>; rel="prev"'
        assert _parse_next_cursor(header) is None

    def test_none(self):
        assert _parse_next_cursor(None) is None


class TestSmartSelect:
    def test_empty(self):
        assert _smart_select([], 5) == []

    def test_selects_n(self):
        items = [
            {"modelId": f"model-{i}", "likes": i * 10, "trendingScore": 0, "createdAt": f"2024-01-{i+1:02d}"}
            for i in range(10)
        ]
        result = _smart_select(items, 5)
        assert len(result) == 5

    def test_mix_of_best_and_recent(self):
        items = [
            {"modelId": "old-popular", "likes": 1000, "trendingScore": 500, "createdAt": "2023-01-01"},
            {"modelId": "new-model", "likes": 0, "trendingScore": 0, "createdAt": "2024-12-01"},
            {"modelId": "medium", "likes": 100, "trendingScore": 50, "createdAt": "2024-06-01"},
        ]
        result = _smart_select(items, 3)
        assert len(result) == 3
        assert "old-popular" in result


class TestModelInfoToEntry:
    def test_valid_info(self):
        info = {
            "safetensors": {"total": 7_000_000_000},
            "pipeline_tag": "text-generation",
            "config": {"max_position_embeddings": 32768},
            "createdAt": "2024-01-01T00:00:00Z",
            "likes": 100,
            "downloads": 5000,
        }
        entry = model_info_to_entry("test/model", info, None)
        assert entry is not None
        assert entry["name"] == "test/model"
        assert entry["parameters_raw"] == 7_000_000_000
        assert entry["context_length"] == 32768
        assert entry["min_ram_gb"] > 0

    def test_no_params_returns_none(self):
        info = {"safetensors": {}}
        assert model_info_to_entry("test/model", info, None) is None

    def test_with_full_config(self):
        info = {
            "safetensors": {"total": 3_000_000_000},
            "pipeline_tag": "text-generation",
        }
        config = {"max_position_embeddings": 131072}
        entry = model_info_to_entry("test/model", info, config)
        assert entry is not None
        assert entry["context_length"] == 131072
