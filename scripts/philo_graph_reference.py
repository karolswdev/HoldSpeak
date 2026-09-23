#!/usr/bin/env python3
"""Generate docs/generated/graph.json, the Philo graph join (brief section 8).

The join reads the four sealed passes (``static-muaddib``, ``static-astra``,
``live-muaddib``, ``live-astra``), the state atlas, the council's explicit
resolutions (``council-resolutions.json``) and the Phase 1 inventories that
the passes reference.  It writes one file.  It never merges two claims that
contradict each other: a contradiction without a council resolution stops the
generator, and the error names both sides.

Usage::

    python scripts/philo_graph_reference.py            # write the join
    python scripts/philo_graph_reference.py --check    # exit 1 on drift
    uv run --extra dev python scripts/philo_graph_reference.py --census

``--check`` proves generated consistency: the file on disk is byte-equal to a
fresh join of the committed inputs.  ``--census`` is a separate comparison of
the entry points in the CURRENT source against the edges of the join.  It
reports new, removed and changed entry points and exits 1 when it finds any
(or cannot read a catalogue).  It also lists miscited sources: a pass cited a
handler that was not in the file at the revision it examined.
It does not rewrite the join: saved observations keep their original revision,
and a regeneration never turns old execution evidence into proof of current
behaviour.

The HTTP census reads the routes from source: it assembles the app through
the route owner the Philo scripts share (``scripts/gen_api_surface.py``,
``build_reference_app``) and compares method, path and handler name with the
edges.  It does not read ``docs/generated/openapi.json`` for membership, so a
route added, removed or renamed in source shows even when OpenAPI is
unchanged.  When the committed OpenAPI no longer matches source, the census
also prints ``stale`` lines.

When you change a route:

1. Change the route in source.
2. ``uv run --extra dev python scripts/philo_openapi_reference.py``
   (regenerate OpenAPI).
3. ``python scripts/philo_graph_reference.py`` (regenerate the join).
4. ``python scripts/philo_graph_reference.py --check``.
5. ``uv run --extra dev python scripts/philo_graph_reference.py --census``.

The census names the new, removed or changed edge.  The sealed passes are not
edited to agree: a pass describes the route as it was at its recorded
revision, and that evidence is never rewritten.  A new pass or a council
resolution records the current route.

The join rules, in full:

* Nodes: one node per id.  The ``kind`` must agree in every pass (else an
  error).  ``phase1_refs`` and ``sources`` are the union, each source keeping
  its own revision.  The label comes from the first pass that has it, in the
  order above.  When the passes classify the exposure of one node
  differently, the label names every position (``[exposure disagreement:
  astra=...; muaddib=...]``) and the summary lists the node; the join does
  not choose.
* Subtypes: when every pass that gives a subtype gives the same one, the node
  has it.  When they differ, the label names every position and the summary
  lists the node.  ``SUBTYPE_NORMALIZATION`` below is the whole table of
  differences that are one classification at two granularities; such a node
  gets the finer value and ``[subtype normalized: ...]``.  Every other
  difference is a conflict: the node gets no subtype and ``[subtype
  conflict: ...]``.  Precedence never decides a subtype.
* Links: one link per (from, to, relation); evidence is the union.
* Cases: the current atlas owns the case contract.  Every case a pass names
  must be in the atlas (else an error).  A pass that ran an older revision of
  a case keeps that revision in its observation provenance.
* Observations, claim reviews and findings: copied unchanged.  A duplicate id
  with different content is an error.  Two claim reviews of one claim that
  say ``verified`` and ``contradicted`` are an error unless a finding that
  cites both has a council resolution.
* Resolutions: every finding has exactly one council resolution, and every
  finding a resolution names exists (else an error).  One resolution row is
  written per finding; a council bin that differs from the sealed bin is
  written in the disposition, beside the sealed bin.

Standard library only, so the CI documentation job can run it with a bare
``python``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = "scripts/philo_graph_reference.py/1"
OUTPUT = "docs/generated/graph.json"
GRAPH_DIR = "docs/internal/philo/graph"
# Precedence for a node's label and subtype: static before live, Muad'Dib
# before Astra within a pass kind.  Precedence never decides a contradiction.
PASSES = ("static-muaddib", "static-astra", "live-muaddib", "live-astra")
ATLAS = f"{GRAPH_DIR}/atlas.json"
RESOLUTIONS = f"{GRAPH_DIR}/council-resolutions.json"
# The revision whose council-resolutions.json is byte-equal to the file the
# join reads (PHILO-2-07 corrected the import refusal's bin after the PHILO-2-06
# council commit e58b4a14).  A resolution row cites the file at this revision.
# When the council rules again: commit the resolutions file, set this to that
# commit, regenerate.  tests/unit/test_philo_graph_reference.py proves the file
# at this revision hashes to the input the join used.
COUNCIL_REVISION = "54cf71a78e65355002cd00fc298e7919ffb7a1bf"
# Subtype normalization: the whole table.  Two different subtypes for one node
# are one classification only when a row below relates them; the node then
# gets the finer (right-hand) value.  Anything else is a conflict and stays
# unresolved in the join.
#   refinement - the finer value extends the coarser one with a dotted suffix
#                (http -> http.POST).  A rule, not rows.
#   bucket     - Astra's class names ``ui`` and ``verb`` hold a named trigger
#                or face kind.  The schema's subtype is the trigger, so the
#                named trigger is the finer value.  ``ui`` does not hold http
#                or timer: those are a conflict.
#   vocabulary - on state nodes Astra names the atlas section that holds the
#                state (atlas.meetings); Muad'Dib names the state
#                (domain.meeting).  One state, two names.
SUBTYPE_BUCKETS = {
    "ui": ("pointer.", "keyboard", "face."),
    "verb": ("pointer.click", "keyboard"),
}
SUBTYPE_VOCABULARY = {
    "atlas.briefs": "projection.brief",
    "atlas.desk_presentation": "browser.presentation",
    "atlas.engines": "projection.assignment",
    "atlas.first_value": "lifecycle.first_value",
    "atlas.meetings": "domain.meeting",
    "atlas.projections": "projection.desk",
    "atlas.time": "clock",
}
EXPOSURE = re.compile(r"\[(?:exposure=)?(active|conditional|internal|parked|historical)\]")


class JoinError(Exception):
    """The inputs contradict each other and no council resolution covers it."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


