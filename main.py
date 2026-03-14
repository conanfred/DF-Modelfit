"""
DF Modelfit — DF AI Research. Outil web : quels modèles LLM pour votre machine (RAM, CPU, GPU).
Lance le serveur API + sert l'interface HTML.
"""
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import partial
from io import StringIO
from pathlib import Path

from fastapi import Query, FastAPI, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from api.system import detect, detect_custom
from api.fit import analyser, to_dict
from api.huggingface import fetch_models_from_hf
from api.runtimes import (
    detect_all_runtimes,
    list_all_local_models,
    match_local_to_hf,
    ollama_pull_model,
    ollama_delete_model,
    ollama_model_info,
    ollama_running_models,
)
from api.chat import (
    ollama_chat_stream,
    ollama_is_available,
    ollama_list_chat_models,
    get_model_defaults,
    get_system_presets,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("df_modelfit")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    ok: bool = False
    message: str
    code: str = "error"


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "DF Modelfit"


class SystemResponse(BaseModel):
    total_ram_gb: float
    available_ram_gb: float
    cpu_cores: int
    cpu_name: str
    has_gpu: bool
    gpu_name: str | None = None
    gpu_vram_gb: float | None = None
    backend: str
    models_last_updated: str | None = None


class CustomProfileRequest(BaseModel):
    total_ram_gb: float = Field(ge=1, le=2048, description="RAM totale en Go")
    cpu_cores: int = Field(ge=1, le=1024, description="Nombre de cœurs CPU")
    gpu_vram_gb: float | None = Field(None, ge=0, le=1024, description="VRAM GPU en Go (null = pas de GPU)")
    backend: str = Field("cpu", description="Backend d'inférence (cpu, cuda, metal, rocm)")


class RefreshResponse(BaseModel):
    ok: bool
    count: int
    added: int = 0
    updated: int = 0
    message: str
    last_updated: str | None = None


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODELS
    MODELS = load_models()
    logger.info("Loaded %d models at startup", len(MODELS))
    yield


app = FastAPI(title="DF Modelfit", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5050", "http://127.0.0.1:5050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_REFRESH_RATE_LIMIT_MINUTES = 5
_refresh_last_by_ip: dict[str, float] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_iso(s: str | None) -> datetime | None:
    """Parse une chaîne ISO 8601 et renvoie toujours un datetime *aware* en UTC."""
    if not s:
        return None
    try:
        s_norm = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s_norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _model_status(model: dict, last_updated: str | None) -> str | None:
    if not last_updated:
        return None
    t_end = _parse_iso(last_updated)
    if t_end is None:
        return None
    t_created_hf = _parse_iso(model.get("hf_created_at") or model.get("release_date"))
    t_modified_hf = _parse_iso(model.get("hf_last_modified") or model.get("updated_at"))
    window_days = 30 * 24 * 3600
    if t_created_hf is not None and abs((t_end - t_created_hf).total_seconds()) <= window_days:
        return "new"
    if (
        t_modified_hf is not None
        and t_created_hf is not None
        and t_modified_hf > t_created_hf
        and abs((t_end - t_modified_hf).total_seconds()) <= window_days
    ):
        return "updated"
    return None


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_PATHS = [
    DATA_DIR / "hf_models.json",
    DATA_DIR / "models.json",
]
DATA_ORIGINAL = DATA_DIR / "hf_models_original.json"
LAST_UPDATE_FILE = DATA_DIR / "last_update.json"
MIN_MODELS_USE_ORIGINAL = 50
MIN_MODELS_TO_SAVE = 4

MODELS: list[dict] = []


def _read_last_updated() -> str | None:
    if not LAST_UPDATE_FILE.exists():
        return None
    try:
        with open(LAST_UPDATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("last_updated")
    except (json.JSONDecodeError, OSError):
        return None


def _save_models_and_date(models_list: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    hf_path = DATA_DIR / "hf_models.json"
    with open(hf_path, "w", encoding="utf-8") as f:
        json.dump(models_list, f, ensure_ascii=False, indent=2)
    now = datetime.now(timezone.utc).isoformat()
    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_updated": now}, f, indent=2)


def _merge_models(existing: list[dict], fetched: list[dict], now_iso: str) -> tuple[list[dict], int, int]:
    by_name: dict[str, dict] = {m.get("name") or "": m for m in existing if m.get("name")}
    added = 0
    updated = 0
    for f in fetched:
        name = f.get("name") or ""
        if not name:
            continue
        if name in by_name:
            old = by_name[name]
            created = old.get("created_at") or (old.get("release_date") or "2020-01-01")[:10] + "T00:00:00+00:00"
            old.clear()
            old.update(f)
            old["updated_at"] = now_iso
            old["created_at"] = created
            updated += 1
        else:
            entry = dict(f)
            entry["created_at"] = now_iso
            entry["updated_at"] = now_iso
            by_name[name] = entry
            added += 1
    for entry in by_name.values():
        if "updated_at" not in entry or "created_at" not in entry:
            old_date = (entry.get("release_date") or "2020-01-01")[:10] + "T00:00:00+00:00"
            if "updated_at" not in entry:
                entry["updated_at"] = old_date
            if "created_at" not in entry:
                entry["created_at"] = old_date
    merged = list(by_name.values())
    merged.sort(key=lambda x: x.get("parameters_raw") or 0)
    return merged, added, updated


def load_models() -> list[dict]:
    for p in (*DATA_PATHS, DATA_ORIGINAL):
        if not p or not p.exists():
            continue
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, list):
            continue
        if p != DATA_ORIGINAL and len(data) < MIN_MODELS_USE_ORIGINAL and DATA_ORIGINAL.exists():
            try:
                with open(DATA_ORIGINAL, encoding="utf-8") as fo:
                    orig = json.load(fo)
                if isinstance(orig, list) and len(orig) > len(data):
                    return orig
            except (json.JSONDecodeError, OSError):
                pass
        return data
    return [
        {
            "name": "meta-llama/Llama-3.2-3B",
            "provider": "Meta",
            "parameter_count": "3B",
            "min_ram_gb": 2.5,
            "recommended_ram_gb": 5.0,
            "min_vram_gb": 2.0,
            "quantization": "Q4_K_M",
            "context_length": 128000,
            "use_case": "Général",
        },
        {
            "name": "Qwen/Qwen2.5-7B-Instruct",
            "provider": "Qwen",
            "parameter_count": "7B",
            "min_ram_gb": 5.0,
            "recommended_ram_gb": 10.0,
            "min_vram_gb": 4.5,
            "quantization": "Q4_K_M",
            "context_length": 32768,
            "use_case": "Chat, instruction",
        },
        {
            "name": "Mistral-7B-Instruct",
            "provider": "Mistral",
            "parameter_count": "7B",
            "min_ram_gb": 5.0,
            "recommended_ram_gb": 10.0,
            "min_vram_gb": 4.5,
            "quantization": "Q4_K_M",
            "context_length": 32768,
            "use_case": "Chat",
        },
    ]


# ---------------------------------------------------------------------------
# API router
# ---------------------------------------------------------------------------

api_router = APIRouter(prefix="/api", tags=["api"])


@api_router.get("/health", response_model=HealthResponse)
def api_health():
    """Vérifie que le serveur DF Modelfit répond."""
    return HealthResponse()


@api_router.post("/reset-original")
def api_reset_original():
    """Restaure data/hf_models.json à partir de data/hf_models_original.json."""
    global MODELS
    if not DATA_ORIGINAL.exists():
        raise HTTPException(status_code=404, detail="Fichier hf_models_original.json introuvable.")
    try:
        with open(DATA_ORIGINAL, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise HTTPException(status_code=422, detail="Format invalide dans hf_models_original.json.")
        now_iso = datetime.now(timezone.utc).isoformat()
        for m in data:
            if "created_at" not in m:
                m["created_at"] = now_iso
            if "updated_at" not in m:
                m["updated_at"] = now_iso
        MODELS = data
        _save_models_and_date(MODELS)
        logger.info("Original models restored: %d models", len(MODELS))
        return {"ok": True, "count": len(MODELS), "message": f"Liste d'origine restaurée ({len(MODELS)} modèles)."}
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to restore original models: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.api_route("/refresh", methods=["GET", "POST"])
async def api_refresh(request: Request, max_models: int | None = Query(None, ge=5, le=20)):
    """Mise à jour : récupère les modèles depuis Hugging Face (non-bloquant)."""
    global MODELS
    client_ip = request.client.host if request.client else "unknown"
    now_ts = time.time()
    last_ts = _refresh_last_by_ip.get(client_ip, 0)
    if now_ts - last_ts < _REFRESH_RATE_LIMIT_MINUTES * 60:
        raise HTTPException(
            status_code=429,
            detail=f"Refresh limité à une fois toutes les {_REFRESH_RATE_LIMIT_MINUTES} minutes. Réessayez plus tard.",
        )
    if max_models is not None and max_models not in (5, 10, 15, 20):
        max_models = 20
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        existing = load_models()
        fetched = await loop.run_in_executor(
            None, partial(fetch_models_from_hf, limit_per_usage=max_models)
        )
        now_iso = datetime.now(timezone.utc).isoformat()
        merged, added, updated = _merge_models(existing, fetched, now_iso)
        if len(merged) < len(existing) and len(fetched) < MIN_MODELS_TO_SAVE:
            logger.warning("HF returned too few models (%d), keeping existing data", len(fetched))
            return RefreshResponse(
                ok=False,
                count=len(fetched),
                message=f"HF a renvoyé {len(fetched)} modèle(s). Données non modifiées.",
                last_updated=_read_last_updated(),
            )
        MODELS = merged
        _save_models_and_date(MODELS)
        last = _read_last_updated()
        logger.info("HF refresh: %d total, %d added, %d updated", len(merged), added, updated)
        return RefreshResponse(
            ok=True,
            count=len(merged),
            added=added,
            updated=updated,
            message=f"{len(merged)} modèle(s) au total. {added} nouveau(x), {updated} mis à jour. Données enregistrées.",
            last_updated=last,
        )
    except Exception as e:
        logger.error("HF refresh failed: %s", e, exc_info=True)
        return RefreshResponse(
            ok=False, count=0, message=str(e), last_updated=_read_last_updated()
        )
    finally:
        _refresh_last_by_ip[client_ip] = time.time()


app.include_router(api_router)


# ---------------------------------------------------------------------------
# Main endpoints
# ---------------------------------------------------------------------------

@app.get("/api/system", response_model=SystemResponse)
def api_system():
    """Spécifications matérielles détectées."""
    s = detect()
    out = SystemResponse(
        total_ram_gb=s.total_ram_gb,
        available_ram_gb=s.available_ram_gb,
        cpu_cores=s.cpu_cores,
        cpu_name=s.cpu_name,
        has_gpu=s.has_gpu,
        gpu_name=s.gpu_name,
        gpu_vram_gb=s.gpu_vram_gb,
        backend=s.backend,
        models_last_updated=_read_last_updated(),
    )
    return out


@app.post("/api/system/custom")
def api_system_custom(profile: CustomProfileRequest):
    """Analyse avec un profil matériel personnalisé (mode manuel)."""
    custom_specs = detect_custom(
        total_ram_gb=profile.total_ram_gb,
        cpu_cores=profile.cpu_cores,
        gpu_vram_gb=profile.gpu_vram_gb,
        backend=profile.backend,
    )
    last = _read_last_updated()
    results = []
    for m in MODELS:
        try:
            f = analyser(m, custom_specs)
            d = to_dict(f)
        except Exception:
            continue
        d["status"] = _model_status(m, last)
        results.append(d)
    order = {"parfait": 0, "bon": 1, "marginal": 2, "trop_juste": 3}
    results.sort(key=lambda x: (order.get(x["fit_level"], 4), -x["utilisation_pct"]))
    system_dict = {
        "total_ram_gb": custom_specs.total_ram_gb,
        "available_ram_gb": custom_specs.available_ram_gb,
        "cpu_cores": custom_specs.cpu_cores,
        "cpu_name": custom_specs.cpu_name,
        "has_gpu": custom_specs.has_gpu,
        "gpu_name": custom_specs.gpu_name,
        "gpu_vram_gb": custom_specs.gpu_vram_gb,
        "backend": custom_specs.backend,
    }
    out = {"system": system_dict, "models": results, "custom": True}
    if last is not None:
        out["last_updated"] = last
    return out


@app.get("/api/models")
def api_models(search: str | None = None, fit: str | None = None):
    """Liste des modèles avec niveau de fit pour la machine actuelle."""
    system = detect()
    last = _read_last_updated()
    results = []
    for m in MODELS:
        try:
            f = analyser(m, system)
            d = to_dict(f)
        except Exception:
            logger.debug("Skipping model %s: analysis failed", m.get("name", "?"), exc_info=True)
            continue
        if search:
            q = search.lower()
            name_lower = (m.get("name") or "").lower()
            prov_lower = (m.get("provider") or "").lower()
            if q not in name_lower and q not in prov_lower:
                continue
        if fit and f.fit_level != fit:
            continue
        d["status"] = _model_status(m, last)
        results.append(d)
    order = {"parfait": 0, "bon": 1, "marginal": 2, "trop_juste": 3}
    results.sort(key=lambda x: (order.get(x["fit_level"], 4), -x["utilisation_pct"]))
    out = {"system": api_system(), "models": results}
    if last is not None:
        out["last_updated"] = last
    return out


@app.get("/api/models/top")
def api_models_top(limit: int = Query(10, ge=1, le=100)):
    """Top modèles qui passent sur la machine."""
    system = detect()
    runnable = []
    for m in MODELS:
        f = analyser(m, system)
        if f.fit_level != "trop_juste":
            runnable.append(to_dict(f))
    runnable.sort(key=lambda x: (-x["utilisation_pct"], x["mem_requise_gb"]))
    return {"system": api_system(), "models": runnable[:limit]}


@app.get("/api/recommend")
def api_recommend(
    use_case: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    min_fit: str | None = "marginal",
    max_params: float | None = Query(None, ge=0),
    min_context: int | None = Query(None, ge=0),
):
    """Recommandation de modèles selon le cas d'usage et quelques filtres."""
    try:
        system = detect()
        last = _read_last_updated()
        use_case_filter = (use_case or "").strip().lower()
        fit_order = {"parfait": 0, "bon": 1, "marginal": 2, "trop_juste": 3}
        min_fit_rank = fit_order.get((min_fit or "").lower(), None)
        results: list[dict] = []
        for m in MODELS:
            try:
                f = analyser(m, system)
                d = to_dict(f)
            except Exception:
                continue
            if min_fit_rank is not None and fit_order.get(f.fit_level, 99) > min_fit_rank:
                continue
            if use_case_filter:
                blob = " ".join([
                    str(m.get("use_case") or ""),
                    str(m.get("name") or ""),
                    str(m.get("provider") or ""),
                ]).lower()
                if use_case_filter not in blob:
                    continue
            if max_params is not None:
                params_raw = m.get("parameters_raw")
                if params_raw is not None:
                    params_b = float(params_raw) / 1e9
                    if params_b > float(max_params):
                        continue
            if min_context is not None:
                ctx = int(m.get("context_length") or 0)
                if ctx < int(min_context):
                    continue
            d["status"] = _model_status(m, last)
            results.append(d)
        results.sort(key=lambda x: (
            -float(x.get("score") or 0.0),
            fit_order.get(x.get("fit_level"), 99),
            -float(x.get("utilisation_pct") or 0.0),
        ))
        if limit is not None and limit > 0:
            results = results[:int(limit)]
        out = {"system": api_system(), "models": results}
        if last is not None:
            out["last_updated"] = last
        return out
    except Exception:
        logger.error("Recommend endpoint failed", exc_info=True)
        try:
            out = {"system": api_system(), "models": []}
        except Exception:
            out = {"system": None, "models": []}
        last = _read_last_updated()
        if last is not None:
            out["last_updated"] = last
        return out


# ---------------------------------------------------------------------------
# Export endpoints (CSV / JSON)
# ---------------------------------------------------------------------------

@app.get("/api/export/json")
def api_export_json():
    """Exporte tous les modèles avec fit en JSON."""
    system = detect()
    last = _read_last_updated()
    results = []
    for m in MODELS:
        try:
            f = analyser(m, system)
            d = to_dict(f)
            d["status"] = _model_status(m, last)
            results.append(d)
        except Exception:
            continue
    return JSONResponse(
        content=results,
        headers={
            "Content-Disposition": "attachment; filename=df_modelfit_export.json",
        },
    )


@app.get("/api/export/csv")
def api_export_csv():
    """Exporte tous les modèles avec fit en CSV."""
    system = detect()
    last = _read_last_updated()
    buf = StringIO()
    headers = [
        "name", "provider", "parameter_count", "fit_level", "mode",
        "mem_requise_gb", "mem_dispo_gb", "utilisation_pct",
        "score", "score_quality", "score_speed", "score_fit", "score_context",
        "estimated_tps", "context_length", "use_case", "status",
    ]
    buf.write(",".join(headers) + "\n")
    for m in MODELS:
        try:
            f = analyser(m, system)
            d = to_dict(f)
            status = _model_status(m, last) or ""
            row = [
                str(d["model"].get("name", "")),
                str(d["model"].get("provider", "")),
                str(d["model"].get("parameter_count", "")),
                str(d["fit_level"]),
                str(d["mode"]),
                str(d["mem_requise_gb"]),
                str(d["mem_dispo_gb"]),
                str(d["utilisation_pct"]),
                str(d["score"]),
                str(d["score_quality"]),
                str(d["score_speed"]),
                str(d["score_fit"]),
                str(d["score_context"]),
                str(d["estimated_tps"]),
                str(d["model"].get("context_length", "")),
                str(d["model"].get("use_case", "")),
                status,
            ]
            row = ['"' + v.replace('"', '""') + '"' for v in row]
            buf.write(",".join(row) + "\n")
        except Exception:
            continue
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=df_modelfit_export.csv"},
    )


# ---------------------------------------------------------------------------
# Changelog endpoint
# ---------------------------------------------------------------------------

@app.get("/api/changelog")
def api_changelog():
    """Retourne les modèles récemment ajoutés/mis à jour (changelog HF)."""
    last = _read_last_updated()
    if not last:
        return {"entries": [], "last_updated": None}
    entries = []
    for m in MODELS:
        status = _model_status(m, last)
        if status:
            entries.append({
                "name": m.get("name", "?"),
                "provider": m.get("provider", "?"),
                "status": status,
                "created_at": m.get("created_at"),
                "updated_at": m.get("updated_at"),
                "parameter_count": m.get("parameter_count", "?"),
            })
    entries.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return {"entries": entries[:50], "last_updated": last}


# ---------------------------------------------------------------------------
# Runtime management endpoints
# ---------------------------------------------------------------------------

@app.get("/api/runtimes")
def api_runtimes():
    """Détecte les runtimes IA installés (Ollama, LM Studio, llama.cpp)."""
    runtimes = detect_all_runtimes()
    local_models = list_all_local_models()
    matched = match_local_to_hf(local_models, MODELS)
    return {
        "runtimes": runtimes,
        "local_models": local_models,
        "local_count": len(local_models),
        "matched_count": len(matched),
    }


@app.get("/api/runtimes/models")
def api_runtimes_models():
    """Liste tous les modèles installés localement."""
    local_models = list_all_local_models()
    matched = match_local_to_hf(local_models, MODELS)
    return {
        "models": local_models,
        "matched": {k: v for k, v in matched.items()},
    }


@app.get("/api/runtimes/running")
def api_runtimes_running():
    """Liste les modèles actuellement chargés en mémoire."""
    return {"models": ollama_running_models()}


@app.post("/api/runtimes/install")
async def api_runtimes_install(request: Request):
    """Installe (pull) un modèle dans Ollama."""
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(422, "Le nom du modèle est requis.")
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ollama_pull_model, name)
    logger.info("Install model %s: %s", name, result)
    return result


@app.post("/api/runtimes/delete")
async def api_runtimes_delete(request: Request):
    """Supprime un modèle d'Ollama."""
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(422, "Le nom du modèle est requis.")
    result = ollama_delete_model(name)
    logger.info("Delete model %s: %s", name, result)
    return result


@app.get("/api/runtimes/model/{name:path}")
def api_runtimes_model_info(name: str):
    """Détails d'un modèle Ollama installé."""
    info = ollama_model_info(name)
    if info is None:
        raise HTTPException(404, f"Modèle {name} non trouvé.")
    return info


# ---------------------------------------------------------------------------
# Chat endpoints
# ---------------------------------------------------------------------------

@app.get("/api/chat/models")
def api_chat_models():
    """Liste les modèles avec capacités et paramètres par défaut."""
    available = ollama_is_available()
    models = ollama_list_chat_models() if available else []
    for m in models:
        m["defaults"] = get_model_defaults(m)
    return {"available": available, "models": models}


@app.get("/api/chat/presets")
def api_chat_presets():
    """Retourne les presets de system prompts."""
    return {"presets": get_system_presets()}


@app.post("/api/chat")
async def api_chat(request: Request):
    """Chat streaming avec paramètres complets (SSE)."""
    body = await request.json()
    model = body.get("model", "").strip()
    messages = body.get("messages", [])
    system_prompt = body.get("system_prompt")
    options = body.get("options")
    if not model:
        raise HTTPException(422, "Le nom du modèle est requis.")
    if not messages:
        raise HTTPException(422, "Au moins un message est requis.")

    import asyncio

    async def generate():
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None,
            lambda: list(ollama_chat_stream(
                model, messages, system_prompt, options,
            )),
        )
        for chunk in chunks:
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Static files & pages
# ---------------------------------------------------------------------------

static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def index():
    """Page d'accueil."""
    index_html = PROJECT_ROOT / "static" / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    raise HTTPException(404, "static/index.html introuvable")


@app.get("/support")
def support_page():
    """Page de soutien financier à la recherche."""
    support_html = PROJECT_ROOT / "static" / "support.html"
    if not support_html.exists():
        raise HTTPException(404, "support.html introuvable")
    return FileResponse(support_html, media_type="text/html")


@app.get("/license")
def license_txt():
    """Fichier de licence."""
    lic_path = PROJECT_ROOT / "LICENSE"
    if not lic_path.exists():
        raise HTTPException(404, "LICENSE introuvable")
    return FileResponse(lic_path, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    print("DF Modelfit: demarrage sur http://0.0.0.0:5050 (ouvrez http://localhost:5050)")
    uvicorn.run(app, host="0.0.0.0", port=5050)
