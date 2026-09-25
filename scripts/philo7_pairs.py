"""PHILO-7-03: the equivalence run over retained atlas observations.

Each named pair is a browser case (``case.p7.*`` at 1440 or 393) and its
headless ``.op`` sibling, run against DIFFERENT isolated hubs. They are never
compared by envelope. Equivalence is three things, each read from the rig's
named observation slots only:

* the durable outcome (the same name, status, membership or absence);
* the identity relationships inside each run (the member IS the note that run
  made; the successor IS the id the supersede returned), never equal ids
  across runs;
* refusals: neither side's write was refused (the op trigger's refusal is
  ``None``; the face trigger's own network response is below 400).

Usage::

    uv run python scripts/philo7_pairs.py <runs-dir> [<runs-dir> ...] --out pairs.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

Obs = dict[str, Any]


def _read(obs: Obs, path_suffix: str) -> Any:
    """The payload of the browser case's retained HTTP read whose path ends so."""
    for read in (obs.get("after") or {}).get("api_reads") or []:
        if read.get("path", "").endswith(path_suffix):
            return read
    return None


def _payload(obs: Obs, path_suffix: str) -> Any:
    read = _read(obs, path_suffix)
    return None if read is None else read.get("payload")


def _op(obs: Obs, index: int | None = None) -> Any:
    after = obs.get("after") or {}
    record = after.get("op") if index is None else (after.get("op_reads") or [None] * (index + 1))[index]
    return (record or {}).get("response"), (record or {}).get("refusal")


def _v(obs: Obs, name: str) -> Any:
    return (obs.get("variables") or {}).get(name)


def _members(rows: Any, key: str) -> list[str]:
    return sorted(str(row.get(key)) for row in rows or [] if isinstance(row, dict))


# Each projection returns (durable outcome, identity relationships held).
Projection = Callable[[Obs], tuple[Any, bool]]


def _zone_create_face(o: Obs) -> tuple[Any, bool]:
    d = (_payload(o, f"/api/directories/{_v(o, 'zone_id')}") or {}).get("directory") or {}
    return {"name": d.get("name")}, d.get("id") == _v(o, "zone_id")


def _zone_create_op(o: Obs) -> tuple[Any, bool]:
    d = (_op(o)[0] or {}).get("directory") or {}
    return {"name": d.get("name")}, d.get("id") == _v(o, "zone_id")


def _filed_face(o: Obs, zone: str = "zone_id") -> tuple[Any, bool]:
    rows = (_payload(o, f"/api/directories/{_v(o, zone)}/members") or {}).get("members")
    return {"members": len(rows or [])}, _members(rows, "primitive_id") == [f"note:{_v(o, 'note_id')}"]


def _filed_op(o: Obs) -> tuple[Any, bool]:
    rows = _op(o)[0]
    return {"members": len(rows or [])}, _members(rows, "primitive_id") == [f"note:{_v(o, 'note_id')}"]


def _refile_face(o: Obs) -> tuple[Any, bool]:
    b = (_payload(o, f"/api/directories/{_v(o, 'zone_b')}/members") or {}).get("members")
    a = (_payload(o, f"/api/directories/{_v(o, 'zone_a')}/members") or {}).get("members")
    note = f"note:{_v(o, 'note_id')}"
    return {"in_b": len(b or []), "in_a": len(a or [])}, _members(b, "primitive_id") == [note] and note not in _members(a, "primitive_id")


def _refile_op(o: Obs) -> tuple[Any, bool]:
    b, a = _op(o)[0], _op(o, 0)[0]
    note = f"note:{_v(o, 'note_id')}"
    return {"in_b": len(b or []), "in_a": len(a or [])}, _members(b, "primitive_id") == [note] and note not in _members(a, "primitive_id")


def _unfile_face(o: Obs) -> tuple[Any, bool]:
    rows = (_payload(o, f"/api/directories/{_v(o, 'zone_id')}/members") or {}).get("members")
    note = (_payload(o, f"/api/notes/{_v(o, 'note_id')}") or {}).get("note") or {}
    return {"members": len(rows or []), "note_kept": note.get("deleted") is False}, note.get("id") == _v(o, "note_id")


def _unfile_op(o: Obs) -> tuple[Any, bool]:
    rows, note = _op(o)[0], _op(o, 1)[0] or {}
    return {"members": len(rows or []), "note_kept": note.get("deleted") is False}, note.get("id") == _v(o, "note_id")


def _kb_create_face(o: Obs) -> tuple[Any, bool]:
    kb = (_payload(o, f"/api/kbs/{_v(o, 'kb_id')}") or {}).get("kb") or {}
    return {"name": kb.get("name")}, kb.get("id") == _v(o, "kb_id")


def _kb_create_op(o: Obs) -> tuple[Any, bool]:
    kb = _op(o)[0] or {}
    return {"name": kb.get("name")}, kb.get("id") == _v(o, "kb_id")


def _kb_member_face(o: Obs) -> tuple[Any, bool]:
    rows = (_payload(o, f"/api/kbs/{_v(o, 'kb_id')}/members") or {}).get("members")
    return {"members": len(rows or [])}, f"note:{_v(o, 'note_id')}" not in _members(rows, "resource_ref")


