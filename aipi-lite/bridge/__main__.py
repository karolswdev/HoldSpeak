"""Entrypoint for `python -m bridge`."""

from __future__ import annotations

import sys

from bridge.cli import main

if __name__ == "__main__":
    sys.exit(main())
