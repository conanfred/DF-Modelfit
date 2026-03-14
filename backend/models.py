from __future__ import annotations

"""
Petit module de base de modèles local.

Il est volontairement simple : il charge `data/models.json` (un sous‑ensemble
manuel de modèles populaires) et fournit quelques aides pour les tailles
et la mémoire estimée. Le backend FastAPI principal utilise déjà une base
plus riche (`hf_models.json`), mais ce module reste utile pour des tests
unitaires ou des scénarios hors‑ligne.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_PATH = DATA_DIR / "models.json"


@dataclass
class ModelSpec:
  name: str
  provider: str
  parameters_raw: int
  parameter_count: str
  min_ram_gb: float
  recommended_ram_gb: float
  min_vram_gb: float
  quantization: str
  context_length: int
  use_case: str

  @property
  def params_billion(self) -> float:
    return self.parameters_raw / 1e9


def _load_models_raw() -> list[dict[str, Any]]:
  if not MODELS_PATH.exists():
    return []
  try:
    with MODELS_PATH.open(encoding="utf-8") as f:
      data = json.load(f)
    if isinstance(data, list):
      return [m for m in data if isinstance(m, dict)]
  except (OSError, json.JSONDecodeError):
    return []
  return []


def load_models() -> list[ModelSpec]:
  """
  Charge les modèles à partir de `data/models.json`.

  Si le fichier est absent ou invalide, retourne une liste vide. Le
  backend principal retombera alors sur d'autres sources (hf_models.json).
  """
  specs: list[ModelSpec] = []
  for m in _load_models_raw():
    try:
      specs.append(
        ModelSpec(
          name=str(m.get("name") or ""),
          provider=str(m.get("provider") or ""),
          parameters_raw=int(m.get("parameters_raw") or 0),
          parameter_count=str(m.get("parameter_count") or ""),
          min_ram_gb=float(m.get("min_ram_gb") or 0.0),
          recommended_ram_gb=float(m.get("recommended_ram_gb") or 0.0),
          min_vram_gb=float(m.get("min_vram_gb") or 0.0),
          quantization=str(m.get("quantization") or "Q4_K_M"),
          context_length=int(m.get("context_length") or 0),
          use_case=str(m.get("use_case") or ""),
        )
      )
    except (ValueError, TypeError):
      # On ignore silencieusement les entrées invalides
      continue
  return specs


