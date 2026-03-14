# AGENTS.md

## Cursor Cloud specific instructions

**DF Modelfit** is a single-process Python FastAPI app (LLM recommendation tool). No database, no Docker, no external services required.

### Running the app

```bash
python main.py
```

Server starts on **http://localhost:5050**. The frontend is served as static files by FastAPI (no separate build step).

### Lint & tests

- Lint: `python3 -m flake8 .` — CI runs two passes (critical errors, then warnings with `--exit-zero`). See `.github/workflows/python-package.yml`.
- Tests: `python3 -m pytest tests/ -v` — 121 tests covering fit scoring, system detection, API routes, chat, runtimes, and HF utilities.
- Coverage: `python3 -m pytest tests/ --cov=api --cov=main --cov-report=term-missing`

### Notes

- `HF_TOKEN` env var is optional (only needed for gated Hugging Face model refresh via `/api/refresh`).
- Model data ships pre-populated in `data/hf_models.json`; the app works fully offline.
- `detect()` in `api/system.py` uses a 30 s TTL cache; call with `use_cache=False` to bypass.
- The HF refresh endpoint (`/api/refresh`) runs in an executor (non-blocking); rate-limited to 1 call per IP every 5 min.
- The chat panel requires Ollama running locally (`http://localhost:11434`) for actual AI chat. Without Ollama the UI still loads but shows "Ollama non démarré".
- Chat API: `GET /api/chat/models`, `GET /api/chat/presets`, `POST /api/chat` (SSE streaming). Backend in `api/chat.py`, frontend in `static/app.js` (Chat Panel section).
