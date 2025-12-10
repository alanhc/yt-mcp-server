# Repository Guidelines

## Project Structure & Module Organization
- Core FastAPI service is in `ubuntu_backend.py`/`backend.py`; `main.py` is the minimal MCP-only subtitle tool. Static client assets live in `static/summary_viewer.html`.
- Manual integration scripts sit at repo root as `test_*.py` and call the server on `localhost:8000`.
- Shell helpers: `start_server.sh` / `simple-start.sh` to boot with `uv`, matching stop scripts, and systemd template `yt-mcp-server.service.template`.
- `mcp-n8n-proxy/` is a sibling MCP package with its own `pyproject.toml`, tests, and README; install its deps separately.

## Build, Test, and Development Commands
- Install deps: `pip install -r requirements.txt` (or `uv pip install -r requirements.txt` to match scripts).
- Run backend: `uv run python ubuntu_backend.py` (or `./start_server.sh` for CUDA env setup).
- Launch MCP-only tool: `uv run python main.py --transport streamable-http`.
- Integration checks (server required): `python test_podcast.py`, `python test_cache.py`, `python test_async_podcast.py`. In `mcp-n8n-proxy`: `uv run pytest`.

## Coding Style & Naming Conventions
- Target Python 3.12+, PEP8 spacing (4 spaces), and type hints where feasible. Keep handlers focused and side effects obvious.
- Use snake_case for modules/functions/vars; constants in UPPER_SNAKE_CASE. Favor descriptive names like `parse_vtt`.
- Log clearly on API boundaries, never secrets. Keep temp artifacts in `/tmp/<uuid>` and clean them up.

## Testing Guidelines
- Tests are integration-heavy: run them with the server active and env vars set (`ANTHROPIC_API_KEY`, Whisper/CUDA config). Expect live calls to YouTube/Apple Podcast.
- Add unit tests for pure helpers (e.g., VTT parsing) to reduce external dependency; place alongside other `test_*.py`.
- For the n8n proxy, mock HTTP calls when adding tools to keep runs deterministic.

## Commit & Pull Request Guidelines
- Use concise, imperative commits (e.g., `Add async podcast status polling`); keep scope tight.
- In PRs, include purpose/behavior, commands run (tests, lint), and any API or env var changes. Add sample responses or screenshots for new endpoints.

## Configuration & Security Notes
- Store secrets in `.env` (loaded via `python-dotenv`); never commit keys. Ensure `ANTHROPIC_API_KEY`, optional Whisper model paths, and n8n tokens are set before running servers.
- When adding endpoints, validate inputs and clean temp artifacts to avoid leaks. Avoid broad filesystem access—stick to per-request temp dirs.
