"""The vitest selection of the quick check never drops a direct dependent.

scripts/vitest_related.py cuts `vitest related` in two places: a barrel edge
is followed by name, and a walk over the cap is cut by depth. These cases
prove, on a fixture graph and on the real web tree, that the cut keeps every
test that imports the changed file, every test of a module that imports it,
and every per-app T2 file.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import vitest_related as vr  # noqa: E402

FIXTURE = {
    "desk/surface/index.ts": (
        'export { Gadget } from "./gadgets";\n'
        "export {\n  // a comment in the list\n  Toolbar,\n} from \"./kit\";\n"
        'export * from "./objects";\n'
        'export type { Shape } from "./shape";\n'
    ),
    "desk/surface/objects/index.ts": 'export { List } from "./List";\n',
    "desk/surface/objects/List.tsx": "export function List() { return null; }\n",
    "desk/surface/gadgets.tsx": 'import "./gadgets.css";\nexport const Gadget = () => null;\n',
    "desk/surface/gadgets.css": ".gadget { color: red; }\n",
    "desk/surface/kit.tsx": "export const Toolbar = () => null;\n",
    "desk/surface/shape.ts": "export type Shape = { a: number };\n",
    "desk/surface/gadgets.test.tsx": 'import { Gadget } from "./gadgets";\n',
    "desk/a/AWin.tsx": 'import { Gadget } from "../surface";\nexport const AWin = Gadget;\n',
    "desk/b/BWin.tsx": 'import { Toolbar, List } from "../surface";\nexport const BWin = Toolbar;\n',
    "desk/a/__tests__/a.app.test.tsx": 'import { AWin } from "../AWin";\n',
    "desk/b/__tests__/b.app.test.tsx": 'import { BWin } from "../BWin";\n',
    "desk/star.test.ts": 'import * as S from "./surface";\n',
    "desk/typeonly.test.ts": 'import type { Gadget } from "./surface";\n',
    "desk/lazy.test.ts": 'const m = await import("./a/AWin");\n',
    "desk/mocked.test.ts": 'vi.mock("./b/BWin");\n',
    "desk/reader.test.ts": 'readFileSync("src/desk/surface/gadgets.css", "utf8");\n',
    # live code that re-exports a parked module (desk/components/SystemShade.tsx)
    "desk/_parked/Shade.tsx": 'import { Gadget } from "../surface";\nexport const Shade = Gadget;\n',
    "desk/_parked/shade.test.tsx": 'import { Shade } from "./Shade";\n',
    "desk/Shade.tsx": 'export { Shade } from "./_parked/Shade";\n',
    "desk/shade.test.tsx": 'import { Shade } from "./Shade";\n',
    # a registry two rings above AWin, and a test deep behind it
    "desk/registry.ts": 'import { AWin } from "./a/AWin";\nimport { BWin } from "./b/BWin";\n',
    "desk/store.ts": 'import "./registry";\n',
    "desk/deep.test.ts": 'import "./store";\n',
}


def _tree(tmp_path: Path) -> Path:
    src = tmp_path / "web" / "src"
    for rel, body in FIXTURE.items():
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return src


def _run(src: Path, changed: str, **kw) -> set[str]:
    return {p.removeprefix("src/") for p in vr.related([f"src/{changed}"], root=src, **kw)}


def test_a_barrel_edge_is_followed_by_name(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/surface/gadgets.css")
    assert {
        "desk/surface/gadgets.test.tsx",  # imports the component directly
        "desk/a/__tests__/a.app.test.tsx",  # AWin imports Gadget by name
        "desk/star.test.ts",  # `import * as` the barrel: everything
        "desk/lazy.test.ts",  # a dynamic import is an edge
        "desk/deep.test.ts",  # store -> registry -> AWin (under the cap)
    } <= got
    assert "desk/b/__tests__/b.app.test.tsx" not in got  # BWin names no gadget
    assert "desk/typeonly.test.ts" not in got  # a type import is erased


def test_plain_follows_every_barrel_edge_like_vitest(tmp_path):
    src = _tree(tmp_path)
    assert "desk/b/__tests__/b.app.test.tsx" in _run(src, "desk/surface/gadgets.css", plain=True)


def test_a_nested_barrel_resolves_the_name(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/surface/objects/List.tsx")
    assert {"desk/b/__tests__/b.app.test.tsx", "desk/mocked.test.ts", "desk/star.test.ts"} <= got
    assert "desk/a/__tests__/a.app.test.tsx" not in got


def test_a_change_to_the_barrel_reaches_every_importer(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/surface/index.ts")
    assert {"desk/a/__tests__/a.app.test.tsx", "desk/b/__tests__/b.app.test.tsx",
            "desk/star.test.ts"} <= got


def test_over_the_cap_keeps_the_direct_rings_and_the_app_files(tmp_path):
    src = _tree(tmp_path)
    why: list[str] = []
    got = _run(src, "desk/surface/gadgets.tsx", cap=2, why=why)
    assert "over the cap of 2" in why[0]
    # distance 1 and 2 always run, and every app file, and the path reader
    assert {"desk/surface/gadgets.test.tsx", "desk/a/__tests__/a.app.test.tsx",
            "desk/b/__tests__/b.app.test.tsx", "desk/star.test.ts"} <= got
    assert "desk/deep.test.ts" not in got  # four imports away: cut


def test_a_path_reader_runs_when_cut(tmp_path):
    src = _tree(tmp_path)
    assert "desk/reader.test.ts" in _run(src, "desk/surface/gadgets.css", cap=1)


def test_a_parked_module_is_followed_and_a_parked_test_never_runs(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/surface/gadgets.tsx")
    assert "desk/shade.test.tsx" in got
    assert "desk/_parked/shade.test.tsx" not in got


def test_a_changed_test_file_runs(tmp_path):
    src = _tree(tmp_path)
    assert _run(src, "desk/star.test.ts") == {"desk/star.test.ts"}


def test_the_real_tree_keeps_every_direct_importer():
    """On web/src: for every source file, each test that imports it (any
    edge, the barrel itself included) and each test of a module that
    imports it is selected."""
    src = vr.WEB / "src"
    graph = vr.Graph(src)
    plain = graph.reverse(True)
    missed: list[str] = []
    for f in sorted(graph.files):
        if vr.is_test(f) or f.suffix == ".json":
            continue
        got = set(vr.related([str(f.relative_to(src.parent))], root=src, graph=graph))
        for importer in plain.get(f, ()):
            if importer in graph.barrels:
                continue
            if vr.is_test(importer):
                rel = str(importer.relative_to(src.parent))
                if rel not in got:
                    missed.append(f"{rel} imports {f.relative_to(src)}")
    assert not missed, "\n".join(missed[:20])
