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


def test_an_imported_alias_names_the_setter_not_the_test_that_observes_it(monkeypatch):
    from tests._module_state import record_replacements, replacement_sources

    source = ModuleType("holdspeak.provider")
    alias = ModuleType("holdspeak.late_import")
    source.get_database = lambda: "real"
    modules = {source.__name__: source, alias.__name__: alias}
    before = hub_functions(modules)
    with record_replacements("test_that_patches_the_provider"):
        with monkeypatch.context() as temporary:
            temporary.setattr(source, "get_database", lambda: "test db")
            alias.get_database = source.get_database  # from provider import get_database
    with record_replacements("test_that_imports_the_alias_later"):
        after = hub_functions(modules)
        leaked = replaced_by_test(before, after)
        assert leaked == ["holdspeak.late_import.get_database"]
        origin = replacement_sources(after, leaked)[leaked[0]]
        assert "test_that_patches_the_provider patched holdspeak.provider.get_database" in origin
        assert "test_that_imports_the_alias_later" not in origin


def test_a_reused_double_keeps_both_setters_instead_of_blame_from_observation(monkeypatch):
    from tests._module_state import record_replacements, replacement_sources

    source = ModuleType("holdspeak.provider")
    source.read = lambda: "real"
    double = lambda: "test answer"
    for owner in ("first_setter", "second_setter"):
        with record_replacements(owner), monkeypatch.context() as temporary:
            temporary.setattr(source, "read", double)
    after = {(source, "read"): double}
    origin = replacement_sources(after, ["holdspeak.provider.read"])["holdspeak.provider.read"]
    assert "first_setter patched holdspeak.provider.read" in origin
    assert "second_setter patched holdspeak.provider.read" in origin