@dataclass
class Inputs:
    passes: dict[str, dict]
    atlas: dict
    resolutions: dict
    hashes: dict[str, str]
    resolution_lines: dict[str, int] = field(default_factory=dict)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _brain(pass_name: str) -> str:
    return pass_name.split("-", 1)[1]


def load_inputs(root: Path = ROOT) -> Inputs:
    """Read every input and hash it.  Inventories are the ones the passes cite."""
    passes = {
        name: json.loads((root / GRAPH_DIR / f"{name}.json").read_text(encoding="utf-8"))
        for name in PASSES
    }
    atlas = json.loads((root / ATLAS).read_text(encoding="utf-8"))
    resolutions_text = (root / RESOLUTIONS).read_text(encoding="utf-8")
    resolutions = json.loads(resolutions_text)

    paths = {f"{GRAPH_DIR}/{name}.json" for name in PASSES} | {ATLAS, RESOLUTIONS}
    for document in passes.values():
        for node in document.get("nodes", []):
            for ref in node.get("phase1_refs", []):
                paths.add(ref["inventory_path"])
        for review in document.get("claim_reviews", []):
            if "inventory_path" in review.get("claim_ref", {}):
                paths.add(review["claim_ref"]["inventory_path"])
    hashes = {}
    for rel in sorted(paths):
        target = root / rel
        if not target.is_file():
            raise JoinError([f"input-missing: {rel} does not exist in the tree"])
        hashes[rel] = _sha256(target)

    lines = {}
    for number, line in enumerate(resolutions_text.splitlines(), start=1):
        match = re.match(r'\s*"id":\s*"(res\.[^"]+)"', line)
        if match:
            lines[match.group(1)] = number
    return Inputs(passes, atlas, resolutions, hashes, lines)


