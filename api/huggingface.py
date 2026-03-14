# Chargement des modèles depuis l'API Hugging Face — DF AI Research
import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from urllib.parse import parse_qs, quote, urlparse

logger = logging.getLogger(__name__)

HF_API = "https://huggingface.co/api/models"
# Nombre max de modèles à récupérer via la liste paginée (évite des milliers d’appels).
# Chaque modèle = 2 appels API + pause 0,3 s → 2000 modèles ≈ 15–20 min. Plus = rate-limit possible.
# Limite par usage : uniquement 5, 10, 15, 20 (choix dans l'UI). 54 * 20 = 1080 max.
ALLOWED_LIMITS_PER_USAGE = (5, 10, 15, 20)
DEFAULT_LIMIT_PER_USAGE = 20
MIN_LIMIT_PER_USAGE = 5
MAX_LIMIT_PER_USAGE = 20
# Tous les pipeline_tag (usages) du Hub Hugging Face — source: huggingface.js/packages/tasks/src/pipelines.ts
PIPELINE_TAGS_BY_USAGE = [
    "text-generation-inference",  # inférence LLM (Hub)
    "text-classification",
    "token-classification",
    "table-question-answering",
    "question-answering",
    "zero-shot-classification",
    "translation",
    "summarization",
    "feature-extraction",
    "text-generation",
    "fill-mask",
    "sentence-similarity",
    "text-to-speech",
    "text-to-audio",
    "automatic-speech-recognition",
    "audio-to-audio",
    "audio-classification",
    "audio-text-to-text",
    "voice-activity-detection",
    "depth-estimation",
    "image-classification",
    "object-detection",
    "image-segmentation",
    "text-to-image",
    "image-to-text",
    "image-to-image",
    "image-to-video",
    "unconditional-image-generation",
    "video-classification",
    "reinforcement-learning",
    "robotics",
    "tabular-classification",
    "tabular-regression",
    "tabular-to-text",
    "table-to-text",
    "multiple-choice",
    "text-ranking",
    "text-retrieval",
    "time-series-forecasting",
    "text-to-video",
    "image-text-to-text",
    "image-text-to-image",
    "image-text-to-video",
    "visual-question-answering",
    "document-question-answering",
    "zero-shot-image-classification",
    "graph-ml",
    "mask-generation",
    "zero-shot-object-detection",
    "text-to-3d",
    "image-to-3d",
    "image-feature-extraction",
    "video-text-to-text",
    "keypoint-detection",
    "visual-document-retrieval",
    "any-to-any",
    "video-to-video",
    "other",
]
# Taille de chaque page de la liste HF.
LIST_PAGE_SIZE = 100
# Plafond total (54 usages × 20 max = 1080). On ne récupère le détail que pour les N premiers après fusion.
MAX_TOTAL_MODELS_TO_FETCH = 1080


