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
  ``None``; the face trigger's own network response is below 400). Where the
  face trigger sends nothing, the row says ``refusal_check: not_applicable``
  with the reason: absence of a response proves no refusal was avoided.

One headless ``.op`` run serves BOTH face widths of its pair, so N pairs at
two widths rest on N op runs and 2N face runs; the summary says so.

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
    """Identity (round two, Muad'Dib F2a): the id the setup minted is the id
    whose own read answers 404 and which the list no longer holds."""
    decision_id = _v(o, "decision_id")
    one = _read(o, f"/api/decisions/{decision_id}") or {}
    rows = (_payload(o, "/api/decisions") or {}).get("decisions")
    listed = decision_id in _members(rows, "id")
    refused = one.get("status") == 404
    return {"read_refused": refused, "listed": listed}, bool(decision_id) and refused and not listed


def _delete_op(o: Obs) -> tuple[Any, bool]:
    """Identity: the minted id is absent from the list, its own read refuses
    naming it, and the READ delete receipt carries the delete's operation id
    and names that decision as its target."""
    decision_id = _v(o, "decision_id")
    listed = decision_id in _members(_op(o)[0], "id")
    _, refusal = _op(o, 0)
    receipt = ((( _op(o, 1)[0] or {}).get("objects") or [{}])[0] or {}).get("receipt") or {}
    refused = (refusal or {}).get("code") == "not_found"
    identity = (bool(decision_id) and not listed and refused
                and str(decision_id) in str((refusal or {}).get("error"))
                and receipt.get("operation_id") == _v(o, "delete_op") is not None
                and receipt.get("target_ref") == f"decision:{decision_id}")
    return {"read_refused": refused, "listed": listed}, identity


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


def _face_trigger_response(o: Obs) -> dict[str, Any] | None:
    """The network response the face trigger itself caused, or None."""
    chosen = (o.get("trigger_response_capture") or {}).get("chosen")
    return chosen if isinstance(chosen, dict) and chosen.get("status") else None


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
            response = _face_trigger_response(face)
            if response is None:
                # Round two (Muad'Dib F2b): a face trigger that sends nothing
                # (a Search fill; the write ran in setup) cannot show a
                # refusal, so "neither side refused" would prove nothing.
                refusal_check = {
                    "status": "not_applicable",
                    "reason": ("the face trigger made no network call (a Search fill or a key "
                               "press; the write ran in setup or the network response was not "
                               "captured), so the face side's refusal cannot be read"),
                    "op_refused": _op_refused(op),
                }
                refusals_ok = not _op_refused(op)
            else:
                face_refused = int(response["status"]) >= 400
                refusal_check = {
                    "status": "checked",
                    "face_trigger_response": f"{response.get('method')} {response.get('path')} {response.get('status')}",
                    "face_refused": face_refused, "op_refused": _op_refused(op),
                }
                refusals_ok = not face_refused and not _op_refused(op)
            row.update(
                face_verdict=face.get("verdict"), op_verdict=op.get("verdict"),
                face_outcome=face_outcome, op_outcome=op_outcome,
                outcome_equal=face_outcome == op_outcome,
                identity=face_identity and op_identity,
                refusal_check=refusal_check,
                # Round two (F2c): ONE headless run serves both face widths.
                op_run_shared_across_widths=True,
                engine=[face["provenance"]["engine_mode"], op["provenance"]["engine_mode"]],
            )
            row["verdict"] = "equivalent" if (row["outcome_equal"] and row["identity"]
                                              and refusals_ok) else "NOT equivalent"
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
    ops = {row["op"] for row in rows if row.get("op")}
    faces = {row["face"] for row in rows if row.get("face")}
    equivalent = sum(row["verdict"] == "equivalent" for row in rows)
    na = sum((row.get("refusal_check") or {}).get("status") == "not_applicable" for row in rows)
    summary = (f"{equivalent}/{len(rows)} pair-widths equivalent, over {len(ops)} headless op runs "
               f"(each shared by both widths) x {len(faces)} face runs; the refusal leg is "
               f"not applicable on {na} of them (the face trigger sent nothing)")
    print(summary)
    if args.out:
        args.out.write_text(json.dumps({"summary": summary, "pairs": rows}, indent=2) + "\n")
    return 0 if all(row["verdict"] == "equivalent" for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