def _one_value(inputs: Inputs, field_name: str, pass_names: tuple[str, ...], problems: list[str]) -> str:
    values = {inputs.passes[name][field_name] for name in pass_names}
    if len(values) != 1:
        positions = "; ".join(f"{name}={inputs.passes[name][field_name]}" for name in pass_names)
        problems.append(f"contradiction: {field_name} differs across passes: {positions}")
    return sorted(values)[0]


def _finer(coarse: str, fine: str) -> str | None:
    """The normalization row that makes ``fine`` the finer form of ``coarse``."""
    if fine.startswith(coarse + "."):
        return "refinement"
    if any(fine == item or (item.endswith(".") and fine.startswith(item)) for item in SUBTYPE_BUCKETS.get(coarse, ())):
        return "bucket"
    if SUBTYPE_VOCABULARY.get(coarse) == fine:
        return "vocabulary"
    return None


def normalize_subtypes(values: set[str]) -> tuple[str, str] | None:
    """(value, rows) when the table makes the differing values one; else None."""
    for candidate in sorted(values):
        rows = {_finer(value, candidate) for value in values - {candidate}}
        if None not in rows:
            return candidate, "+".join(sorted(rows))
    return None


def _join_nodes(inputs: Inputs, problems: list[str], notes: list[str]) -> list[dict]:
    grouped: dict[str, list[tuple[str, dict]]] = {}
    for name in PASSES:
        for node in inputs.passes[name].get("nodes", []):
            grouped.setdefault(node["id"], []).append((name, node))

    joined = []
    for node_id in sorted(grouped):
        members = grouped[node_id]
        kinds = {node["kind"] for _, node in members}
        if len(kinds) > 1:
            positions = "; ".join(f"{name}: kind={node['kind']}" for name, node in members)
            problems.append(f"contradiction: node {node_id} kind differs ({positions})")
            continue
        first = members[0][1]
        label = first["label"]
        subtypes: dict[str, set[str]] = {}
        for name, node in members:
            if node.get("subtype"):
                subtypes.setdefault(_brain(name), set()).add(node["subtype"])
        values = {value for brain_values in subtypes.values() for value in brain_values}
        subtype = next(iter(values)) if len(values) == 1 else None

        exposures: dict[str, set[str]] = {}
        for name, node in members:
            match = EXPOSURE.search(node["label"])
            if match:
                exposures.setdefault(_brain(name), set()).add(match.group(1))
        distinct = {value for values in exposures.values() for value in values}
        if len(distinct) > 1:
            said = "; ".join(
                f"{brain}={'/'.join(sorted(exposures[brain]))}" for brain in sorted(exposures)
            )
            label = f"{label} [exposure disagreement: {said}]"
            notes.append(f"exposure-disagreement: {node_id}: {said}")
        if len(values) > 1:
            said = "; ".join(
                f"{brain}={'/'.join(sorted(subtypes[brain]))}" for brain in sorted(subtypes)
            )
            normal = normalize_subtypes(values)
            if normal:
                subtype = normal[0]
                label = f"{label} [subtype normalized: {said} -> {subtype} ({normal[1]})]"
                notes.append(f"subtype-normalized: {node_id}: {said} -> {subtype} ({normal[1]})")
            else:
                label = f"{label} [subtype conflict: {said}]"
                notes.append(f"subtype-conflict: {node_id}: {said}")

        refs = {_key(ref): ref for _, node in members for ref in node.get("phase1_refs", [])}
        sources = {_key(src): src for _, node in members for src in node.get("sources", [])}
        out = {
            "id": node_id,
            "kind": first["kind"],
            "label": label,
            "phase1_refs": [refs[key] for key in sorted(refs)],
            "sources": [
                sources[key]
                for key in sorted(
                    sources,
                    key=lambda key: (
                        sources[key]["path"],
                        sources[key]["line"],
                        sources[key]["revision"],
                        key,
                    ),
                )
            ],
        }
        if subtype:
            out["subtype"] = subtype
        joined.append(out)
    return joined