def _auth_headers() -> dict[str, str]:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    headers = {"User-Agent": "DF-Modelfit/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# Liste de secours si l’API de liste échoue (génération de texte populaires)
TARGET_MODELS_FALLBACK = [
    "meta-llama/Llama-3.2-3B",
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3.5-mini-instruct",
    "google/gemma-2-2b-it",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
]


def _parse_next_cursor(link_header: str | None) -> str | None:
    """Extrait le cursor de la page suivante depuis le header Link."""
    if not link_header:
        return None
    # Format: <https://...?cursor=XXX>; rel="next"
    match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
    if not match:
        return None
    url = match.group(1)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    cursors = qs.get("cursor", [])
    return cursors[0] if cursors else None


def fetch_model_list_from_api(
    pool_size: int,
    pipeline_filter: str,
) -> list[dict]:
    """Liste de modèles avec métadonnées (modelId, likes, trendingScore, createdAt)."""
    items: list[dict] = []
    seen: set[str] = set()
    cursor: str | None = None
    url_base = HF_API
    while len(items) < pool_size:
        params = "limit=%d" % min(LIST_PAGE_SIZE, pool_size - len(items))
        if pipeline_filter:
            params += "&filter=" + quote(pipeline_filter, safe="")
        if cursor:
            params += "&cursor=" + quote(cursor, safe="")
        url = url_base + "?" + params
        req = urllib.request.Request(url, headers=_auth_headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                link_header = resp.headers.get("Link")
                body = resp.read().decode()
                data = json.loads(body)
            if not isinstance(data, list):
                break
            for item in data:
                model_id = item.get("modelId") or item.get("id")
                if not model_id or not isinstance(model_id, str) or model_id in seen:
                    continue
                seen.add(model_id)
                items.append({
                    "modelId": model_id,
                    "likes": int(item.get("likes") or 0),
                    "trendingScore": int(item.get("trendingScore") or 0),
                    "createdAt": (item.get("createdAt") or "")[:19],
                })
                if len(items) >= pool_size:
                    break
            cursor = _parse_next_cursor(link_header)
            if not cursor or not data:
                break
            time.sleep(0.2)
        except (OSError, urllib.error.HTTPError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("HF list fetch error for %s: %s", pipeline_filter, exc)
            break
    logger.info("Fetched %d models for pipeline %s", len(items), pipeline_filter)
    return items


def _smart_select(items: list[dict], n: int) -> list[str]:
    """Environ 75% des meilleurs (likes+trending), 25% des plus récents. Si pas assez de récents, complète avec les meilleurs."""
    if not items or n <= 0:
        return []
    n = min(n, len(items))
    def score_key(x: dict) -> int:
        return (x.get("likes") or 0) + (x.get("trendingScore") or 0)

    def date_key(x: dict) -> str:
        return x.get("createdAt") or ""
    n_best = max(1, round(n * 0.75))
    n_new = n - n_best
    by_score = sorted(items, key=score_key, reverse=True)
    best_ids = [by_score[i]["modelId"] for i in range(min(n_best, len(by_score)))]
    best_set = set(best_ids)
    by_date = sorted(items, key=date_key, reverse=True)
    new_ids = []
    for it in by_date:
        if it["modelId"] in best_set:
            continue
        new_ids.append(it["modelId"])
        if len(new_ids) >= n_new:
            break
    return (best_ids + new_ids)[:n]


def fetch_model_ids_from_api(
    limit_total: int = DEFAULT_LIMIT_PER_USAGE,
    pipeline_filter: str = "text-generation-inference",
) -> list[str]:
    """
    Récupère les IDs de modèles via l’API list (pagination).
    Filtre par pipeline_tag pour limiter aux modèles de génération de texte.
    """
    pool_size = min(80, max(limit_total * 3, 30))
    items = fetch_model_list_from_api(pool_size=pool_size, pipeline_filter=pipeline_filter)
    if not items and pool_size < 150:
        items = fetch_model_list_from_api(pool_size=150, pipeline_filter=pipeline_filter)
    return _smart_select(items, limit_total)


def fetch_model_info(repo_id: str) -> dict | None:
    """Récupère les infos d'un modèle depuis l'API Hugging Face."""
    url = f"{HF_API}/{repo_id}"
    req = urllib.request.Request(url, headers=_auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            pass  # modèle gated, ignorer
        return None
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def fetch_config_json(repo_id: str) -> dict | None:
    """Récupère config.json du dépôt (pour max_position_embeddings)."""
    url = f"https://huggingface.co/{repo_id}/resolve/main/config.json"
    req = urllib.request.Request(url, headers=_auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except (OSError, urllib.error.HTTPError, json.JSONDecodeError, ValueError):
        return None


def _format_param_count(total: int) -> str:
    if total >= 1_000_000_000:
        v = total / 1_000_000_000
        return f"{int(v)}B" if v == int(v) else f"{v:.1f}B"
    if total >= 1_000_000:
        return f"{total // 1_000_000}M"
    return f"{total // 1000}K"


def _estimate_ram(total_params: int, bpp: float = 0.5) -> tuple[float, float]:
    model_gb = (total_params * bpp) / (1024**3)
    min_gb = max(model_gb * 1.2, 1.0)
    rec_gb = max(model_gb * 2.0, 2.0)
    return round(min_gb, 1), round(rec_gb, 1)


def _estimate_vram(total_params: int, bpp: float = 0.5) -> float:
    model_gb = (total_params * bpp) / (1024**3)
    return round(max(model_gb * 1.1, 0.5), 1)


def _infer_context_length(config: dict | None) -> int:
    if not config:
        return 4096
    for key in ("max_position_embeddings", "max_sequence_length", "n_positions", "seq_length"):
        if key in config and isinstance(config[key], int) and config[key] > 0:
            return config[key]
    if "text_config" in config and isinstance(config["text_config"], dict):
        for key in ("max_position_embeddings", "max_sequence_length"):
            if key in config["text_config"] and isinstance(config["text_config"][key], int):
                return config["text_config"][key]
    return 4096


def _extract_provider(repo_id: str) -> str:
    org = repo_id.split("/")[0].lower()
    mapping = {
        "meta-llama": "Meta",
        "mistralai": "Mistral AI",
        "qwen": "Alibaba (Qwen)",
        "microsoft": "Microsoft",
        "google": "Google",
        "deepseek-ai": "DeepSeek",
        "01-ai": "01.ai",
        "bigcode": "BigCode",
        "nomic-ai": "Nomic",
        "liquidai": "Liquid AI",
        "huggingfacetb": "Hugging Face",
        "unsloth": "Unsloth",
        "upstage": "Upstage",
        "tiiuae": "TII",
        "codellama": "Meta",
    }
    return mapping.get(org, org.replace("-", " ").title())


def _infer_use_case(repo_id: str, pipeline_tag: str | None) -> str:
    r = repo_id.lower()
    if "embed" in r:
        return "Embeddings, RAG"
    if "coder" in r or "code" in r or "starcoder" in r:
        return "Code"
    if "instruct" in r or "chat" in r:
        return "Chat, instruction"
    if pipeline_tag == "text-generation":
        return "Génération de texte"
    return "Général"


def model_info_to_entry(repo_id: str, info: dict, full_config: dict | None) -> dict | None:
    """Transforme la réponse API HF en entrée pour notre fit (min_ram_gb, etc.)."""
    safetensors = info.get("safetensors") or {}
    total_params = safetensors.get("total")
    if not total_params and isinstance(safetensors.get("parameters"), dict):
        total_params = max(safetensors["parameters"].values(), default=0)
    if not total_params or total_params <= 0:
        return None

    config = info.get("config") or {}
    pipeline_tag = info.get("pipeline_tag")
    min_ram, rec_ram = _estimate_ram(total_params)
    min_vram = _estimate_vram(total_params)
    ctx = _infer_context_length(full_config or config)
    created = info.get("createdAt") or ""
    last_mod = info.get("lastModified") or info.get("updatedAt") or ""

    return {
        "name": repo_id,
        "provider": _extract_provider(repo_id),
        "parameter_count": _format_param_count(total_params),
        "parameters_raw": total_params,
        "min_ram_gb": min_ram,
        "recommended_ram_gb": rec_ram,
        "min_vram_gb": min_vram,
        "quantization": "Q4_K_M",
        "context_length": ctx,
        "use_case": _infer_use_case(repo_id, pipeline_tag),
        "pipeline_tag": pipeline_tag,
        # Dates Hugging Face (réelles)
        "hf_created_at": created or None,
        "hf_last_modified": last_mod or None,
        "release_date": created[:10] or None,
        "hf_likes": info.get("likes", 0),
        "hf_downloads": info.get("downloads", 0),
    }


def fetch_models_from_hf(
    model_ids: list[str] | None = None,
    limit_per_usage: int | None = None,
) -> list[dict]:
    """
    Récupère les modèles depuis l'API Hugging Face.
    Si model_ids est None : appelle l’API list (pagination) pour récupérer jusqu’à MAX_MODELS_FROM_LIST
    modèles (text-generation-inference), puis récupère le détail de chaque modèle.
    En cas d’échec de la liste, utilise TARGET_MODELS_FALLBACK.
    Ne lève pas d'exception : retourne une liste (éventuellement vide) en cas de problème réseau.
    """
    if model_ids is None:
        limit = limit_per_usage if limit_per_usage is not None else DEFAULT_LIMIT_PER_USAGE
        if limit not in ALLOWED_LIMITS_PER_USAGE:
            limit = min(ALLOWED_LIMITS_PER_USAGE, key=lambda x: abs(x - limit))
        limit = max(MIN_LIMIT_PER_USAGE, min(limit, MAX_LIMIT_PER_USAGE))
        seen = set()
        model_ids_merged = []
        for pipeline_tag in PIPELINE_TAGS_BY_USAGE:
            ids = fetch_model_ids_from_api(limit_total=limit, pipeline_filter=pipeline_tag)
            for mid in ids:
                if mid not in seen:
                    seen.add(mid)
                    model_ids_merged.append(mid)
        model_ids = model_ids_merged
        if len(model_ids) < 4:
            model_ids = TARGET_MODELS_FALLBACK
        else:
            model_ids = model_ids[:MAX_TOTAL_MODELS_TO_FETCH]
    results = []
    for repo_id in model_ids:
        try:
            info = fetch_model_info(repo_id)
            if not info:
                time.sleep(0.2)
                continue
            full_config = fetch_config_json(repo_id)
            entry = model_info_to_entry(repo_id, info, full_config)
            if entry:
                results.append(entry)
        except Exception:
            continue
        time.sleep(0.3)
    results.sort(key=lambda m: m.get("parameters_raw", 0))
    return results
