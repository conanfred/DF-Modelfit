# Chat avec les modèles IA locaux (Ollama) — DF AI Research
import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass

logger = logging.getLogger(__name__)

OLLAMA_API = "http://localhost:11434"


@dataclass
class ChatMessage:
    role: str       # "user", "assistant", "system"
    content: str
    images: list[str] | None = None  # base64 images for vision


def ollama_chat_stream(
    model: str,
    messages: list[dict],
    system_prompt: str | None = None,
):
    """
    Générateur qui yield les chunks de réponse d'Ollama en streaming.
    Chaque chunk est un dict avec au minimum {"message": {"content": "..."}}.
    """
    payload: dict = {
        "model": model,
        "messages": [],
        "stream": True,
    }

    if system_prompt:
        payload["messages"].append({
            "role": "system",
            "content": system_prompt,
        })

    for msg in messages:
        entry: dict = {
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        }
        if msg.get("images"):
            entry["images"] = msg["images"]
        payload["messages"].append(entry)

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=300)
        for raw_line in resp:
            line = raw_line.decode().strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
                yield chunk
            except json.JSONDecodeError:
                continue
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        logger.error("Ollama chat error %d: %s", e.code, body)
        yield {
            "error": True,
            "message": {"content": ""},
            "detail": f"Ollama error {e.code}: {body[:200]}",
        }
    except Exception as e:
        logger.error("Ollama chat failed: %s", e)
        yield {
            "error": True,
            "message": {"content": ""},
            "detail": str(e),
        }


def ollama_chat_sync(
    model: str,
    messages: list[dict],
    system_prompt: str | None = None,
) -> dict:
    """Chat non-streaming : retourne la réponse complète."""
    payload: dict = {
        "model": model,
        "messages": [],
        "stream": False,
    }

    if system_prompt:
        payload["messages"].append({
            "role": "system",
            "content": system_prompt,
        })

    for msg in messages:
        entry: dict = {
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        }
        if msg.get("images"):
            entry["images"] = msg["images"]
        payload["messages"].append(entry)

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode())
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": True, "detail": f"Ollama error {e.code}: {body[:200]}"}
    except Exception as e:
        return {"error": True, "detail": str(e)}


def ollama_is_available() -> bool:
    """Vérifie si Ollama répond."""
    try:
        req = urllib.request.Request(f"{OLLAMA_API}/api/version")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def ollama_list_chat_models() -> list[dict]:
    """Liste les modèles Ollama disponibles pour le chat."""
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
            supports_vision = any(
                f in ["clip", "mllama"] for f in families
            )
            result.append({
                "name": name,
                "size_gb": round(m.get("size", 0) / (1024**3), 1),
                "family": details.get("family", ""),
                "parameter_size": details.get("parameter_size", ""),
                "quantization": details.get("quantization_level", ""),
                "supports_vision": supports_vision,
            })
        return result
    except Exception:
        return []


def build_screen_context_prompt(lang: str = "fr") -> str:
    """Prompt système pour le mode vision/écran."""
    if lang == "en":
        return (
            "You are a helpful AI assistant integrated into DF Modelfit, "
            "an LLM model recommendation tool. The user may share screenshots "
            "of their screen. Analyze the content and help them with their questions. "
            "Be concise and helpful."
        )
    return (
        "Tu es un assistant IA intégré à DF Modelfit, "
        "un outil de recommandation de modèles LLM. L'utilisateur peut partager "
        "des captures d'écran. Analyse le contenu et aide-le avec ses questions. "
        "Sois concis et utile."
    )