def _join_links(inputs: Inputs) -> list[dict]:
    grouped: dict[tuple[str, str, str], dict[str, dict]] = {}
    for name in PASSES:
        for link in inputs.passes[name].get("links", []):
            key = (link["from"], link["to"], link["relation"])
            bucket = grouped.setdefault(key, {})
            for evidence in link["evidence"]:
                bucket[_key(evidence)] = evidence
    return [
        {
            "from": key[0],
            "to": key[1],
            "relation": key[2],
            "evidence": [evidence[item] for item in sorted(evidence)],
        }
        for key, evidence in sorted(grouped.items())
    ]


def _copy_unique(inputs: Inputs, collection: str, problems: list[str]) -> dict[str, tuple[str, dict]]:
    seen: dict[str, tuple[str, dict]] = {}
    for name in PASSES:
        for item in inputs.passes[name].get(collection, []):
            item_id = item["id"]
            if item_id in seen and _key(seen[item_id][1]) != _key(item):
                problems.append(
                    f"contradiction: {collection} id {item_id} differs between "
                    f"{seen[item_id][0]} and {name}"
                )
                continue
            seen.setdefault(item_id, (name, item))
    return seen


def _claim_key(claim_ref: dict) -> str:
    if "record_id" in claim_ref:
        return f"{claim_ref['inventory_path']}#{claim_ref['record_id']}.{claim_ref['field']}"
    return f"{claim_ref['path']}#{claim_ref.get('symbol') or claim_ref.get('anchor')}"


def _check_claim_contradictions(
    reviews: dict[str, tuple[str, dict]],
    findings: dict[str, tuple[str, dict]],
    resolved: set[str],
    problems: list[str],
) -> None:
    by_claim: dict[str, list[tuple[str, str, str]]] = {}
    for review_id, (name, review) in reviews.items():
        by_claim.setdefault(_claim_key(review["claim_ref"]), []).append(
            (review_id, name, review["verdict"])
        )
    for claim, members in sorted(by_claim.items()):
        verified = {review_id for review_id, _, verdict in members if verdict == "verified"}
        contradicted = {review_id for review_id, _, verdict in members if verdict == "contradicted"}
        if not verified or not contradicted:
            continue
        covered = any(
            finding_id in resolved
            and set(finding["claim_ids"]) & verified
            and set(finding["claim_ids"]) & contradicted
            for finding_id, (_, finding) in findings.items()
        )
        if not covered:
            sides = "; ".join(
                f"{review_id} ({name}) says {verdict}"
                for review_id, name, verdict in sorted(members)
                if verdict in {"verified", "contradicted"}
            )
            problems.append(
                f"contradiction: claim {claim} has no council resolution: {sides}"
            )


def _resolution_rows(
    inputs: Inputs, findings: dict[str, tuple[str, dict]], problems: list[str]
) -> list[dict]:
    council = inputs.resolutions
    placed: dict[str, str] = {}
    rows = []
    for resolution in council.get("resolutions", []):
        res_id = resolution["id"]
        for finding_id in resolution["findings"]:
            if finding_id in placed:
                problems.append(
                    f"contradiction: finding {finding_id} is resolved twice, by "
                    f"{placed[finding_id]} and {res_id}"
                )
                continue
            placed[finding_id] = res_id
            if finding_id not in findings:
                problems.append(
                    f"resolution-unresolved: {res_id} names finding {finding_id}, "
                    "which no pass contains"
                )
                continue
            name, finding = findings[finding_id]
            disposition = f"{resolution['bin']}: {resolution.get('disposition_final') or resolution['disposition']}"
            if finding["bin"] != resolution["bin"]:
                disposition += f" (sealed {name} bin: {finding['bin']})"
            if resolution.get("astra_bin") and resolution["astra_bin"] != resolution["bin"]:
                disposition += f" (Astra proposed bin: {resolution['astra_bin']})"
            positions = resolution.get("positions", {})
            by = (
                f"council {council.get('council', 'PHILO-2-06')}, round "
                f"{council.get('council_round', 1)}; muaddib={positions.get('muaddib', 'not recorded')}; "
                f"astra={positions.get('astra', 'not recorded')}"
            )
            evidence = [
                {
                    "revision": COUNCIL_REVISION,
                    "path": RESOLUTIONS,
                    "line": inputs.resolution_lines.get(res_id, 1),
                    "anchor": res_id,
                    "claim": "the council's recorded resolution of this finding",
                }
            ]
            evidence.extend(resolution.get("evidence", []))
            rows.append(
                {
                    "id": f"{res_id}:{finding_id}",
                    "finding_id": finding_id,
                    "disposition": disposition,
                    "by": by,
                    "evidence": evidence,
                }
            )
    for finding_id in sorted(set(findings) - set(placed)):
        problems.append(
            f"finding-unresolved: {finding_id} ({findings[finding_id][0]}) has no "
            f"council resolution in {RESOLUTIONS}"
        )
    return sorted(rows, key=lambda row: row["id"])


