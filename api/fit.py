# Logique de « fit » : comparer modèle vs matériel
from dataclasses import dataclass
from typing import Any

import math

from .system import SystemSpecs


FIT_PARFAIT = "parfait"
FIT_BON = "bon"
FIT_MARGINAL = "marginal"
FIT_TROP_JUSTE = "trop_juste"


@dataclass
class ModelFit:
    model: dict[str, Any]
    fit_level: str  # parfait | bon | marginal | trop_juste
    mode: str       # gpu | cpu
    mem_requise_gb: float
    mem_dispo_gb: float
    utilisation_pct: float
    quant: str
    note: str
    # Scores (0–100)
    score_quality: float
    score_speed: float
    score_fit: float
    score_context: float
    score: float
    # Estimation de vitesse (tokens/s) – simplifiée
    estimated_tps: float
    # Estimation énergie / coût (approximation)
    estimated_energy_kwh: float
    estimated_cost_per_hour: float
    eco_level: str  # "eco" | "moyen" | "energivore"


def _score_fit_level(
    mem_requise: float,
    mem_dispo: float,
    recommande_gb: float,
    mode: str,
) -> str:
    """Niveau de fit discret (Parfait / Bon / Marginal / Trop juste)."""
    if mem_dispo <= 0:
        return FIT_TROP_JUSTE
    if mem_requise > mem_dispo:
        return FIT_TROP_JUSTE
    utilisation = (mem_requise / mem_dispo) * 100.0
    # Parfait : GPU + dans la fourchette recommandée avec marge
    if mode == "gpu" and recommande_gb > 0 and mem_requise <= recommande_gb * 1.1 and utilisation <= 80:
        return FIT_PARFAIT
    if utilisation <= 70:
        return FIT_BON
    if utilisation <= 95:
        return FIT_MARGINAL
    return FIT_TROP_JUSTE


def _score_fit_continu(mem_pct: float) -> float:
    """Score continu de fit (0–100) centré autour de ~70 % d'utilisation mémoire."""
    if mem_pct <= 0:
        return 0.0
    # Pénaliser très faible et très forte utilisation
    return max(0.0, 100.0 - abs(mem_pct - 70.0) * 2.0)


def _score_quality(parameters_raw: int) -> float:
    """Score qualité basé sur le nombre de paramètres (échelle log)."""
    if not parameters_raw or parameters_raw <= 0:
        return 0.0
    # Échelle ~[10M, 500B] → [0,100]
    log_p = math.log10(parameters_raw)
    return max(0.0, min(100.0, (log_p - 7.0) / (11.7 - 7.0) * 100.0))


def _score_context(ctx: int) -> float:
    """Score contexte : mieux si le contexte est grand, plafonné."""
    if ctx <= 0:
        return 0.0
    target_max = 65536  # 65k tokens ≈ très confortable
    return max(0.0, min(100.0, ctx / target_max * 100.0))


def _estimate_energy_and_cost(
    parameters_raw: int,
    mode: str,
    backend: str | None,
) -> tuple[float, float, str]:
    """
    Estimation très simplifiée de la consommation énergétique et du coût horaire.

    Hypothèses arbitraires :
    - la consommation est proportionnelle au nombre de paramètres et dépend du backend ;
    - le coût est dérivé d'un prix horaire typique (GPU > CPU) ;
    - objectif : fournir un ordre de grandeur relatif, pas une mesure réelle.
    """
    if not parameters_raw or parameters_raw <= 0:
        return 0.0, 0.0, "eco"

    params_b = parameters_raw / 1e9
    backend = (backend or "").lower()

    if "cuda" in backend or "nvidia" in backend:
        base_kwh_per_b = 0.08
        base_cost_per_kwh = 0.35
    elif "metal" in backend or "apple" in backend:
        base_kwh_per_b = 0.05
        base_cost_per_kwh = 0.35
    elif "rocm" in backend or "amd" in backend:
        base_kwh_per_b = 0.07
        base_cost_per_kwh = 0.30
    else:
        # CPU ou inconnu : plus lent, mais potentiellement moins dense en énergie
        base_kwh_per_b = 0.04
        base_cost_per_kwh = 0.30

    energy_kwh = max(0.01, base_kwh_per_b * max(params_b, 0.5))
    cost_per_hour = round(energy_kwh * base_cost_per_kwh, 3)

    if energy_kwh <= 0.1:
        eco = "eco"
    elif energy_kwh <= 0.3:
        eco = "moyen"
    else:
        eco = "energivore"

    return round(energy_kwh, 3), cost_per_hour, eco


def _estimate_tps_placeholder(
    parameters_raw: int,
    mode: str,
    backend: str | None,
) -> float:
    """
    Estimation grossière de tok/s, avant raffinement dans la tâche add-speed-mem.
    Approche simple : constante par backend / taille du modèle.
    """
    if not parameters_raw or parameters_raw <= 0:
        return 0.0
    backend = (backend or "").lower()
    if "cuda" in backend or "nvidia" in backend:
        k = 220.0
    elif "metal" in backend or "apple" in backend:
        k = 160.0
    elif "rocm" in backend or "amd" in backend:
        k = 180.0
    elif "sycl" in backend:
        k = 100.0
    elif "ascend" in backend or "npu" in backend:
        k = 390.0
    else:
        # CPU ou inconnu
        k = 80.0
    params_b = parameters_raw / 1e9
    if params_b <= 0:
        return 0.0
    base = k / max(params_b, 0.1)
    if mode == "cpu":
        base *= 0.5
    return round(base, 1)


