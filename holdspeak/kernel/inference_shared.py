"""Shared canonical material helpers for inference operation codecs."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

_REVISION = re.compile(r"^[^\r\n]{1,160}$")


def executor_identity(target_id: str) -> str:
    digest = hashlib.sha256(target_id.encode()).hexdigest()[:16]
    return f"inference-{digest}"


def digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
