# PARKED 2026-11-09 (fences diet, pipe/fences-diet): counts and verbatim text pinned in docs (MCP tool count, effect census numbers, built-in plugin count, the Qlippy doc sentences); each turned red on a legitimate change.
# Nothing replaces them: the README says "hundreds of tools" and no plugin count; docs/MCP_SIDECAR.md is generated from the live registry.
"""HS-32-06: a lightweight guard against the worst doc-rot returning.

The phase-29 plugin rollout made every built-in real — **zero**
``DeterministicPlugin`` stubs remain, locked at the code level by
``test_decision_announcement_drafter_plugin.py::test_no_deterministic_stub_remains``.
This guard stops the *docs* from drifting back to claiming stubs exist (the most
actively misleading historical doc-rot — see HS-32-06).

Scope is **non-PMO** live docs (`docs/*.md`, excluding `docs/evidence/` snapshots);
the PMO roadmap corpus is the historical record and is kept verbatim by design.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

def test_mcp_tool_count_claims_match_registry() -> None:
    """Published MCP counts stay pinned to the actual aggregate registry."""
    from holdspeak.mcp.tools import TOOLS

    claim = re.compile(
        r"(\d+)\s+(?:MCP\s+)?tools\s+(?:across|are organized)", re.IGNORECASE
    )
    # docs/MCP_SIDECAR.md is generated on demand from TOOLS
    # (scripts/gen_mcp_sidecar_doc.py), so its count cannot drift.
    for relative in (Path("README.md"), Path("docs/README.md")):
        text = (_REPO / relative).read_text(encoding="utf-8")
        counts = [int(value) for value in claim.findall(text)]
        assert counts, f"{relative} must state its MCP tool count"
        assert set(counts) == {len(TOOLS)}, (
            f"{relative} states MCP tool counts {counts}, registry has {len(TOOLS)}"
        )


# HS-107-06: the current effect census is stated at both security/architecture
# entry points. Parse those claims and pin them to the ledger's expected block so
# docs cannot retain an obsolete snapshot after the ledger changes.
_EFFECT_CENSUS_DOCS = (
    Path("docs/SECURITY.md"),
    Path("docs/internal/PLAN_KERNEL_OPERATION_BROKER.md"),
)
_EFFECT_CENSUS_CLAIM = re.compile(
    r"(?P<total>\d+)\s+total\s*/\s*"
    r"(?P<covered>\d+)\s+covered\s*/\s*"
    r"(?:(?P<exempt>\d+)\s+exempt[a-z\s]*?/\s*)?"
    r"(?P<debt>\d+)\s+debt",
    re.IGNORECASE,
)


def test_effect_census_doc_counts_match_ledger_expected_block() -> None:
    ledger = json.loads(
        (_REPO / "holdspeak/kernel/effect_ledger.json").read_text(encoding="utf-8")
    )
    expected_block = ledger["expected"]
    expected = (
        expected_block["total"],
        expected_block["covered"],
        expected_block.get("exempt_computation", 0),
        expected_block["not_covered"],
    )

    for relative_path in _EFFECT_CENSUS_DOCS:
        path = _REPO / relative_path
        claims = [
            (
                int(match.group("total")),
                int(match.group("covered")),
                int(match.group("exempt") or 0),
                int(match.group("debt")),
            )
            for match in _EFFECT_CENSUS_CLAIM.finditer(
                path.read_text(encoding="utf-8")
            )
        ]
        assert claims, f"{relative_path} must state 'N total / N covered / N debt'"
        assert set(claims) == {expected}, (
            f"{relative_path} effect census {claims} does not match ledger expected "
            f"block {expected}"
        )


# HS-46-01: the README headlines a built-in-plugin count ("ships **14 built-in
# plugins**"). That number drifted before and is exactly the kind of "cool fact"
# the docs lead with — pin it to the registry so it can't silently rot. Cheap:
# one import + one regex.
_PLUGIN_COUNT_CLAIM = re.compile(r"(\d+)\s+built-in plugins", re.IGNORECASE)


def test_readme_plugin_count_matches_registry() -> None:
    builtin_source = _REPO / "holdspeak/plugins/builtin/__init__.py"
    tree = ast.parse(builtin_source.read_text(encoding="utf-8"), filename=str(builtin_source))
    definition = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "_BUILTIN_PLUGIN_DEFS"
        ),
        None,
    )
    assert definition is not None and isinstance(definition.value, ast.Tuple), (
        "holdspeak/plugins/builtin/__init__.py must define _BUILTIN_PLUGIN_DEFS "
        "as a tuple literal"
    )
    registry_count = len(definition.value.elts)
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    claims = [int(m) for m in _PLUGIN_COUNT_CLAIM.findall(readme)]

    assert claims, (
        "README no longer states a built-in-plugin count ('N built-in plugins'). "
        "If the phrasing changed, update this guard; otherwise restore the count."
    )
    mismatched = [n for n in claims if n != registry_count]
    assert not mismatched, (
        f"README advertises {mismatched} built-in plugins but the registry has "
        f"{registry_count} (holdspeak/plugins/builtin/_BUILTIN_PLUGIN_DEFS). "
        "Reconcile the count and the plugin table."
    )



def test_qlippy_doc_states_the_guarantees_verbatim() -> None:
    """HS-56-06 / revised HS-62-01: the mascot doc keeps the never-acts
    guarantee, and the cards state egress with the BADGE, never a privacy
    paragraph (the owner's Quiet Trust direction — one symbol, no novels)."""
    guide = (_REPO / "docs" / "DICTATION_PIPELINE_GUIDE.md").read_text()
    assert "Qlippy, the mascot" in guide
    assert "never acts on his own" in guide
    assert "the egress badge" in guide  # the documented contract
    # The cards pass structured egress states; the retired privacy
    # paragraphs must never come back.
    events = (_REPO / "web/src/components/AmbientLayer.tsx").read_text()
    assert "actuator_proposed" in events
    assert "Approve" in events and "Decline" in events
    for retired in ("Data used:", "If you approve, this goes to", "Your controls:",
                    "nothing leaves", "stays on this machine"):
        assert retired not in events, f"privacy prose crept back: {retired!r}"
