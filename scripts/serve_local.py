from __future__ import annotations

import functools
import os
import secrets
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from packages.core.io import ROOT


def main() -> None:
    import uvicorn

    os.environ.setdefault(
        "DATABASE_URL", "sqlite:///" + str(ROOT / "data/generated/local-api.sqlite")
    )
    os.environ.setdefault("MLSPEND_SALT", secrets.token_hex(32))
    os.environ["MLSPEND_CORS_ORIGINS"] = "http://127.0.0.1:4173,http://localhost:4173"
    server = ThreadingHTTPServer(
        ("127.0.0.1", 4173),
        functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT / "web")),
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("Dashboard: http://127.0.0.1:4173  API: http://127.0.0.1:8000", flush=True)
    uvicorn.run("packages.api.app:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
