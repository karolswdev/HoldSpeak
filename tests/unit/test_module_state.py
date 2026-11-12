"""A restored double is lawful; a double left in any hub module is named."""
from types import ModuleType

from tests._module_state import hub_functions, replaced_by_test


def test_a_replaced_function_is_named_and_a_restored_one_is_not(monkeypatch):
    module = ModuleType("holdspeak.example")
    original = lambda: None
    module.read = original
    modules = {module.__name__: module}
    before = hub_functions(modules)
    with monkeypatch.context() as patch:
        patch.setattr(module, "read", lambda: "test answer")
        assert replaced_by_test(before, hub_functions(modules)) == ["holdspeak.example.read"]
    assert replaced_by_test(before, hub_functions(modules)) == []


def test_a_module_imported_during_the_test_cannot_keep_its_test_double():
    module = ModuleType("holdspeak.lazy_example")
    module.read = lambda: "test answer"
    assert replaced_by_test({}, hub_functions({module.__name__: module})) == ["holdspeak.lazy_example.read"]


def test_a_recorder_cannot_leave_its_factory_in_a_hub_module():
    module = ModuleType("holdspeak.example")
    module.factory = lambda: "hub"
    module.factory.__module__ = module.__name__
    modules = {module.__name__: module}
    before = hub_functions(modules)
    module.factory = lambda: "recording rig"
    module.factory.__module__ = "scripts.record_example"
    assert replaced_by_test(before, hub_functions(modules)) == ["holdspeak.example.factory"]