def _score_speed_from_tps(tps: float) -> float:
    """Transforme l'estimation de tok/s en score 0–100 (log-échelle simple)."""
    if tps <= 0:
        return 0.0
    log_t = math.log10(tps + 1.0)
    return max(0.0, min(100.0, log_t / 2.0 * 100.0))


def _weights_for_use_case(use_case: str) -> tuple[float, float, float, float]:
    """Renvoie les poids (Q,S,F,C) en fonction du use-case principal."""
    u = (use_case or "").lower()
    if "code" in u or "coder" in u:
        return 0.4, 0.3, 0.15, 0.15
    if "rag" in u or "embed" in u or "embedding" in u:
        return 0.3, 0.3, 0.2, 0.2
    if "chat" in u or "instruct" in u:
        return 0.3, 0.35, 0.2, 0.15
    if "reason" in u or "raisonnement" in u:
        return 0.55, 0.15, 0.15, 0.15
    # par défaut : général
    return 0.4, 0.2, 0.2, 0.2


def analyser(m: dict, system: SystemSpecs) -> ModelFit:
    """Calcule fit, scores Q/S/F/C et score composite pour un modèle sur un système donné."""
    min_ram = float(m.get("min_ram_gb") or 0)
    rec_ram = float(m.get("recommended_ram_gb") or min_ram * 1.5)
    min_vram = float(m.get("min_vram_gb") or min_ram)
    quant = m.get("quantization") or "Q4_K_M"
    ctx = int(m.get("context_length") or 8192)

    mem_requise = min_ram
    mem_dispo = system.available_ram_gb
    mode = "cpu"
    note = ""

    if system.has_gpu and system.gpu_vram_gb is not None and system.gpu_vram_gb > 0:
        # Préférer GPU si le modèle tient en VRAM
        if min_vram <= system.gpu_vram_gb:
            mem_requise = min_vram
            mem_dispo = system.gpu_vram_gb
            mode = "gpu"
            note = "Modèle chargé en VRAM."
        else:
            # Pas assez de VRAM, fallback RAM
            if min_ram <= system.available_ram_gb:
                mem_requise = min_ram
                mem_dispo = system.available_ram_gb
                mode = "cpu"
                note = "VRAM insuffisante, utilisation de la RAM système."
            else:
                mem_requise = min_vram
                mem_dispo = system.gpu_vram_gb
                mode = "gpu"
                note = "VRAM et RAM insuffisantes."
    else:
        if min_ram > system.available_ram_gb:
            mem_requise = min_ram
            mem_dispo = system.available_ram_gb
            note = "RAM insuffisante."
        else:
            note = "Pas de GPU détecté, inférence sur CPU."

    fit_level = _score_fit_level(mem_requise, mem_dispo, rec_ram, mode)
    utilisation_pct = (mem_requise / mem_dispo * 100.0) if mem_dispo > 0 else 0.0
    utilisation_pct = max(0.0, min(200.0, utilisation_pct))  # clamp léger

    # Scores
    params_raw = int(m.get("parameters_raw") or 0)
    score_q = _score_quality(params_raw)
    score_f = _score_fit_continu(utilisation_pct)
    est_tps = _estimate_tps_placeholder(params_raw, mode, system.backend)
    score_s = _score_speed_from_tps(est_tps)
    score_c = _score_context(ctx)
    wq, ws, wf, wc = _weights_for_use_case(m.get("use_case") or "")
    composite = round(wq * score_q + ws * score_s + wf * score_f + wc * score_c, 1)

    energy_kwh, cost_per_hour, eco_level = _estimate_energy_and_cost(
        params_raw,
        mode,
        system.backend,
    )

    return ModelFit(
        model=m,
        fit_level=fit_level,
        mode=mode,
        mem_requise_gb=round(mem_requise, 2),
        mem_dispo_gb=round(mem_dispo, 2),
        utilisation_pct=round(utilisation_pct, 1),
        quant=quant,
        note=note,
        score_quality=round(score_q, 1),
        score_speed=round(score_s, 1),
        score_fit=round(score_f, 1),
        score_context=round(score_c, 1),
        score=composite,
        estimated_tps=est_tps,
        estimated_energy_kwh=energy_kwh,
        estimated_cost_per_hour=cost_per_hour,
        eco_level=eco_level,
    )


def to_dict(f: ModelFit) -> dict:
    return {
        "model": f.model,
        "fit_level": f.fit_level,
        "mode": f.mode,
        "mem_requise_gb": f.mem_requise_gb,
        "mem_dispo_gb": f.mem_dispo_gb,
        "utilisation_pct": f.utilisation_pct,
        "quant": f.quant,
        "note": f.note,
        "score": f.score,
        "score_quality": f.score_quality,
        "score_speed": f.score_speed,
        "score_fit": f.score_fit,
        "score_context": f.score_context,
        "estimated_tps": f.estimated_tps,
        "estimated_energy_kwh": f.estimated_energy_kwh,
        "estimated_cost_per_hour": f.estimated_cost_per_hour,
        "eco_level": f.eco_level,
    }
