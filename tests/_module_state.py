"""Find test functions left installed in hub modules after fixture teardown."""
from types import FunctionType, ModuleType
from typing import Mapping


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
