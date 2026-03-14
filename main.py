"""
DF Modelfit — DF AI Research. Outil web : quels modèles LLM pour votre machine (RAM, CPU, GPU).
Lance le serveur API + sert l’interface HTML.
"""
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Query

from fastapi import FastAPI, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.system import detect, SystemSpecs
from api.fit import analyser, to_dict
from api.huggingface import fetch_models_from_hf


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODELS
    MODELS = load_models()
    yield


app = FastAPI(title="DF Modelfit", version="1.0.0", lifespan=lifespan)

# CORS : autoriser les requêtes depuis d'autres origines (ex. front sur autre port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit pour /api/refresh : 1 appel par IP toutes les 5 minutes
_REFRESH_RATE_LIMIT_MINUTES = 5
_refresh_last_by_ip: dict[str, float] = {}


def _parse_iso(s: str | None) -> datetime | None:
    """
    Parse une chaîne ISO 8601 et renvoie toujours un datetime *aware* en UTC.

    - Accepte les formes avec ou sans timezone (ex. '2024-02-10', '2024-02-10T00:00:00', '...Z').
    - Les dates sans timezone sont interprétées comme UTC.
    """
    if not s:
        return None
    try:
        # Normaliser le suffixe 'Z' en offset explicite
        s_norm = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s_norm)
        # Si la date est naive (pas de timezone), on l'interprète comme UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _model_status(model: dict, last_updated: str | None) -> str | None:
    """
    Statut par rapport aux dates Hugging Face :
    - 'new'     : modèle récemment créé sur HF (hf_created_at proche de la dernière mise à jour locale)
    - 'updated' : modèle plus ancien mais récemment modifié sur HF (hf_last_modified proche de la dernière mise à jour locale)
    """
    if not last_updated:
        return None
    t_end = _parse_iso(last_updated)
    if t_end is None:
        return None
    t_created_hf = _parse_iso(model.get("hf_created_at") or model.get("release_date"))
    t_modified_hf = _parse_iso(model.get("hf_last_modified") or model.get("updated_at"))
    # Fenêtre de 30 jours pour considérer qu'un événement est "récent" par rapport à la dernière mise à jour locale
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

# Charger les modèles une fois au démarrage
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_PATHS = [
    DATA_DIR / "hf_models.json",
    DATA_DIR / "models.json",
]
# Fichier de référence : liste d’origine (100 modèles) pour ne pas repartir de zéro.
DATA_ORIGINAL = DATA_DIR / "hf_models_original.json"
LAST_UPDATE_FILE = DATA_DIR / "last_update.json"
MIN_MODELS_USE_ORIGINAL = 50  # Si le fichier chargé a moins de modèles, on préfère l'original

MODELS: list[dict] = []


