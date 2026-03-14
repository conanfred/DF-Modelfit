# Détection matérielle (RAM, CPU, GPU)
import logging
import subprocess
import sys
import time
from dataclasses import dataclass

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

_cache: dict[str, object] = {}
_cache_ts: float = 0.0
_CACHE_TTL_S = 30.0


@dataclass
class SystemSpecs:
    total_ram_gb: float
    available_ram_gb: float
    cpu_cores: int
    cpu_name: str
    has_gpu: bool
    gpu_name: str | None
    gpu_vram_gb: float | None
    backend: str  # cuda, metal, rocm, cpu


def _cpu_name() -> str:
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["wmic", "cpu", "get", "name"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0 and out.stdout:
                lines = [line.strip() for line in out.stdout.strip().splitlines() if line.strip()]
                if len(lines) >= 2:
                    return lines[1]
        except Exception:
            logger.debug("wmic cpu detection failed", exc_info=True)
        return "Processeur inconnu"
    if sys.platform == "darwin":
        try:
            out = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0 and out.stdout:
                return out.stdout.strip()
        except Exception:
            logger.debug("sysctl cpu detection failed", exc_info=True)
        return "Apple Silicon" if _is_arm() else "Processeur inconnu"
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.strip().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        logger.debug("/proc/cpuinfo read failed", exc_info=True)
    return "Processeur inconnu"


def _is_arm() -> bool:
    import platform
    return "arm" in platform.machine().lower() or "aarch64" in platform.machine().lower()


def _detect_nvidia(platform_check: str) -> tuple[str | None, float | None]:
    """Détecte un GPU NVIDIA via nvidia-smi (Windows ou Linux)."""
    if sys.platform != platform_check:
        return None, None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode != 0 or not out.stdout.strip():
            return None, None
        line = out.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            name = parts[0]
            try:
                vram_mb = int(parts[1].strip().split()[0])
                return name, vram_mb / 1024.0
            except (ValueError, IndexError):
                return name, None
        return None, None
    except FileNotFoundError:
        return None, None
    except Exception:
        logger.debug("nvidia-smi detection failed on %s", platform_check, exc_info=True)
        return None, None


def _detect_apple_gpu(total_ram_gb: float) -> tuple[str | None, float | None]:
    if sys.platform != "darwin":
        return None, None
    if not _is_arm():
        return None, None
    try:
        out = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if out.returncode != 0:
            return "Apple GPU", total_ram_gb
        if "Chipset Model" in out.stdout or "Apple" in out.stdout:
            return "Apple Silicon", total_ram_gb
        return "Apple GPU", total_ram_gb
    except Exception:
        logger.debug("Apple GPU detection failed", exc_info=True)
        return "Apple GPU", total_ram_gb


def detect(*, use_cache: bool = True) -> SystemSpecs:
    """Détecte les specs matérielles avec cache TTL de 30 s."""
    global _cache, _cache_ts

    now = time.time()
    if use_cache and _cache and (now - _cache_ts) < _CACHE_TTL_S:
        return _cache["specs"]  # type: ignore[return-value]

    if psutil is None:
        specs = SystemSpecs(
            total_ram_gb=16.0,
            available_ram_gb=12.0,
            cpu_cores=8,
            cpu_name="Inconnu (installez psutil)",
            has_gpu=False,
            gpu_name=None,
            gpu_vram_gb=None,
            backend="cpu",
        )
        logger.warning("psutil non installé, valeurs par défaut utilisées")
        _cache = {"specs": specs}
        _cache_ts = now
        return specs

    mem = psutil.virtual_memory()
    total_ram_gb = mem.total / (1024 ** 3)
    available_ram_gb = mem.available / (1024 ** 3)
    cpu_cores = psutil.cpu_count() or 4
    cpu_name_val = _cpu_name()

    gpu_name, gpu_vram_gb = None, None
    backend = "cpu"

    if sys.platform == "win32":
        gpu_name, gpu_vram_gb = _detect_nvidia("win32")
        if gpu_name:
            backend = "cuda"
    elif sys.platform == "linux":
        gpu_name, gpu_vram_gb = _detect_nvidia("linux")
        if gpu_name:
            backend = "cuda"
    elif sys.platform == "darwin" and _is_arm():
        gpu_name, vram = _detect_apple_gpu(total_ram_gb)
        if gpu_name:
            gpu_vram_gb = vram
            backend = "metal"

    specs = SystemSpecs(
        total_ram_gb=round(total_ram_gb, 2),
        available_ram_gb=round(available_ram_gb, 2),
        cpu_cores=cpu_cores,
        cpu_name=cpu_name_val,
        has_gpu=gpu_name is not None,
        gpu_name=gpu_name,
        gpu_vram_gb=round(gpu_vram_gb, 2) if gpu_vram_gb is not None else None,
        backend=backend,
    )

    _cache = {"specs": specs}
    _cache_ts = now
    logger.info("Hardware detected: %s", specs)
    return specs


def detect_custom(
    total_ram_gb: float,
    cpu_cores: int,
    gpu_vram_gb: float | None = None,
    backend: str = "cpu",
) -> SystemSpecs:
    """Crée un profil matériel personnalisé (mode manuel)."""
    has_gpu = gpu_vram_gb is not None and gpu_vram_gb > 0
    return SystemSpecs(
        total_ram_gb=round(total_ram_gb, 2),
        available_ram_gb=round(total_ram_gb * 0.85, 2),
        cpu_cores=cpu_cores,
        cpu_name="Profil personnalisé",
        has_gpu=has_gpu,
        gpu_name="GPU personnalisé" if has_gpu else None,
        gpu_vram_gb=round(gpu_vram_gb, 2) if gpu_vram_gb else None,
        backend=backend if has_gpu else "cpu",
    )