def join(inputs: Inputs) -> tuple[dict, list[str]]:
    """The join, plus notes for the summary.  Raises JoinError on a contradiction."""
    problems: list[str] = []
    notes: list[str] = []

    statics = ("static-muaddib", "static-astra")
    lives = ("live-muaddib", "live-astra")
    _one_value(inputs, "source_commit", statics, problems)
    source_commit = _one_value(inputs, "source_commit", lives, problems)
    baseline = _one_value(inputs, "phase1_baseline", PASSES, problems)

    nodes = _join_nodes(inputs, problems, notes)
    links = _join_links(inputs)

    atlas_cases = {case["id"]: case for case in inputs.atlas["cases"]}
    for name in PASSES:
        for case in inputs.passes[name].get("cases", []):
            if case["id"] not in atlas_cases:
                problems.append(f"case-unknown: {name} names case {case['id']}, which is not in {ATLAS}")
            elif _key(case) != _key(atlas_cases[case["id"]]):
                notes.append(f"case-revision: {name} ran an older revision of {case['id']}")

    observations = _copy_unique(inputs, "observations", problems)
    reviews = _copy_unique(inputs, "claim_reviews", problems)
    findings = _copy_unique(inputs, "findings", problems)
    resolutions = _resolution_rows(inputs, findings, problems)
    resolved = {row["finding_id"] for row in resolutions}
    _check_claim_contradictions(reviews, findings, resolved, problems)

    if problems:
        raise JoinError(sorted(problems))

    graph = {
        "schema_version": 1,
        "generator": GENERATOR,
        "source_commit": source_commit,
        "phase1_baseline": baseline,
        "inputs": [{"path": path, "sha256": digest} for path, digest in sorted(inputs.hashes.items())],
        "nodes": nodes,
        "links": links,
        "cases": [atlas_cases[case_id] for case_id in sorted(atlas_cases)],
        "observations": [observations[key][1] for key in sorted(observations)],
        "claim_reviews": [reviews[key][1] for key in sorted(reviews)],
        "findings": [findings[key][1] for key in sorted(findings)],
        "resolutions": resolutions,
    }
    return graph, sorted(set(notes))


