"""``uv run python -m uat.conductor`` — serve the guided UAT site + API.

Localhost by default on the pinned port (8799); ``UAT_HOST=0.0.0.0`` opts
onto the LAN so a device browser can walk the sitting, and ``UAT_PORT``
overrides the port. The conductor itself carries no auth — it is a dev rig
on the trusted LAN; the *product* it boots rides its own per-run token.
"""

from __future__ import annotations

import os

import uvicorn

from .app import create_app
from .runs import _lan_ip

DEFAULT_PORT = 8799
DEFAULT_HOST = "127.0.0.1"


def main() -> None:
    host = os.environ.get("UAT_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST
    try:
        port = int(os.environ.get("UAT_PORT", str(DEFAULT_PORT)))
    except ValueError:
        port = DEFAULT_PORT

    app = create_app()

    shown = (
        "localhost"
        if host in ("127.0.0.1", "localhost")
        else _lan_ip() if host == "0.0.0.0" else host
    )
    print("=" * 60)
    print("  HoldSpeak UAT Conductor")
    print(f"  Site + API:  http://{shown}:{port}")
    print(f"  Health:      http://{shown}:{port}/api/health")
    print(f"  Ports:       conductor {port} · product-under-test 8788+ · hub 8765 untouched")
    if host == "0.0.0.0":
        print("  LAN-bound: reachable from the iPad/iPhone browser on this network.")
    print("=" * 60)

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
