"""Run selected pytest nodes with HOME equal to the fake passwd home."""

from __future__ import annotations

import os
import pwd
import sys
from types import SimpleNamespace


fake_home = os.environ["HOME"]
real_getpwuid = pwd.getpwuid


def fake_getpwuid(uid: int):
    real = real_getpwuid(uid)
    return SimpleNamespace(pw_dir=fake_home, pw_uid=real.pw_uid, pw_name=real.pw_name)


pwd.getpwuid = fake_getpwuid

import pytest

raise SystemExit(pytest.main(sys.argv[1:]))
