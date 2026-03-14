"""Tests pour api/professions.py — recommandation par métier."""
from api.professions import (
    PROFESSIONS,
    PROFESSIONS_BY_ID,
    get_all_professions,
    recommend_for_profession,
    score_model_for_profession,
)
from api.system import SystemSpecs
from api.fit import analyser, to_dict


def _make_model_fit(name="test/model", params_raw=7_000_000_000,
                    ctx=32768, use_case="Chat, instruction"):
    sys = SystemSpecs(
        total_ram_gb=16, available_ram_gb=14, cpu_cores=8,
        cpu_name="Test", has_gpu=False, gpu_name=None,
        gpu_vram_gb=None, backend="cpu",
    )
    model = {
        "name": name, "provider": "Test",
        "parameter_count": "7B", "parameters_raw": params_raw,
        "min_ram_gb": 4.0, "recommended_ram_gb": 8.0,
        "min_vram_gb": 3.0, "quantization": "Q4_K_M",
        "context_length": ctx, "use_case": use_case,
    }
    f = analyser(model, sys)
    return to_dict(f)


class TestProfessionsList:
    def test_at_least_10_professions(self):
        assert len(PROFESSIONS) >= 10

    def test_all_have_required_fields(self):
        for p in PROFESSIONS:
            assert p.id
            assert p.icon
            assert p.name_fr
            assert p.name_en
            assert p.use_cases
            assert p.keywords

    def test_ids_are_unique(self):
        ids = [p.id for p in PROFESSIONS]
        assert len(ids) == len(set(ids))

    def test_by_id_lookup(self):
        assert "developer" in PROFESSIONS_BY_ID
        assert "student" in PROFESSIONS_BY_ID
        assert PROFESSIONS_BY_ID["developer"].prefer_code is True


class TestGetAllProfessions:
    def test_returns_list_fr(self):
        result = get_all_professions("fr")
        assert len(result) >= 10
        assert all("id" in p for p in result)
        assert result[0]["name"]  # non-empty

    def test_returns_list_en(self):
        result = get_all_professions("en")
        assert len(result) >= 10
        dev = next(p for p in result if p["id"] == "developer")
        assert "Developer" in dev["name"]


class TestScoreModelForProfession:
    def test_code_model_for_developer(self):
        mf = _make_model_fit(
            name="bigcode/starcoder2-7b",
            use_case="Code",
        )
        prof = PROFESSIONS_BY_ID["developer"]
        score, reasons = score_model_for_profession(mf, prof)
        assert score > 0

    def test_chat_model_for_student(self):
        mf = _make_model_fit(
            name="meta-llama/Llama-3.2-3B-Instruct",
            params_raw=3_000_000_000,
        )
        prof = PROFESSIONS_BY_ID["student"]
        score, _ = score_model_for_profession(mf, prof)
        assert score > 0


class TestRecommendForProfession:
    def test_valid_profession(self):
        fits = [_make_model_fit() for _ in range(5)]
        result = recommend_for_profession("developer", fits, limit=3)
        assert "profession" in result
        assert "models" in result
        assert "tips" in result
        assert len(result["models"]) <= 3
        assert result["profession"]["id"] == "developer"

    def test_unknown_profession(self):
        result = recommend_for_profession("unknown", [])
        assert result.get("error") is True

    def test_with_tips_fr(self):
        result = recommend_for_profession("developer", [], lang="fr")
        assert len(result["tips"]) >= 1
        assert any("code" in t.lower() for t in result["tips"])

    def test_with_tips_en(self):
        result = recommend_for_profession("developer", [], lang="en")
        assert len(result["tips"]) >= 1
        assert any("Code" in t or "code" in t for t in result["tips"])

    def test_settings_returned(self):
        result = recommend_for_profession("developer", [])
        assert "settings" in result
        s = result["settings"]
        assert s["prefer_code"] is True
        assert s["suggested_temperature"] == 0.3
