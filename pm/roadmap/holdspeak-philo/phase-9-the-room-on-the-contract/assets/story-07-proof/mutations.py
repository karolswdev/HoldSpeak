"""PHILO-9-07 mutation runs: each check's mutation must turn its fence red.

For each mutation: assert the exact original text occurs once, write the
mutated text, run the named fences (isolated HOME), restore the original bytes
(always, in ``finally``). One line per mutation: RED (caught) or GREEN (a miss).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

WT = Path(__file__).resolve().parents[6]
PY = str(WT / ".venv" / "bin" / "python")
G = "tests/unit/test_philo9_project_grant.py"
L = "tests/unit/test_philo9_project_grant_lifecycle.py"

MUTATIONS: list[tuple[str, str, str, str, list[str]]] = [
    ("M1 admission looks up any project's LIVE grant for the agent",
     "holdspeak/kernel/project.py",
     '        f"SELECT * FROM {_TABLE} WHERE agent_identity=? AND project_id=? AND state=\'LIVE\'",\n        (agent_identity, project_id),',
     '        f"SELECT * FROM {_TABLE} WHERE agent_identity=? AND state=\'LIVE\' AND ?<>\'\'",\n        (agent_identity, project_id),',
     [f"{G}::test_grants_on_two_projects_each_authorise_their_own_project"]),
    ("M2 approval and the claim read the latest LIVE row, not the frozen id (G2 for G1)",
     "holdspeak/kernel/project.py",
     '    row = conn.execute(f"SELECT * FROM {_TABLE} WHERE id=?", (grant_id,)).fetchone()\n    if project_id is None:',
     '    row = conn.execute(f"SELECT * FROM {_TABLE} WHERE agent_identity=? AND state=\'LIVE\'", (agent_identity,)).fetchone()\n    if project_id is None:',
     [f"{L}::test_a_regrant_before_approval_never_approves_the_older_operation",
      f"{L}::test_a_change_between_approval_and_the_claim_refuses_the_claim"]),
    ("M3 no re-check at the claim",
     "holdspeak/kernel/project_codec.py",
     "        if self.name not in rooms.PROJECT_GRANT_OPERATIONS or str(operation.get(\"principal_kind\")) != \"agent\":\n            return\n",
     "        return\n",
     [f"{L}::test_a_change_between_approval_and_the_claim_refuses_the_claim"]),
    ("M4 approval never re-checks the agent's grant",
     "holdspeak/kernel/project.py",
     "            return by_basis(conn, operation, None, broker._clock(), authoritative=True)\n    return None",
     "            return \"\"\n    return None",
     [f"{L}::test_a_change_between_admission_and_approval_refuses_the_approval"]),
    ("M5 the expiry is outside the hash",
     "holdspeak/kernel/project.py",
     "    sha = terms_sha256(terms, expires_at)\n\n    def effect(conn: Any) -> None:\n        # Local SQL",
     "    sha = terms_sha256(terms, None)\n\n    def effect(conn: Any) -> None:\n        # Local SQL",
     [f"{L}::test_the_expiry_and_the_project_are_inside_the_hash"]),
    ("M6 a running agent run never re-checks its frozen grant",
     "holdspeak/services/steward_contract.py",
     "        if authority.get(\"grant\"):\n",
     "        if False:\n",
     [f"{G}::test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child"]),
    ("M7 a lost grant stops the run BEFORE the child is attempted (no child receipt)",
     "holdspeak/services/steward_contract.py",
     "        if code not in rooms.GRANT_CODES:\n",
     "        if True:\n",
     [f"{G}::test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run"]),
    ("M8 stop is not bound to the run's requester",
     "holdspeak/kernel/project_codec.py",
     "            if str(run.get(\"requested_by\") or \"\") != f\"principal:{principal.identity}\":",
     "            if False:",
     [f"{G}::test_an_agent_cannot_stop_another_agents_run_in_the_same_project"]),
    ("M9 an agent may grant (not owner-only)",
     "holdspeak/kernel/project_codec.py",
     "        if self.name in rooms.PROJECT_DELEGATION_OPERATIONS:\n            # XI.4",
     "        if False:\n            # XI.4",
     [f"{G}::test_the_grant_operations_are_owner_only_admitted_and_in_no_palette"]),
    ("M10 the credential revoke leaves the project grants LIVE",
     "holdspeak/web/routes/mcp_http.py",
     "            project_grants = project_delegation.revoke_for_credential(principal, identity)\n        except",
     "            project_grants = []\n        except",
     [f"{G}::test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant"]),
    ("M11 the palette is reverse-mapped (DESK = ALL)",
     "holdspeak/web/routes/mcp_http.py",
     "            palette_name = c.palette_name or (_palette_reverse.get(c.palette, None) if c.palette else None)",
     "            palette_name = _palette_reverse.get(c.palette, None) if c.palette else None",
     [f"{G}::test_a_desk_credential_reads_back_desk"]),
    ("M12 the projection reads the stored state (no expiry)",
     "holdspeak/kernel/project.py",
     '    state = {"": "LIVE", EXPIRED: "EXPIRED", REVOKED: "REVOKED"}[code]\n    return {"state": state, "grant_id": str(row["id"]), "expires_at": row["expires_at"]}\n\n\nclass ProjectGrantRefused',
     '    state = str(row["state"])\n    return {"state": state, "grant_id": str(row["id"]), "expires_at": row["expires_at"]}\n\n\nclass ProjectGrantRefused',
     [f"{L}::test_the_projection_says_what_the_kernel_would_answer"]),
    ("M13 an agent's steward child is refused (no trusted child path)",
     "holdspeak/kernel/causation.py",
     "        if not (direct_parent_principal and agent_steward_child(request.name, principal, parent_id)):",
     "        if True:",
     [f"{G}::test_an_agent_runs_children_each_naming_the_grant_and_the_policy"]),
]


def run(tests: list[str]) -> tuple[int, str]:
    env = dict(os.environ, HOME=tempfile.mkdtemp())
    env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
    proc = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line", *tests],
                          cwd=str(WT), env=env, capture_output=True, text=True, timeout=900)
    tail = [line for line in proc.stdout.splitlines() if line.startswith(("E ", "/", "FAILED")) or " passed" in line or " failed" in line]
    return proc.returncode, " | ".join(tail[-3:])[:500]


def main() -> int:
    only = set(sys.argv[1:])
    misses = ran = 0
    for label, rel, old, new, tests in MUTATIONS:
        if only and label.split()[0] not in only:
            continue
        ran += 1
        path = WT / rel
        original = path.read_bytes()
        text = original.decode()
        if text.count(old) != 1:
            print(f"ERROR {label}: the original text occurs {text.count(old)} times in {rel}")
            misses += 1
            continue
        try:
            path.write_text(text.replace(old, new, 1))
            code, tail = run(tests)
        finally:
            path.write_bytes(original)
        verdict = "RED (caught)" if code != 0 else "GREEN (MISSED)"
        misses += code == 0
        print(f"{verdict}: {label} [{rel}] -> {tail}")
    print(f"MUTATIONS: {ran} run, {misses} missed")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
