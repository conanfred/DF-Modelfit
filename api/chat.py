# Chat complet avec les modèles IA locaux (Ollama) — DF AI Research
import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

OLLAMA_API = "http://localhost:11434"

# Capacités connues par famille de modèle
MODEL_CAPABILITIES = {
    "llava": {"vision": True, "code": False, "default_ctx": 4096},
    "llama": {"vision": False, "code": False, "default_ctx": 8192},
    "mllama": {"vision": True, "code": False, "default_ctx": 131072},
    "qwen2": {"vision": False, "code": False, "default_ctx": 32768},
    "qwen2vl": {"vision": True, "code": False, "default_ctx": 32768},
    "command-r": {"vision": False, "code": False, "default_ctx": 131072},
    "gemma": {"vision": False, "code": False, "default_ctx": 8192},
    "gemma2": {"vision": False, "code": False, "default_ctx": 8192},
    "phi3": {"vision": False, "code": True, "default_ctx": 4096},
    "phi3.5": {"vision": False, "code": True, "default_ctx": 131072},
    "starcoder": {"vision": False, "code": True, "default_ctx": 8192},
    "codellama": {"vision": False, "code": True, "default_ctx": 16384},
    "deepseek-coder": {"vision": False, "code": True, "default_ctx": 16384},
    "mistral": {"vision": False, "code": False, "default_ctx": 32768},
    "mixtral": {"vision": False, "code": False, "default_ctx": 32768},
    "falcon": {"vision": False, "code": False, "default_ctx": 2048},
    "vicuna": {"vision": False, "code": False, "default_ctx": 2048},
    "deepseek": {"vision": False, "code": False, "default_ctx": 65536},
}

# Presets de system prompts
SYSTEM_PRESETS = {
    "default": {
        "fr": "Tu es un assistant IA utile et concis.",
        "en": "You are a helpful and concise AI assistant.",
    },
    "coder": {
        "fr": (
            "Tu es un assistant de programmation expert. "
            "Réponds avec du code bien commenté, des explications techniques précises. "
            "Utilise les bonnes pratiques et les design patterns appropriés."
        ),
        "en": (
            "You are an expert programming assistant. "
            "Reply with well-commented code and precise technical explanations. "
            "Use best practices and appropriate design patterns."
        ),
    },
    "analyst": {
        "fr": (
            "Tu es un analyste de données et modèles LLM. "
            "Aide l'utilisateur à comparer les modèles, comprendre les benchmarks, "
            "et choisir le meilleur modèle pour son usage."
        ),
        "en": (
            "You are a data and LLM model analyst. "
            "Help the user compare models, understand benchmarks, "
            "and choose the best model for their use case."
        ),
    },
    "vision": {
        "fr": (
            "Tu es un assistant IA avec capacité de vision. "
            "L'utilisateur peut partager des images ou captures d'écran. "
            "Décris et analyse le contenu visuel en détail."
        ),
        "en": (
            "You are an AI assistant with vision capability. "
            "The user may share images or screenshots. "
            "Describe and analyze the visual content in detail."
        ),
    },
    "creative": {
        "fr": (
            "Tu es un assistant créatif. Écris avec style, imagination et originalité. "
            "Propose des idées innovantes et des perspectives inattendues."
        ),
        "en": (
            "You are a creative assistant. Write with style, imagination and originality. "
            "Propose innovative ideas and unexpected perspectives."
        ),
    },
}


@dataclass
class ChatOptions:
    """Paramètres de génération Ollama."""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    num_predict: int = 2048
    repeat_penalty: float = 1.1
    seed: int = 0
    num_ctx: int = 4096
    stop: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_predict": self.num_predict,
            "repeat_penalty": self.repeat_penalty,
            "num_ctx": self.num_ctx,
        }
        if self.seed > 0:
            d["seed"] = self.seed
        if self.stop:
            d["stop"] = self.stop
        return d