def render(graph: dict) -> str:
    return json.dumps(graph, indent=1, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# The census: current source against the join's edges (brief section 8).
# ---------------------------------------------------------------------------

def _norm(entry: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", entry.lower()).strip("_")


HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def route_table(app: Any) -> dict[tuple[str, str], dict]:
    """(METHOD, path) -> handler name and defining file, for an assembled app.

    Routes are read in dispatch order; when two routes share a method and
    path, the first one serves the request and is the one recorded.  Paths
    are written as OpenAPI writes them (``{path:path}`` becomes ``{path}``).
    Routes hidden from the schema (the page shells, /docs, /openapi.json) are
    not API operations and have no edge, so they are not censused."""
    table: dict[tuple[str, str], dict] = {}
    for route in getattr(app, "routes", []):
        endpoint = getattr(route, "endpoint", None)
        methods = (getattr(route, "methods", None) or set()) & HTTP_METHODS
        if endpoint is None or not methods or not getattr(route, "include_in_schema", True):
            continue  # mounts, websockets and schema-hidden routes
        path = re.sub(r"\{([^}:]+):[^}]+\}", r"{\1}", route.path)
        module = getattr(endpoint, "__module__", "") or ""
        entry = {
            "handler": getattr(endpoint, "__name__", ""),
            "module": module.replace(".", "/") + ".py",
        }
        for method in methods:
            table.setdefault((method, path), entry)
    return table


def current_routes(root: Path) -> dict[tuple[str, str], dict] | str:
    """The HTTP routes of the current source, or why they could not be read.

    Membership comes from the app assembled by the route owner the Philo
    scripts share (scripts/gen_api_surface.py), not from the committed
    OpenAPI, so a source-only route change is visible.  ``root`` is unused:
    the app is the importable ``holdspeak`` package."""
    del root
    scripts = str(Path(__file__).resolve().parent)
    try:
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import gen_api_surface

        return route_table(gen_api_surface.build_reference_app())
    except Exception as exc:  # noqa: BLE001 - any assembly failure is reported, not guessed around
        return f"{type(exc).__name__}: {exc}"


def openapi_routes(root: Path) -> set[tuple[str, str]]:
    """The (METHOD, path) pairs of the committed docs/generated/openapi.json."""
    target = root / "docs/generated/openapi.json"
    if not target.is_file():
        return set()
    document = json.loads(target.read_text(encoding="utf-8"))
    return {
        (method.upper(), path)
        for path, operations in document.get("paths", {}).items()
        for method in operations
        if method.upper() in HTTP_METHODS
    }


def current_verbs(root: Path) -> set[str]:
    """The verb ids the face registers: the literal ids of verbRegistry.ts plus
    the ``go.<action>`` verbs it derives from the app and tool entries of
    applications.ts (the same parse as tests/unit/doc_claims/registry.py)."""

    def code(rel: str) -> str:
        text = (root / rel).read_text(encoding="utf-8")
        return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))

    ids = set(re.findall(r'^\s*id:\s*"([a-z][a-z0-9]*\.[a-z0-9-]+)"', code("web/src/desk/verbRegistry.ts"), re.M))
    apps = code("web/src/desk/applications.ts")
    for block in apps[apps.index("DESK_APPLICATIONS"):].split("\n  },"):
        action = re.search(r'^\s{4}action:\s*"([a-z0-9-]+)"', block, re.M)
        group = re.search(r'^\s{4}group:\s*"(app|tool)"', block, re.M)
        if action and group:
            ids.add(f"go.{action.group(1)}")
    return ids


def current_mcp_tools() -> set[str] | str:
    """The tool names the real MCP catalogue declares, or why it could not be read.

    The catalogue is assembled at import time from several declaration forms,
    so the census reads the real module (``uv run --extra dev``) rather than a
    pattern over its source."""
    try:
        from holdspeak.mcp import tools
    except Exception as exc:  # noqa: BLE001 - any import failure is reported, not guessed around
        return f"{type(exc).__name__}: {exc}"
    return {str(tool["name"]) for tool in tools.TOOLS}


def _code_sources(node: dict) -> list[dict]:
    """The sources of a node that point at code, not at an audit document."""
    return [source for source in node["sources"] if not source["path"].startswith("docs/")]


def _gone(root: Path, node: dict) -> str | None:
    for source in _code_sources(node):
        if not (root / source["path"]).is_file():
            return f"{source['path']} is gone"
    return None


_REVISIONS: dict[tuple[str, str], str | None] = {}


def _at_revision(root: Path, revision: str, rel: str) -> str | None:
    """The file as the pass read it (``git show``), or None when git cannot say."""
    key = (revision, rel)
    if key not in _REVISIONS:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "-C", str(root), "show", f"{revision}:{rel}"],
                capture_output=True, text=True, check=False,
            )
            _REVISIONS[key] = result.stdout if result.returncode == 0 else None
        except OSError:
            _REVISIONS[key] = None
    return _REVISIONS[key]


