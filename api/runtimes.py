# Détection et gestion des runtimes IA locaux (Ollama, LM Studio, llama.cpp…)
import json
import logging
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

OLLAMA_API = "http://localhost:11434"
LMSTUDIO_API = "http://localhost:1234"


@dataclass
class RuntimeInfo:
    name: str
    installed: bool
    running: bool
    version: str | None = None
    api_url: str | None = None
    models_count: int = 0
    error: str | None = None


@dataclass
class LocalModel:
    name: str
    runtime: str
    size_gb: float | None = None
    quantization: str | None = None
    modified_at: str | None = None
    family: str | None = None
    parameter_size: str | None = None
    format: str | None = None
    digest: str | None = None
    details: dict = field(default_factory=dict)


def _http_get_json(url: str, timeout: int = 5) -> dict | None:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _http_post_json(
    url: str,
    body: dict,
    timeout: int = 30,
) -> dict | None:
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _http_delete_json(
    url: str,
    body: dict,
    timeout: int = 15,
) -> dict | None:
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="DELETE",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        if hasattr(e, "code") and e.code == 200:
            return {"ok": True}
        return None


def _http_post_stream(
    url: str,
    body: dict,
    timeout: int = 600,
) -> list[dict]:
    """POST avec réponse en NDJSON (streaming Ollama)."""
    lines: list[dict] = []
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode().strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        logger.warning("Stream POST to %s failed: %s", url, e)
    return lines


# ── Ollama ──────────────────────────────────────────────────────────────

def detect_ollama() -> RuntimeInfo:
    """Détecte si Ollama est installé et en cours d'exécution."""
    installed = shutil.which("ollama") is not None
    if not installed:
        for p in [
            Path.home() / ".ollama",
            Path("/usr/local/bin/ollama"),
            Path("C:/Users") / os.environ.get("USERNAME", "") / "AppData" / "Local" / "Ollama",
        ]:
            if p.exists():
                installed = True
                break

    running = False
    version = None
    models_count = 0
    error = None

    if installed:
        resp = _http_get_json(f"{OLLAMA_API}/api/version")
        if resp and "version" in resp:
            running = True
            version = resp["version"]
        else:
            try:
                out = subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True, text=True, timeout=5,
                )
                if out.returncode == 0 and out.stdout.strip():
                    version = out.stdout.strip().split()[-1]
            except Exception:
                pass

        if running:
            tags = _http_get_json(f"{OLLAMA_API}/api/tags")
            if tags and "models" in tags:
                models_count = len(tags["models"])
        else:
            error = "Ollama installé mais non démarré. Lancez 'ollama serve'."

    return RuntimeInfo(
        name="Ollama",
        installed=installed,
        running=running,
        version=version,
        api_url=OLLAMA_API if running else None,
        models_count=models_count,
        error=error,
    )


def ollama_list_models() -> list[LocalModel]:
    """Liste les modèles installés dans Ollama."""
    tags = _http_get_json(f"{OLLAMA_API}/api/tags")
    if not tags or "models" not in tags:
        return []
    result = []
    for m in tags["models"]:
        size_bytes = m.get("size", 0)
        details = m.get("details", {})
        result.append(LocalModel(
            name=m.get("name", m.get("model", "?")),
            runtime="ollama",
            size_gb=round(size_bytes / (1024**3), 2) if size_bytes else None,
            quantization=details.get("quantization_level"),
            modified_at=m.get("modified_at"),
            family=details.get("family"),
            parameter_size=details.get("parameter_size"),
            format=details.get("format"),
            digest=m.get("digest"),
            details=details,
        ))
    return result


def ollama_model_info(name: str) -> dict | None:
    """Détails d'un modèle Ollama."""
    return _http_post_json(f"{OLLAMA_API}/api/show", {"name": name})


def ollama_pull_model(name: str) -> dict:
    """Télécharge (pull) un modèle dans Ollama. Bloquant."""
    logger.info("Pulling Ollama model: %s", name)
    lines = _http_post_stream(
        f"{OLLAMA_API}/api/pull",
        {"name": name, "stream": True},
        timeout=1800,
    )
    if not lines:
        return {"ok": False, "message": "Pas de réponse d'Ollama. Vérifiez qu'il tourne."}
    last = lines[-1]
    if last.get("status") == "success":
        return {"ok": True, "message": f"Modèle {name} installé avec succès."}
    error = last.get("error") or last.get("status") or "Erreur inconnue"
    return {"ok": False, "message": str(error)}


