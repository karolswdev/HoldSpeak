# Parked with dead code (2026-10-05)

`tests/unit/test_workroom_context.py` tested only `holdspeak/workrooms.py`,
which had no product caller. Both are parked; see `parked/README.md`.
Nothing here runs (`tests/_parked/conftest.py`).