def census(graph: dict, root: Path = ROOT) -> list[str]:
    """Every difference between the current source and the join's edges."""
    lines: list[str] = []
    edges = [node for node in graph["nodes"] if node["kind"] == "edge"]

    def text(rel: str) -> str:
        return (root / rel).read_text(encoding="utf-8", errors="replace")

    # HTTP routes: the routes of the current source (the assembled app)
    # against every edge that carries an OpenAPI method/path reference.
    # Changed: a cited file is gone, or the handler that source registers for
    # the method and path is not the handler the edge cites.
    routes = current_routes(root)
    graphed: dict[tuple[str, str], list[dict]] = {}
    for node in edges:
        for ref in node["phase1_refs"]:
            if ref.get("inventory_path") == "docs/generated/openapi.json" and "method" in ref:
                graphed.setdefault((ref["method"].upper(), ref["path"]), []).append(node)
    if isinstance(routes, str):
        lines.append(f"unread: http route table could not be assembled ({routes}); not censused")
        routes = {}
    else:
        roster = openapi_routes(root)
        for method, path in sorted(set(routes) - roster):
            lines.append(f"stale: http {method} {path} is in source, not in docs/generated/openapi.json")
        for method, path in sorted(roster - set(routes)):
            lines.append(f"stale: http {method} {path} is in docs/generated/openapi.json, not in source")
    for method, path in sorted(set(routes) - set(graphed)):
        lines.append(f"new: http {method} {path} has no edge ({routes[(method, path)]['handler']})")
    for method, path in sorted(set(graphed) - set(routes)):
        ids = ", ".join(sorted(node["id"] for node in graphed[(method, path)]))
        lines.append(f"removed: http {method} {path} is not in source ({ids})")
    for pair in sorted(set(graphed) & set(routes)):
        handler = routes[pair]["handler"]
        for node in graphed[pair]:
            why = _gone(root, node)
            kind = "changed"
            cited = [
                source
                for source in _code_sources(node)
                if source["path"].endswith(".py")
                and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", source.get("symbol", ""))
                and source["symbol"] != "source_census"
            ]
            if why is None and cited and handler not in {source["symbol"] for source in cited}:
                # The registered handler is not a cited one.  If the file had
                # that handler at the pass's revision, the pass cited the
                # wrong function; if not, source changed since.
                source = cited[0]
                then = _at_revision(root, source["revision"], routes[pair]["module"])
                if then is not None and f"def {handler}(" in then:
                    kind = "miscited"
                    why = (
                        f"source registered {handler} at {source['revision'][:8]} already; "
                        f"the pass cited {source['symbol']}"
                    )
                else:
                    why = f"source registers {handler}, not the cited {source['symbol']}"
            elif why is None:
                # The handler is cited; every other cited function must still exist.
                for source in cited:
                    symbol = source["symbol"]
                    if f"def {symbol}(" in text(source["path"]):
                        continue
                    then = _at_revision(root, source["revision"], source["path"])
                    if then is not None and f"def {symbol}(" not in then:
                        kind = "miscited"
                        why = f"def {symbol} was not in {source['path']} at {source['revision'][:8]} either"
                    else:
                        why = f"def {symbol} is no longer in {source['path']}"
                    break
            if why:
                lines.append(f"{kind}: http {pair[0]} {pair[1]} ({node['id']}): {why}")

    # Desk verbs and MCP tools: the current declarations against the edges of
    # that family.  Changed: a cited file is gone, or no cited code file still
    # names the entry point.
    families: list[tuple[str, str, set[str] | str]] = [
        ("verb", "edge.verb.", current_verbs(root)),
        ("mcp tool", "edge.mcp.", current_mcp_tools()),
    ]
    for family, prefix, declared in families:
        if isinstance(declared, str):
            lines.append(f"unread: {family} catalogue could not be read ({declared}); not censused")
            continue
        current = {_norm(entry): entry for entry in declared}
        graphed_family = {node["id"][len(prefix):]: node for node in edges if node["id"].startswith(prefix)}
        for key in sorted(set(current) - set(graphed_family)):
            lines.append(f"new: {family} {current[key]} has no edge")
        for key in sorted(set(graphed_family) - set(current)):
            lines.append(f"removed: {family} edge {graphed_family[key]['id']} names nothing declared now")
        for key in sorted(set(current) & set(graphed_family)):
            node = graphed_family[key]
            why = _gone(root, node)
            sources = _code_sources(node)
            # A go.* verb is derived (`go.${tool.action}`), so its sources name the action.
            literal = current[key][3:] if family == "verb" and current[key].startswith("go.") else current[key]
            if why is None and sources and not any(f'"{literal}"' in text(s["path"]) for s in sources):
                why = f'no cited file still names "{literal}"'
            if why:
                lines.append(f"changed: {family} {current[key]} ({node['id']}): {why}")
    return lines


