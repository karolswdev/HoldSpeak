"""Run scoped verification with isolated Python home/path resolution."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
original_expanduser = os.path.expanduser
with tempfile.TemporaryDirectory(prefix="holdspeak-interview-tests-") as directory:
    isolated = Path(directory)
    def expanduser(path):
        value = os.fspath(path)
        if isinstance(value, str) and (value == "~" or value.startswith("~/")):
            return str(isolated) + value[1:]
        return original_expanduser(path)
    with patch.object(Path, "home", return_value=isolated), patch("os.path.expanduser", side_effect=expanduser):
        import pytest
        raise SystemExit(pytest.main(sys.argv[1:]))
