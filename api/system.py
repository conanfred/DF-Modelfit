# Détection matérielle (RAM, CPU, GPU)
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


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
                lines = [l.strip() for l in out.stdout.strip().splitlines() if l.strip()]
                if len(lines) >= 2:
                    return lines[1]
        except Exception:
            pass
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
            pass
        return "Apple Silicon" if _is_arm() else "Processeur inconnu"
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.strip().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "Processeur inconnu"


def _is_arm() -> bool:
    import platform
    return "arm" in platform.machine().lower() or "aarch64" in platform.machine().lower()


def _detect_nvidia_windows() -> tuple[str | None, float | None]:
    if sys.platform != "win32":
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
        return None, None


def _detect_nvidia_linux() -> tuple[str | None, float | None]:
    if sys.platform != "linux":
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
        return "Apple GPU", total_ram_gb


def detect() -> SystemSpecs:
    if psutil is None:
        return SystemSpecs(
            total_ram_gb=16.0,
            available_ram_gb=12.0,
            cpu_cores=8,
            cpu_name="Inconnu (installez psutil)",
            has_gpu=False,
            gpu_name=None,
            gpu_vram_gb=None,
            backend="cpu",
        )

    mem = psutil.virtual_memory()
    total_ram_gb = mem.total / (1024 ** 3)
    available_ram_gb = mem.available / (1024 ** 3)
    cpu_cores = psutil.cpu_count() or 4
    cpu_name = _cpu_name()

    gpu_name, gpu_vram_gb = None, None
    backend = "cpu"

    if sys.platform == "win32":
        gpu_name, gpu_vram_gb = _detect_nvidia_windows()
        if gpu_name:
            backend = "cuda"
    elif sys.platform == "linux":
        gpu_name, gpu_vram_gb = _detect_nvidia_linux()
        if gpu_name:
            backend = "cuda"
    elif sys.platform == "darwin" and _is_arm():
        gpu_name, vram = _detect_apple_gpu(total_ram_gb)
        if gpu_name:
            gpu_vram_gb = vram
            backend = "metal"

    return SystemSpecs(
        total_ram_gb=round(total_ram_gb, 2),
        available_ram_gb=round(available_ram_gb, 2),
        cpu_cores=cpu_cores,
        cpu_name=cpu_name,
        has_gpu=gpu_name is not None,
        gpu_name=gpu_name,
        gpu_vram_gb=round(gpu_vram_gb, 2) if gpu_vram_gb is not None else None,
        backend=backend,
    )