CENSUS_SCOPE = (
    "census scope: HTTP routes (the app assembled from source by "
    "scripts/gen_api_surface.py, schema-hidden page routes excluded; stale = "
    "docs/generated/openapi.json differs from source), desk verbs "
    "(web/src/desk/verbRegistry.ts + applications.ts), MCP tools (the real "
    "holdspeak.mcp.tools catalogue). Face handlers, keys, timers, frames, CLI "
    "and connector edges are not censused. miscited = a pass cited a handler "
    "that was not in the file at the revision it examined."
)


def subtype_conflicts(graph: dict) -> list[str]:
    """The unresolved subtype conflicts the join recorded in node labels."""
    lines = []
    for node in graph["nodes"]:
        match = re.search(r"\[subtype conflict: ([^\]]+)\]", node["label"])
        if match:
            lines.append(f"note: subtype conflict {node['id']}: {match.group(1)}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 when the join on disk is stale")
    mode.add_argument("--census", action="store_true", help="compare current source entry points with the join's edges")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root
    target = root / OUTPUT

    if args.census:
        if not target.is_file():
            print(f"census: {OUTPUT} does not exist; generate it first")
            return 1
        graph = json.loads(target.read_text(encoding="utf-8"))
        differences = census(graph, root)
        print(CENSUS_SCOPE)
        for line in differences:
            print(line)
        conflicts = subtype_conflicts(graph)
        for line in conflicts:
            print(line)
        counts = {kind: sum(1 for line in differences if line.startswith(kind + ":")) for kind in ("new", "removed", "changed", "stale", "miscited", "unread")}
        print(
            f"census: {counts['new']} new, {counts['removed']} removed, {counts['changed']} changed, "
            f"{counts['stale']} stale, {counts['miscited']} miscited, {counts['unread']} unread, "
            f"{len(conflicts)} subtype conflict note(s) "
            f"against {OUTPUT} (source_commit {graph['source_commit'][:8]})"
        )
        # A miscited source is a sealed pass's error, not source drift, and a
        # subtype conflict is an open classification question; both are
        # reported and do not fail the census.
        return 1 if any(counts[kind] for kind in ("new", "removed", "changed", "stale", "unread")) else 0

    try:
        graph, notes = join(load_inputs(root))
    except JoinError as error:
        for problem in error.problems:
            print(problem)
        print(f"graph join refused: {len(error.problems)} problem(s)")
        return 1
    text = render(graph)
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != text:
            print(f"graph join drift: {OUTPUT} (run python scripts/philo_graph_reference.py)")
            return 1
        conflicts = subtype_conflicts(graph)
        for line in conflicts:
            print(line)
        print(f"graph join checked: {OUTPUT}; {len(conflicts)} subtype conflict note(s)")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    for note in notes:
        print(note)
    print(
        f"graph join generated: {OUTPUT} — {len(graph['nodes'])} nodes, {len(graph['links'])} links, "
        f"{len(graph['cases'])} cases, {len(graph['observations'])} observations, "
        f"{len(graph['claim_reviews'])} claim reviews, {len(graph['findings'])} findings, "
        f"{len(graph['resolutions'])} resolutions; {len(notes)} note(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
