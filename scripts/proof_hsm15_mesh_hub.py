"""HSM-15-02 — the scratch hub for the mesh-dispatch proof.

Starts a REAL MeetingWebServer on loopback with the intel engine faked
in-process; every dispatched step that arrives over `POST /api/ask` is
receipted (prompt + count) to `scratchpad`-adjacent files so the driving
shell can assert the iPad Simulator's pinned step genuinely landed here.
The /api/ask route itself runs for real — only the model is faked.
"""
import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/hsm15-proof")
OUT.mkdir(parents=True, exist_ok=True)
RECEIPT = OUT / "ask-receipts.jsonl"
URLFILE = OUT / "hub-url.txt"


class _FakeIntel:
    active_provider = "local"

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        with RECEIPT.open("a") as f:
            f.write(json.dumps({"prompt": user_prompt[:200]}) + "\n")
        return "MESH RESULT: distilled on your Mac (scratch hub, faked model)."


def main():
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    get_database(tmp / "holdspeak.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host="127.0.0.1")
    url = server.start()
    URLFILE.write_text(url)
    print(f"hub up at {url}; receipts -> {RECEIPT}", flush=True)
    try:
        with patch("holdspeak.intel.providers.build_configured_meeting_intel",
                   lambda: _FakeIntel()):
            # Serve until the driver removes the url file (the stop signal).
            while URLFILE.exists():
                time.sleep(0.5)
    finally:
        server.stop()
        reset_database()
        print("hub stopped", flush=True)


if __name__ == "__main__":
    main()
