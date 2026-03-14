"""Tests pour api/fit.py — scoring et niveaux de fit."""
import pytest
from api.system import SystemSpecs
from api.fit import (
    analyser,
    to_dict,
    _score_quality,
    _score_context,
    _score_fit_continu,
    _score_fit_level,
    _estimate_tps_placeholder,
    _estimate_energy_and_cost,
    _weights_for_use_case,
    _score_speed_from_tps,
    FIT_PARFAIT,
    FIT_BON,
    FIT_MARGINAL,
    FIT_TROP_JUSTE,
)


def _make_system(ram=16.0, avail=14.0, gpu_vram=None, backend="cpu"):
    return SystemSpecs(
        total_ram_gb=ram,
        available_ram_gb=avail,
        cpu_cores=8,
        cpu_name="Test CPU",
        has_gpu=gpu_vram is not None,
        gpu_name="Test GPU" if gpu_vram else None,
        gpu_vram_gb=gpu_vram,
        backend=backend,
    )


def _make_model(name="test/model", min_ram=4.0, rec_ram=8.0, min_vram=3.0,
                params_raw=7_000_000_000, ctx=32768, use_case="Chat"):
    return {
        "name": name,
        "provider": "Test",
        "parameter_count": "7B",
        "parameters_raw": params_raw,
        "min_ram_gb": min_ram,
        "recommended_ram_gb": rec_ram,
        "min_vram_gb": min_vram,
        "quantization": "Q4_K_M",
        "context_length": ctx,
        "use_case": use_case,
    }


class TestScoreFitLevel:
    def test_trop_juste_when_mem_exceeds(self):
        assert _score_fit_level(20.0, 16.0, 20.0, "cpu") == FIT_TROP_JUSTE

    def test_trop_juste_when_no_mem(self):
        assert _score_fit_level(5.0, 0.0, 10.0, "cpu") == FIT_TROP_JUSTE

    def test_bon_when_low_utilisation(self):
        assert _score_fit_level(5.0, 16.0, 10.0, "cpu") == FIT_BON

    def test_marginal_when_high_utilisation(self):
        assert _score_fit_level(12.0, 16.0, 15.0, "cpu") == FIT_MARGINAL

    def test_parfait_gpu_in_range(self):
        assert _score_fit_level(4.0, 12.0, 8.0, "gpu") == FIT_PARFAIT


class TestScoreQuality:
    def test_zero_params(self):
        assert _score_quality(0) == 0.0

    def test_negative_params(self):
        assert _score_quality(-1) == 0.0

    def test_small_model(self):
        score = _score_quality(100_000_000)
        assert 0 < score < 50

    def test_large_model(self):
        score = _score_quality(70_000_000_000)
        assert score > 50

    def test_clamped_to_100(self):
        score = _score_quality(10**12)
        assert score <= 100.0


class TestScoreContext:
    def test_zero_context(self):
        assert _score_context(0) == 0.0

    def test_large_context(self):
        assert _score_context(65536) == pytest.approx(100.0)

    def test_small_context(self):
        score = _score_context(4096)
        assert 0 < score < 100

    def test_over_target_clamped(self):
        assert _score_context(200000) == 100.0


class TestScoreFitContinu:
    def test_optimal_at_70(self):
        assert _score_fit_continu(70.0) == 100.0

    def test_zero_pct(self):
        assert _score_fit_continu(0.0) == 0.0

    def test_symmetric_penalty(self):
        s_low = _score_fit_continu(50.0)
        s_high = _score_fit_continu(90.0)
        assert s_low == s_high


class TestEstimateTps:
    def test_zero_params(self):
        assert _estimate_tps_placeholder(0, "cpu", "cpu") == 0.0

    def test_cpu_slower_than_gpu(self):
        tps_cpu = _estimate_tps_placeholder(7_000_000_000, "cpu", "cpu")
        tps_gpu = _estimate_tps_placeholder(7_000_000_000, "gpu", "cuda")
        assert tps_gpu > tps_cpu


class TestEstimateEnergy:
    def test_zero_params(self):
        kwh, cost, eco = _estimate_energy_and_cost(0, "cpu", "cpu")
        assert kwh == 0.0
        assert cost == 0.0
        assert eco == "eco"

    def test_large_model_energivore(self):
        kwh, cost, eco = _estimate_energy_and_cost(70_000_000_000, "gpu", "cuda")
        assert kwh > 0.3
        assert eco == "energivore"

    def test_small_model_eco(self):
        kwh, cost, eco = _estimate_energy_and_cost(1_000_000_000, "cpu", "cpu")
        assert eco == "eco"


class TestWeightsForUseCase:
    def test_coding(self):
        wq, ws, wf, wc = _weights_for_use_case("Code")
        assert wq == 0.4

    def test_chat(self):
        wq, ws, wf, wc = _weights_for_use_case("Chat, instruction")
        assert ws == 0.35

    def test_default(self):
        wq, ws, wf, wc = _weights_for_use_case("Général")
        assert wq == 0.4
        assert ws == 0.2


class TestScoreSpeedFromTps:
    def test_zero_tps(self):
        assert _score_speed_from_tps(0) == 0.0

    def test_positive_tps(self):
        score = _score_speed_from_tps(10.0)
        assert 0 < score < 100


class TestAnalyser:
    def test_cpu_mode(self):
        sys = _make_system(ram=16.0, avail=14.0)
        m = _make_model(min_ram=4.0)
        fit = analyser(m, sys)
        assert fit.mode == "cpu"
        assert fit.fit_level in (FIT_PARFAIT, FIT_BON, FIT_MARGINAL)
        assert fit.utilisation_pct > 0

    def test_gpu_mode(self):
        sys = _make_system(ram=32.0, avail=28.0, gpu_vram=12.0, backend="cuda")
        m = _make_model(min_ram=4.0, min_vram=3.0)
        fit = analyser(m, sys)
        assert fit.mode == "gpu"

    def test_trop_juste_insufficient_ram(self):
        sys = _make_system(ram=4.0, avail=2.0)
        m = _make_model(min_ram=8.0)
        fit = analyser(m, sys)
        assert fit.fit_level == FIT_TROP_JUSTE

    def test_scores_are_bounded(self):
        sys = _make_system()
        m = _make_model()
        fit = analyser(m, sys)
        assert 0 <= fit.score_quality <= 100
        assert 0 <= fit.score_speed <= 100
        assert 0 <= fit.score_fit <= 100
        assert 0 <= fit.score_context <= 100
        assert 0 <= fit.score <= 100


class TestToDict:
    def test_returns_expected_keys(self):
        sys = _make_system()
        m = _make_model()
        fit = analyser(m, sys)
        d = to_dict(fit)
        assert "model" in d
        assert "fit_level" in d
        assert "score" in d
        assert "score_quality" in d
        assert "estimated_tps" in d
        assert "eco_level" in d
