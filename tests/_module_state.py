"""Find test functions left installed in hub modules after fixture teardown."""
from types import FunctionType, ModuleType
from typing import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from unittest.mock import patch
from weakref import WeakKeyDictionary

_patch_owner = ContextVar("test_replacement_owner", default="")
_origins: WeakKeyDictionary = WeakKeyDictionary()


@contextmanager
def record_replacements(owner: str):
    """Keep a double's setters even when a later import retains it."""
    import pytest

    token = _patch_owner.set(owner)
    original = pytest.MonkeyPatch.setattr

    def record(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        module, name, _previous = self._setattr[-1]
        if isinstance(module, ModuleType) and module.__name__.startswith("holdspeak."):
            value = getattr(module, name)
            if (isinstance(value, FunctionType) and _patch_owner.get()
                    and not (value.__module__ or "").startswith("holdspeak.")):
                _origins.setdefault(value, set()).add((_patch_owner.get(), f"{module.__name__}.{name}"))
        return result

    try:
        with patch.object(pytest.MonkeyPatch, "setattr", record):
            yield
    finally:
        _patch_owner.reset(token)


def replacement_sources(after: dict, names: list[str]) -> dict[str, str]:
    sources = {}
    for (module, key), value in after.items():
        name = f"{module.__name__}.{key}"
        if name in names:
            origin = _origins.get(value)
            source = f"{value.__code__.co_filename}:{value.__code__.co_firstlineno} ({value.__qualname__})"
            setters = "; ".join(f"{owner} patched {target}" for owner, target in sorted(origin or ()))
            sources[name] = f"{setters}; defined at {source}" if origin else f"setter not recorded; defined at {source}"
    return sources


def hub_functions(modules: Mapping[str, ModuleType]) -> dict[tuple[ModuleType, str], FunctionType]:
    return {(module, key): value
            for name, module in tuple(modules.items())
            if name.startswith("holdspeak.") and isinstance(module, ModuleType)
            for key, value in tuple(vars(module).items())
            if isinstance(value, FunctionType)}


def replaced_by_test(before: dict, after: dict) -> list[str]:
    leaked = []
    for (module, key), value in after.items():
        original = before.get((module, key))
        origin = value.__module__ or ""
        if value is original:
            continue
        if origin.startswith("tests.") or (
            original and (original.__module__ or "").startswith("holdspeak.")
            and not origin.startswith("holdspeak.")
        ):
            leaked.append(f"{module.__name__}.{key}")
    return sorted(leaked)