def _read_last_updated() -> str | None:
    """Lit la date de dernière mise à jour des modèles (fichier JSON local)."""
    if not LAST_UPDATE_FILE.exists():
        return None
    try:
        with open(LAST_UPDATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("last_updated")
    except (json.JSONDecodeError, OSError):
        return None


def _save_models_and_date(models_list: list[dict]) -> None:
    """Enregistre la liste des modèles dans data/hf_models.json et la date dans data/last_update.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    hf_path = DATA_DIR / "hf_models.json"
    with open(hf_path, "w", encoding="utf-8") as f:
        json.dump(models_list, f, ensure_ascii=False, indent=2)
    now = datetime.now(timezone.utc).isoformat()
    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_updated": now}, f, indent=2)


def _merge_models(existing: list[dict], fetched: list[dict], now_iso: str) -> tuple[list[dict], int, int]:
    """
    Fusionne la liste existante avec les modèles récupérés depuis HF.
    - Modèle déjà présent : on met à jour les champs et updated_at, on garde created_at.
    - Nouveau modèle : on l’ajoute avec created_at et updated_at = now.
    Retourne (liste fusionnée, nombre ajoutés, nombre mis à jour).
    """
    by_name: dict[str, dict] = {m.get("name") or "": m for m in existing if m.get("name")}
    added = 0
    updated = 0
    for f in fetched:
        name = f.get("name") or ""
        if not name:
            continue
        if name in by_name:
            old = by_name[name]
            # Conserver une date de création ancienne pour afficher "Mis à jour" et non "Nouveau"
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
            # Modèle déjà présent mais sans dates (ancien) : on met une date ancienne pour ne pas afficher "Nouveau" ni "Mis à jour"
            old_date = (entry.get("release_date") or "2020-01-01")[:10] + "T00:00:00+00:00"
            if "updated_at" not in entry:
                entry["updated_at"] = old_date
            if "created_at" not in entry:
                entry["created_at"] = old_date
    merged = list(by_name.values())
    merged.sort(key=lambda x: x.get("parameters_raw") or 0)
    return merged, added, updated

# Routeur API (enregistré en premier pour éviter 404 sur /api/refresh)
api_router = APIRouter(prefix="/api", tags=["api"])


@api_router.get("/health")
def api_health():
    """Vérifie que le serveur DF Modelfit répond."""
    return { "status": "ok", "app": "DF Modelfit" }


@api_router.post("/reset-original")
def api_reset_original():
    """Restaure data/hf_models.json à partir de data/hf_models_original.json (liste d’origine)."""
    global MODELS
    if not DATA_ORIGINAL.exists():
        return { "ok": False, "message": "Fichier hf_models_original.json introuvable." }
    try:
        with open(DATA_ORIGINAL, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return { "ok": False, "message": "Format invalide dans hf_models_original.json." }
        now_iso = datetime.now(timezone.utc).isoformat()
        for m in data:
            if "created_at" not in m:
                m["created_at"] = now_iso
            if "updated_at" not in m:
                m["updated_at"] = now_iso
        MODELS = data
        _save_models_and_date(MODELS)
        return { "ok": True, "count": len(MODELS), "message": f"Liste d’origine restaurée ({len(MODELS)} modèles)." }
    except (json.JSONDecodeError, OSError) as e:
        return { "ok": False, "message": str(e) }


# Seuil minimal : on n’écrase le JSON que si on a au moins autant de modèles (évite de remplacer par une liste vide ou trop courte).
MIN_MODELS_TO_SAVE = 4


@api_router.api_route("/refresh", methods=["GET", "POST"])
def api_refresh(request: Request, max_models: int | None = Query(None, ge=5, le=20)):
    """Mise à jour : récupère les modèles depuis Hugging Face et enregistre dans data/hf_models.json.
    Query param max_models : max par usage, uniquement 5, 10, 15 ou 20 (défaut 20). Sélection : 75% meilleurs, 25% récents."""
    global MODELS
    # Rate limit : 1 appel par IP toutes les 5 minutes
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
        existing = load_models()
        fetched = fetch_models_from_hf(limit_per_usage=max_models)
        now_iso = datetime.now(timezone.utc).isoformat()
        merged, added, updated = _merge_models(existing, fetched, now_iso)
        if len(merged) < len(existing) and len(fetched) < MIN_MODELS_TO_SAVE:
            return {
                "ok": False,
                "count": len(fetched),
                "message": f"HF a renvoye {len(fetched)} modele(s). Donnees non modifiees.",
                "last_updated": _read_last_updated(),
            }
        MODELS = merged
        _save_models_and_date(MODELS)
        last = _read_last_updated()
        return {
            "ok": True,
            "count": len(merged),
            "added": added,
            "updated": updated,
            "message": f"{len(merged)} modèle(s) au total. {added} nouveau(x), {updated} mis à jour. Données enregistrées.",
            "last_updated": last,
        }
    except Exception as e:
        return { "ok": False, "count": 0, "message": str(e), "last_updated": _read_last_updated() }
    finally:
        _refresh_last_by_ip[client_ip] = time.time()


app.include_router(api_router)


def load_models() -> list[dict]:
    """Charge les modèles : hf_models.json, sinon models.json, sinon hf_models_original.json (liste d’origine), sinon liste minimale."""
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


@app.get("/api/system")
def api_system():
    """Spécifications matérielles détectées + date de dernière mise à jour des modèles."""
    s = detect()
    out = {
        "total_ram_gb": s.total_ram_gb,
        "available_ram_gb": s.available_ram_gb,
        "cpu_cores": s.cpu_cores,
        "cpu_name": s.cpu_name,
        "has_gpu": s.has_gpu,
        "gpu_name": s.gpu_name,
        "gpu_vram_gb": s.gpu_vram_gb,
        "backend": s.backend,
    }
    last = _read_last_updated()
    if last is not None:
        out["models_last_updated"] = last
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
            continue
        if search and search.lower() not in (m.get("name") or "").lower() and search.lower() not in (m.get("provider") or "").lower():
            continue
        if fit and f.fit_level != fit:
            continue
        d["status"] = _model_status(m, last)
        results.append(d)
    # Trier : runnable d’abord, puis par utilisation croissante
    order = { "parfait": 0, "bon": 1, "marginal": 2, "trop_juste": 3 }
    results.sort(key=lambda x: (order.get(x["fit_level"], 4), -x["utilisation_pct"]))
    out = { "system": api_system(), "models": results }
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
    return { "system": api_system(), "models": runnable[:limit] }


@app.get("/api/recommend")
def api_recommend(
    use_case: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    min_fit: str | None = "marginal",
    max_params: float | None = Query(None, ge=0),
    min_context: int | None = Query(None, ge=0),
):
    """
    Recommandation de modèles selon le cas d'usage et quelques filtres.

    Paramètres :
    - use_case : texte libre (ex. 'coding', 'chat', 'reasoning', 'edge') utilisé comme filtre souple ;
    - limit : nombre maximum de modèles retournés ;
    - min_fit : niveau de fit minimal ('parfait', 'bon', 'marginal', 'trop_juste') ;
    - max_params : nombre max de paramètres en milliards (approximation) ;
    - min_context : longueur de contexte minimale.
    """
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
                blob = " ".join(
                    [
                        str(m.get("use_case") or ""),
                        str(m.get("name") or ""),
                        str(m.get("provider") or ""),
                    ]
                ).lower()
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

        results.sort(
            key=lambda x: (
                -float(x.get("score") or 0.0),
                fit_order.get(x.get("fit_level"), 99),
                -float(x.get("utilisation_pct") or 0.0),
            )
        )
        if limit is not None and limit > 0:
            results = results[: int(limit)]

        out = {"system": api_system(), "models": results}
        if last is not None:
            out["last_updated"] = last
        return out
    except Exception:
        try:
            out = {"system": api_system(), "models": []}
        except Exception:
            out = {"system": None, "models": []}
        last = _read_last_updated()
        if last is not None:
            out["last_updated"] = last
        return out


# Fichiers statiques (HTML, CSS, JS)
static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def index():
    """Page d’accueil."""
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
    """Fichier de licence (usage public gratuit ; entreprises/laboratoires : seule licence écrite et signée acceptée)."""
    lic_path = PROJECT_ROOT / "LICENSE"
    if not lic_path.exists():
        raise HTTPException(404, "LICENSE introuvable")
    return FileResponse(lic_path, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    print("DF Modelfit: demarrage sur http://0.0.0.0:5050 (ouvrez http://localhost:5050)")
    uvicorn.run(app, host="0.0.0.0", port=5050)
