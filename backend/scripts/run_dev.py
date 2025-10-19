from __future__ import annotations

import os
from pathlib import Path

import uvicorn


BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8000


def _resolve_reload_dirs() -> list[str]:
    """Limit auto-reload watchers to code directories to avoid scanning `.venv` on WSL."""
    candidate_dirs = [
        BACKEND_ROOT / "app",
        BACKEND_ROOT / "tests",
    ]
    return [str(path) for path in candidate_dirs if path.exists()]


def main() -> None:
    port = int(os.getenv("PORT", DEFAULT_PORT))

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=port,
        reload=True,
        reload_dirs=_resolve_reload_dirs(),
        reload_excludes=[
            "*/.venv/*",
            "*/__pycache__/*",
            "*/data/*",
        ],
    )


if __name__ == "__main__":
    main()

