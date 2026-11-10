"""The residual reader recognizes constructions and ignores parked routes."""
from scripts.residual_census import _http


def test_a_route_construction_is_found_in_its_function_and_leaves_when_parked(tmp_path):
    routes = tmp_path / "holdspeak" / "web" / "routes"
    routes.mkdir(parents=True)
    route = routes / "example.py"
    route.write_text("def read():\n    return ExampleService().read()\n")
    [entry] = _http(tmp_path)
    assert entry["entry_point"] == "holdspeak/web/routes/example.py::read"
    assert entry["discriminator"] == "ExampleService"
    parked = routes / "_parked"
    parked.mkdir()
    route.rename(parked / route.name)
    assert _http(tmp_path) == []
