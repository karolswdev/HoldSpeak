"""The vitest selection of the quick check: one hop, the app files, the readers.

scripts/vitest_related.py selects, per changed file, the tests that import it
directly (a barrel by name, a re-export as the same hop), the per-app T2 files
of its app (by folder or registry entry) and the tests that name it. These
cases prove the rule on a fixture tree, and on the real web tree that no
direct test importer is dropped.
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
    "desk/named.test.ts": 'import { Toolbar } from "./surface";\n',
    "desk/a/AWin.tsx": 'import { Gadget } from "../surface";\nexport const AWin = Gadget;\n',
    "desk/a/parts/Deep.tsx": "export const Deep = 1;\n",
    "desk/a/a.css": ".a { color: red; }\n",
    "desk/b/BWin.tsx": 'import { Toolbar, List } from "../surface";\nexport const BWin = Toolbar;\n',
    "desk/a/__tests__/a.app.test.tsx": 'import { AWin } from "../AWin";\n',
    "desk/b/__tests__/b.app.test.tsx": 'import { BWin } from "../BWin";\n',
    "desk/star.test.ts": 'import * as S from "./surface";\n',
    "desk/typeonly.test.ts": 'import type { Gadget } from "./surface";\n',
    "desk/lazy.test.ts": 'const m = await import("./a/AWin");\n',
    "desk/mocked.test.ts": 'vi.mock("./b/BWin");\n',
    "desk/reader.test.ts": 'readFileSync("src/desk/surface/gadgets.css", "utf8");\n',
    # live code that re-exports a parked module
    "desk/_parked/Shade.tsx": 'import { Gadget } from "../surface";\nexport const Shade = Gadget;\n',
    "desk/_parked/shade.test.tsx": 'import { Shade } from "./Shade";\n',
    "desk/Shade.tsx": 'export { Shade } from "./_parked/Shade";\n',
    "desk/shade.test.tsx": 'import { Shade } from "./Shade";\n',
    # a store behind the registry: two hops from AWin, never selected
    "desk/store.ts": 'import { AWin } from "./a/AWin";\n',
    "desk/deep.test.ts": 'import "./store";\n',
    # the app registry: two cores in one shared folder
    "desk/applications.ts": (
        '  {\n    action: "open-bees",\n    windowId: "surface-bees",\n'
        '    load: () => import("../pages/cores/BeesCore"),\n  },\n'
        '  {\n    action: "open-wasps",\n    windowId: "surface-wasps",\n'
        '    load: () => import("../pages/cores/WaspCore"),\n  },\n'
    ),
    "pages/cores/BeesCore.tsx": "export const BeesCore = 1;\n",
    "pages/cores/WaspCore.tsx": "export const WaspCore = 1;\n",
    "pages/cores/bees/Hive.tsx": "export const Hive = 1;\n",
    "desk/__tests__/bees.app.test.tsx": "it('bees');\n",
    "desk/__tests__/wasp.app.test.tsx": "it('wasp');\n",
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


def test_one_hop_follows_a_barrel_by_name(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/surface/gadgets.tsx")
    assert {"desk/surface/gadgets.test.tsx", "desk/star.test.ts"} <= got
    assert "desk/named.test.ts" not in got  # names only Toolbar
    assert "desk/typeonly.test.ts" not in got  # a type import is erased
    assert "desk/a/__tests__/a.app.test.tsx" not in got  # two hops: AWin, then the test
    assert "desk/deep.test.ts" not in got  # no transitive walk
    assert "desk/named.test.ts" in _run(src, "desk/surface/kit.tsx")


def test_a_nested_barrel_resolves_the_name(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/surface/objects/List.tsx")
    assert "desk/star.test.ts" in got
    assert "desk/named.test.ts" not in got


def test_a_change_to_the_barrel_reaches_every_importer(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/surface/index.ts")
    assert {"desk/star.test.ts", "desk/named.test.ts"} <= got
    assert "desk/typeonly.test.ts" not in got


def test_a_re_export_is_the_same_hop_and_a_parked_test_never_runs(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/_parked/Shade.tsx")
    assert "desk/shade.test.tsx" in got  # through desk/Shade.tsx, a re-export
    assert "desk/_parked/shade.test.tsx" not in got


def test_the_app_folder_selects_its_app_file(tmp_path):
    src = _tree(tmp_path)
    got = _run(src, "desk/a/AWin.tsx")
    assert {"desk/a/__tests__/a.app.test.tsx", "desk/lazy.test.ts"} <= got
    assert "desk/b/__tests__/b.app.test.tsx" not in got
    assert _run(src, "desk/a/parts/Deep.tsx") == {"desk/a/__tests__/a.app.test.tsx"}
    assert "desk/mocked.test.ts" in _run(src, "desk/b/BWin.tsx")  # vi.mock is an edge


def test_the_registry_entry_selects_its_app_file(tmp_path):
    src = _tree(tmp_path)
    # the loaded core itself, and a file in a folder named like the app
    assert _run(src, "pages/cores/WaspCore.tsx") == {"desk/__tests__/wasp.app.test.tsx"}
    assert _run(src, "pages/cores/bees/Hive.tsx") == {"desk/__tests__/bees.app.test.tsx"}
    # pages/cores holds two cores: a sibling there belongs to neither
    assert _run(src, "pages/cores/BeesCore.tsx") == {"desk/__tests__/bees.app.test.tsx"}


def test_a_stylesheet_selects_its_app_file_and_its_readers_only(tmp_path):
    src = _tree(tmp_path)
    assert _run(src, "desk/surface/gadgets.css") == {"desk/reader.test.ts"}
    assert _run(src, "desk/a/a.css") == {"desk/a/__tests__/a.app.test.tsx"}


def test_a_changed_test_file_runs(tmp_path):
    src = _tree(tmp_path)
    assert _run(src, "desk/star.test.ts") == {"desk/star.test.ts"}


def test_why_names_each_rule_per_changed_file(tmp_path):
    src = _tree(tmp_path)
    why: list[str] = []
    vr.related(["src/desk/a/AWin.tsx", "src/desk/surface/gadgets.css"], root=src, why=why)
    assert why[0] == "src/desk/a/AWin.tsx: 2 import it, 1 app files (folder desk/a), 0 name it"
    assert why[1] == "src/desk/surface/gadgets.css: 0 import it, 0 app files (no app), 1 name it"


def test_the_real_tree_keeps_every_direct_importer():
    """On web/src: for every source file, each test that imports it by path
    is selected (the barrel cut and the re-export hop drop none). One graph
    for the whole check (graph_for caches it)."""
    graph = vr.graph_for(vr.WEB / "src")
    plain = graph.reverse(True)
    cut = graph.reverse(False)
    missed: list[str] = []
    for f in graph.files:
        if vr.is_test(f) or f.suffix in (".json", ".css"):
            continue
        direct = graph.direct_tests(f, cut)
        for importer in plain.get(f, ()):
            if vr.is_test(importer) and importer not in direct:
                missed.append(f"{importer.relative_to(graph.root)} imports {f.relative_to(graph.root)}")
    assert not missed, "\n".join(sorted(missed)[:20])


def test_the_real_tree_places_files_in_their_apps():
    """The app rule on the real registry and folders (batch 23 files)."""
    cases = {
        "src/desk/walk/walk.ts": "src/desk/walk/__tests__/walk.app.test.tsx",
        "src/pages/cores/history/MeetingRecord.tsx": "src/desk/__tests__/meetings.app.test.tsx",
        "src/pages/cores/settings/native.tsx": "src/desk/__tests__/settings.app.test.tsx",
        "src/desk/calls/CallsWindow.tsx": "src/desk/__tests__/calls.app.test.tsx",
    }
    for changed, app in cases.items():
        assert app in vr.related([changed]), changed
