from __future__ import annotations

import platform
from dataclasses import dataclass, asdict

import psutil


@dataclass
class SystemInfo:
    os: str
    os_version: str
    cpu_model: str
    cpu_cores_logical: int
    cpu_cores_physical: int
    ram_total_gb: float


def _round_gb(bytes_value: float) -> float:
    return round(bytes_value / (1024**3), 2)


def get_system_info() -> SystemInfo:
    uname = platform.uname()
    cpu_freq = psutil.cpu_freq()

    return SystemInfo(
        os=uname.system,
        os_version=uname.release,
        cpu_model=uname.processor or uname.machine,
        cpu_cores_logical=psutil.cpu_count(logical=True) or 0,
        cpu_cores_physical=psutil.cpu_count(logical=False) or 0,
        ram_total_gb=_round_gb(psutil.virtual_memory().total),
    )


def system_info_dict() -> dict:
    return asdict(get_system_info())

