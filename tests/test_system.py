"""Tests pour api/system.py — détection matérielle et cache."""
from unittest.mock import patch

import pytest
from api.system import (
    detect,
    detect_custom,
    SystemSpecs,
    _cpu_name,
    _detect_nvidia,
    _is_arm,
)


class TestDetect:
    def test_returns_system_specs(self):
        specs = detect(use_cache=False)
        assert isinstance(specs, SystemSpecs)
        assert specs.total_ram_gb > 0
        assert specs.available_ram_gb > 0
        assert specs.cpu_cores > 0
        assert isinstance(specs.cpu_name, str)
        assert isinstance(specs.backend, str)

    def test_cache_returns_same_object(self):
        specs1 = detect(use_cache=False)
        specs2 = detect(use_cache=True)
        assert specs1 == specs2

    def test_cache_bypass(self):
        specs1 = detect(use_cache=False)
        specs2 = detect(use_cache=False)
        assert specs1.total_ram_gb == specs2.total_ram_gb

    @patch("api.system.psutil", None)
    def test_fallback_without_psutil(self):
        specs = detect(use_cache=False)
        assert specs.total_ram_gb == 16.0
        assert specs.cpu_name == "Inconnu (installez psutil)"


class TestDetectCustom:
    def test_custom_cpu_only(self):
        specs = detect_custom(total_ram_gb=32.0, cpu_cores=16)
        assert specs.total_ram_gb == 32.0
        assert specs.cpu_cores == 16
        assert specs.has_gpu is False
        assert specs.backend == "cpu"
        assert specs.cpu_name == "Profil personnalisé"

    def test_custom_with_gpu(self):
        specs = detect_custom(total_ram_gb=64.0, cpu_cores=32, gpu_vram_gb=24.0, backend="cuda")
        assert specs.has_gpu is True
        assert specs.gpu_vram_gb == 24.0
        assert specs.backend == "cuda"

    def test_available_ram_is_85pct(self):
        specs = detect_custom(total_ram_gb=100.0, cpu_cores=8)
        assert specs.available_ram_gb == pytest.approx(85.0)


class TestDetectNvidia:
    def test_returns_none_on_wrong_platform(self):
        name, vram = _detect_nvidia("win32" if __import__("sys").platform != "win32" else "darwin")
        assert name is None
        assert vram is None


class TestCpuName:
    def test_returns_string(self):
        name = _cpu_name()
        assert isinstance(name, str)
        assert len(name) > 0


class TestIsArm:
    def test_returns_bool(self):
        assert isinstance(_is_arm(), bool)
