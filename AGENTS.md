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
- Tests: `python3 -m pytest` — no test files exist in the repo yet; pytest exits cleanly with "no tests ran".

### Notes

- The `backend/` directory is a legacy/unused Flask app; the main entry point is `main.py` (FastAPI).
- `HF_TOKEN` env var is optional (only needed for gated Hugging Face model refresh via `/api/refresh`).
- Model data ships pre-populated in `data/hf_models.json`; the app works fully offline.
