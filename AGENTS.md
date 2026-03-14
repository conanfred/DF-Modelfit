# AGENTS.md

## Cursor Cloud specific instructions

**DF Modelfit** is a single-process Python FastAPI app — an LLM model recommendation tool with integrated AI chat. No database, no Docker, no external services required.

### Project structure

```
api/
  system.py       # Hardware detection (RAM, CPU, GPU) with 30s TTL cache
  fit.py          # Fit scoring (Quality, Speed, Fit, Context, energy, cost)
  huggingface.py  # HF API integration (model listing, pagination, metadata)
  runtimes.py     # Local AI runtime detection (Ollama, LM Studio, llama.cpp)
  chat.py         # Ollama chat proxy (streaming SSE, vision, presets)
static/
  index.html      # SPA shell (chat panel, filters, comparison, runtimes)
  app.js          # Frontend logic (~2400 lines): i18n FR/EN, chat, filters, charts
  style.css       # Theming (dark/light), responsive, chat sidebar
  manifest.json   # PWA manifest
data/
  hf_models.json  # Pre-populated model database (~590 models)
tests/
  test_fit.py, test_system.py, test_api.py, test_huggingface.py,
  test_runtimes.py, test_chat.py
main.py           # FastAPI entry point (all endpoints)
pyproject.toml    # Project config with [dev] dependencies
```

### Running the app

```bash
python main.py
```

Server starts on **http://localhost:5050**. Frontend is served as static files by FastAPI (no build step). Swagger docs at `/docs`.

### Lint & tests

```bash
python3 -m flake8 .                          # lint (CI: critical errors fail, warnings exit-zero)
python3 -m pytest tests/ -v                  # 116 tests
python3 -m pytest tests/ --cov=api --cov=main --cov-report=term-missing  # with coverage
```

CI config: `.github/workflows/python-package.yml` (Python 3.9–3.12, flake8, pytest-cov, pip-audit).

### Key API endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/system` | Hardware specs (cached 30s) |
| `GET /api/models` | All models with fit scores |
| `GET /api/recommend` | Filtered recommendations |
| `POST /api/refresh` | Fetch from HF (async, rate-limited 5min/IP) |
| `POST /api/system/custom` | Custom hardware profile analysis |
| `GET /api/export/csv` | Export models as CSV |
| `GET /api/export/json` | Export models as JSON |
| `GET /api/changelog` | Recently added/updated models |
| `GET /api/runtimes` | Detect local AI runtimes |
| `POST /api/runtimes/install` | Install model via Ollama |
| `POST /api/runtimes/delete` | Delete model from Ollama |
| `GET /api/chat/models` | List chat models with capabilities |
| `GET /api/chat/presets` | System prompt presets (5 types) |
| `POST /api/chat` | Streaming chat (SSE) with full Ollama params |

### Caveats & non-obvious notes

- `HF_TOKEN` env var is optional (only for gated HF models via `/api/refresh`).
- Model data ships pre-populated in `data/hf_models.json`; the app works fully offline.
- `detect()` in `api/system.py` uses a **30s TTL cache**; pass `use_cache=False` to bypass.
- The HF refresh runs in an `asyncio` executor (non-blocking).
- The chat panel requires **Ollama running** at `http://localhost:11434`. Without it the UI loads but shows "Ollama non démarré". Install Ollama and run `ollama serve` to enable chat.
- Chat streaming uses a `threading.Thread` + `queue.Queue` pattern to yield SSE chunks incrementally (not buffered).
- Vision models (e.g. `llava:7b`) are auto-detected by family (`clip`/`mllama`). The UI shows/hides image upload controls accordingly.
- The `backend/` directory was removed (legacy Flask app, unused). Only `main.py` (FastAPI) is the entry point.
- `requirements.txt` no longer includes Flask. Use `pip install -r requirements.txt` or `pip install -e ".[dev]"` with `pyproject.toml`.
- The frontend uses vanilla JS (no build step, no npm). Chart.js is loaded from CDN with SRI integrity hash.