def ollama_delete_model(name: str) -> dict:
    """Supprime un modèle d'Ollama."""
    logger.info("Deleting Ollama model: %s", name)
    resp = _http_delete_json(f"{OLLAMA_API}/api/delete", {"name": name})
    if resp is not None:
        return {"ok": True, "message": f"Modèle {name} supprimé."}
    return {"ok": False, "message": f"Échec de suppression de {name}."}


def ollama_running_models() -> list[dict]:
    """Liste les modèles actuellement chargés en mémoire."""
    resp = _http_get_json(f"{OLLAMA_API}/api/ps")
    if resp and "models" in resp:
        return resp["models"]
    return []


# ── LM Studio ───────────────────────────────────────────────────────────

def detect_lmstudio() -> RuntimeInfo:
    """Détecte si LM Studio est en cours d'exécution."""
    running = False
    version = None

    resp = _http_get_json(f"{LMSTUDIO_API}/v1/models", timeout=3)
    if resp and "data" in resp:
        running = True
        models_count = len(resp.get("data", []))
    else:
        models_count = 0

    lms_dir = Path.home() / ".cache" / "lm-studio"
    installed = lms_dir.exists() or running

    return RuntimeInfo(
        name="LM Studio",
        installed=installed,
        running=running,
        version=version,
        api_url=LMSTUDIO_API if running else None,
        models_count=models_count,
        error=None if running or not installed else "LM Studio installé mais non démarré.",
    )


def lmstudio_list_models() -> list[LocalModel]:
    """Liste les modèles chargés dans LM Studio via l'API OpenAI-compatible."""
    resp = _http_get_json(f"{LMSTUDIO_API}/v1/models", timeout=5)
    if not resp or "data" not in resp:
        return []
    result = []
    for m in resp["data"]:
        result.append(LocalModel(
            name=m.get("id", "?"),
            runtime="lmstudio",
            details=m,
        ))
    return result


# ── llama.cpp / llama-server ────────────────────────────────────────────

def detect_llamacpp() -> RuntimeInfo:
    """Détecte si llama-server (llama.cpp) tourne."""
    installed = (
        shutil.which("llama-server") is not None
        or shutil.which("llama-cli") is not None
        or shutil.which("server") is not None
    )

    running = False
    for port in [8080, 8081]:
        resp = _http_get_json(f"http://localhost:{port}/health", timeout=2)
        if resp and resp.get("status") == "ok":
            running = True
            break

    return RuntimeInfo(
        name="llama.cpp",
        installed=installed,
        running=running,
        api_url=f"http://localhost:8080" if running else None,
        error=None if running or not installed else "llama.cpp installé mais non démarré.",
    )


# ── Agrégation ──────────────────────────────────────────────────────────

def detect_all_runtimes() -> list[dict]:
    """Détecte tous les runtimes IA supportés."""
    runtimes = []
    for detect_fn in [detect_ollama, detect_lmstudio, detect_llamacpp]:
        try:
            info = detect_fn()
            runtimes.append({
                "name": info.name,
                "installed": info.installed,
                "running": info.running,
                "version": info.version,
                "api_url": info.api_url,
                "models_count": info.models_count,
                "error": info.error,
            })
        except Exception as e:
            logger.warning("Runtime detection failed for %s: %s", detect_fn.__name__, e)
    return runtimes


def list_all_local_models() -> list[dict]:
    """Liste tous les modèles locaux (tous runtimes confondus)."""
    all_models: list[dict] = []

    try:
        for m in ollama_list_models():
            all_models.append({
                "name": m.name,
                "runtime": m.runtime,
                "size_gb": m.size_gb,
                "quantization": m.quantization,
                "modified_at": m.modified_at,
                "family": m.family,
                "parameter_size": m.parameter_size,
                "format": m.format,
                "digest": m.digest,
            })
    except Exception:
        pass

    try:
        for m in lmstudio_list_models():
            all_models.append({
                "name": m.name,
                "runtime": m.runtime,
                "size_gb": m.size_gb,
            })
    except Exception:
        pass

    return all_models


def match_local_to_hf(
    local_models: list[dict],
    hf_models: list[dict],
) -> dict[str, list[dict]]:
    """Associe les modèles locaux aux modèles HF par correspondance de nom."""
    result: dict[str, list[dict]] = {}
    local_names_lower = {}
    for lm in local_models:
        key = lm["name"].lower().split(":")[0]
        local_names_lower.setdefault(key, []).append(lm)

    for hf in hf_models:
        hf_name = (hf.get("name") or "").lower()
        hf_short = hf_name.split("/")[-1] if "/" in hf_name else hf_name
        matches = []
        for local_key, local_list in local_names_lower.items():
            if hf_short in local_key or local_key in hf_name:
                matches.extend(local_list)
        if matches:
            result[hf.get("name", "")] = matches
    return result