def ollama_chat_stream(
    model: str,
    messages: list[dict],
    system_prompt: str | None = None,
    options: dict | None = None,
):
    """Générateur de chunks SSE depuis Ollama /api/chat (streaming)."""
    payload: dict = {
        "model": model,
        "messages": [],
        "stream": True,
    }

    if options:
        payload["options"] = options

    if system_prompt:
        payload["messages"].append({
            "role": "system", "content": system_prompt,
        })

    for msg in messages:
        entry: dict = {"role": msg.get("role", "user"), "content": msg.get("content", "")}
        if msg.get("images"):
            entry["images"] = msg["images"]
        payload["messages"].append(entry)

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/chat", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=600)
        for raw_line in resp:
            line = raw_line.decode().strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        logger.error("Ollama chat error %d: %s", e.code, body)
        yield {"error": True, "message": {"content": ""}, "detail": body[:300]}
    except Exception as e:
        logger.error("Ollama chat failed: %s", e)
        yield {"error": True, "message": {"content": ""}, "detail": str(e)}


def ollama_chat_sync(
    model: str,
    messages: list[dict],
    system_prompt: str | None = None,
    options: dict | None = None,
) -> dict:
    """Chat non-streaming."""
    payload: dict = {
        "model": model, "messages": [], "stream": False,
    }
    if options:
        payload["options"] = options
    if system_prompt:
        payload["messages"].append({"role": "system", "content": system_prompt})
    for msg in messages:
        entry: dict = {"role": msg.get("role", "user"), "content": msg.get("content", "")}
        if msg.get("images"):
            entry["images"] = msg["images"]
        payload["messages"].append(entry)

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/chat", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": True, "detail": str(e)}


def ollama_is_available() -> bool:
    try:
        req = urllib.request.Request(f"{OLLAMA_API}/api/version")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def ollama_list_chat_models() -> list[dict]:
    """Liste les modèles avec leurs capacités détectées."""
    try:
        req = urllib.request.Request(f"{OLLAMA_API}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        models = data.get("models", [])
        result = []
        for m in models:
            name = m.get("name", m.get("model", "?"))
            details = m.get("details", {})
            families = details.get("families") or []
            family = details.get("family", "")

            supports_vision = any(f in ["clip", "mllama"] for f in families)
            supports_code = any(
                kw in name.lower()
                for kw in ["code", "coder", "starcoder", "deepseek-coder"]
            )

            caps = MODEL_CAPABILITIES.get(family, {})
            if caps.get("vision"):
                supports_vision = True
            if caps.get("code"):
                supports_code = True

            default_ctx = caps.get("default_ctx", 4096)
            param_size = details.get("parameter_size", "")

            result.append({
                "name": name,
                "size_gb": round(m.get("size", 0) / (1024**3), 1),
                "family": family,
                "parameter_size": param_size,
                "quantization": details.get("quantization_level", ""),
                "supports_vision": supports_vision,
                "supports_code": supports_code,
                "default_ctx": default_ctx,
                "families": families,
                "digest": m.get("digest", "")[:12],
            })
        return result
    except Exception:
        return []


def get_model_defaults(model_info: dict) -> dict:
    """Retourne les paramètres par défaut adaptés au modèle."""
    family = model_info.get("family", "")
    caps = MODEL_CAPABILITIES.get(family, {})
    ctx = caps.get("default_ctx", 4096)

    preset = "default"
    if model_info.get("supports_vision"):
        preset = "vision"
    elif model_info.get("supports_code"):
        preset = "coder"

    return {
        "temperature": 0.7 if not model_info.get("supports_code") else 0.3,
        "top_p": 0.9,
        "top_k": 40,
        "num_predict": min(ctx, 4096),
        "repeat_penalty": 1.1,
        "num_ctx": ctx,
        "seed": 0,
        "suggested_preset": preset,
    }


def get_system_presets() -> dict:
    """Retourne tous les presets de system prompts."""
    return SYSTEM_PRESETS
