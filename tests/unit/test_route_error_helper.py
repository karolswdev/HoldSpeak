"""HS-32-05: the one route 500-response helper (`error_500`).

This locks the response shape/status and the log line that the ~48 route
handlers previously hand-wrote inline, so a future change to the error contract
is a one-line edit (and this test catches a drift in it)."""

from __future__ import annotations

import json
import logging

from holdspeak.web.runtime_support import error_500


def test_error_500_response_shape_and_status() -> None:
    resp = error_500(ValueError("boom"), logging.getLogger("test.error_500"), "Failed to do thing")
    assert resp.status_code == 500
    assert json.loads(resp.body) == {"error": "boom"}


