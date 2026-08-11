"""Uruchomienie: python -m fa3check.web"""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "fa3check.web.app:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