def _kb_member_op(o: Obs) -> tuple[Any, bool]:
    rows = _op(o)[0]
    return {"members": len(rows or [])}, f"note:{_v(o, 'note_id')}" not in _members(rows, "resource_ref")


def _status_face(o: Obs) -> tuple[Any, bool]:
    d = (_payload(o, f"/api/decisions/{_v(o, 'decision_id')}") or {}).get("decision") or {}
    return {"status": d.get("status")}, d.get("id") == _v(o, "decision_id")


def _status_op(o: Obs) -> tuple[Any, bool]:
    d = _op(o)[0] or {}
    return {"status": d.get("status")}, d.get("id") == _v(o, "decision_id")


def _supersede_face(o: Obs) -> tuple[Any, bool]:
    old = (_payload(o, f"/api/decisions/{_v(o, 'decision_id')}") or {}).get("decision") or {}
    new = (_payload(o, f"/api/decisions/{_v(o, 'successor_id')}") or {}).get("decision") or {}
    return ({"old_status": old.get("status"), "successor_readable": bool(new)},
            old.get("superseded_by") == _v(o, "successor_id") == new.get("id"))


def _supersede_op(o: Obs) -> tuple[Any, bool]:
    old, new = _op(o)[0] or {}, _op(o, 0)[0] or {}
    return ({"old_status": old.get("status"), "successor_readable": bool(new)},
            old.get("superseded_by") == _v(o, "successor_id") == new.get("id"))


def _delete_face(o: Obs) -> tuple[Any, bool]:
    one = _read(o, f"/api/decisions/{_v(o, 'decision_id')}") or {}
    rows = (_payload(o, "/api/decisions") or {}).get("decisions")
    listed = _v(o, "decision_id") in _members(rows, "id")
    return {"read_refused": one.get("status") == 404, "listed": listed}, True


def _delete_op(o: Obs) -> tuple[Any, bool]:
    listed = _v(o, "decision_id") in _members(_op(o)[0], "id")
    _, refusal = _op(o, 0)
    return {"read_refused": (refusal or {}).get("code") == "not_found", "listed": listed}, True


PAIRS: dict[str, tuple[Projection, Projection]] = {
    "case.p7.zone_create.visible": (_zone_create_face, _zone_create_op),
    "case.p7.zone_file.note_in_zone": (_filed_face, _filed_op),
    "case.p7.zone_file.refile_moves": (_refile_face, _refile_op),
    "case.p7.zone_unfile.note_leaves": (_unfile_face, _unfile_op),
    "case.p7.kb_create.visible": (_kb_create_face, _kb_create_op),
    "case.p7.kb_member.add_and_remove": (_kb_member_face, _kb_member_op),
    "case.p7.decision_status.review_list": (_status_face, _status_op),
    "case.p7.decision_supersede.successor_visible": (_supersede_face, _supersede_op),
    "case.p7.decision_delete.gone": (_delete_face, _delete_op),
}


def _face_refused(o: Obs) -> bool:
    chosen = ((o.get("trigger_response_capture") or {}).get("chosen")) or {}
    return int(chosen.get("status") or 0) >= 400


def _op_refused(o: Obs) -> bool:
    return bool((o.get("trigger") or {}).get("refusal"))


def load(dirs: list[Path]) -> dict[tuple[str, int | None], Obs]:
    found: dict[tuple[str, int | None], Obs] = {}
    for root in dirs:
        for path in sorted(root.glob("*/observation.json")):
            obs = json.loads(path.read_text())
            obs["_path"] = str(path)
            headless = str(obs.get("case_id", "")).endswith(".op")
            found[(obs["case_id"], None if headless else obs.get("viewport"))] = obs
    return found


def build(dirs: list[Path]) -> list[dict[str, Any]]:
    runs = load(dirs)
    rows = []
    for case_id, (face_projection, op_projection) in PAIRS.items():
        op = runs.get((case_id + ".op", None))
        for width in (1440, 393):
            face = runs.get((case_id, width))
            row: dict[str, Any] = {"pair": case_id, "width": width,
                                   "face": face and face["_path"], "op": op and op["_path"]}
            if face is None or op is None:
                row.update(verdict="missing", why="a side was not run")
                rows.append(row)
                continue
            face_outcome, face_identity = face_projection(face)
            op_outcome, op_identity = op_projection(op)
            row.update(
                face_verdict=face.get("verdict"), op_verdict=op.get("verdict"),
                face_outcome=face_outcome, op_outcome=op_outcome,
                outcome_equal=face_outcome == op_outcome,
                identity=face_identity and op_identity,
                refusals_equal=_face_refused(face) == _op_refused(op) is False,
                engine=[face["provenance"]["engine_mode"], op["provenance"]["engine_mode"]],
            )
            row["verdict"] = "equivalent" if (row["outcome_equal"] and row["identity"]
                                              and row["refusals_equal"]) else "NOT equivalent"
            rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    rows = build(args.runs)
    for row in rows:
        print(f"{row['pair']} @{row['width']}: {row['verdict']} "
              f"face={row.get('face_outcome')} op={row.get('op_outcome')} "
              f"identity={row.get('identity')} verdicts={row.get('face_verdict')}/{row.get('op_verdict')}")
    if args.out:
        args.out.write_text(json.dumps(rows, indent=2) + "\n")
    return 0 if all(row["verdict"] == "equivalent" for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
