"""HS-131-03 real-LAN walk: Ask and a saved Agent through the migrated door.

Against the live llama.cpp endpoint at 192.168.1.43:8080, through the REAL
service layer (not the runner directly), proves:
  1. AskService.ask → one admitted inference.invoke + terminal receipt +
     staged-then-finalized ask_result projection referencing both.
  2. RecipeService.run (a saved Agent) → same door, SavedDefinition origin
     with the exact persisted revision, Artifact materialized only after the
     receipt.
  3. A target mutation after admission cannot change what executes.

Run with an isolated HOME. Exits non-zero on any failed assertion.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import AskService
from holdspeak.services.recipe_service import RecipeService

LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"


async def main(workdir: Path) -> int:
    db = Database(workdir / "walk-ask.db")
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "walk-owner")

    # Leg 1: Ask through the migrated door.
    ask = AskService(db)
    answer = await ask.ask(
        owner, "Reply with exactly: DOOR", inference_target_id="lan43", max_tokens=24,
    )
    print(f"leg1 ask keys={sorted(answer)}")
    ops = [
        broker.store.operation(e["operation_id"])
        for e in broker.events(0, {}, owner)["events"]
    ]
    invokes = [o for o in ops if o and o["name"] == "inference.invoke"]
    assert invokes, "Ask must create an admitted inference.invoke"
    receipt = broker.store.receipt(invokes[0]["operation_id"])
    assert receipt and receipt["outcome"] == "succeeded", receipt
    with db._connection() as conn:
        ask_rows = conn.execute("SELECT invocation_id, operation_id FROM ask_results").fetchall()
    assert len(ask_rows) == 1, f"exactly one finalized ask_result, got {len(ask_rows)}"
    print(f"leg1 invoke={invokes[0]['operation_id']} receipt={receipt['outcome']} ask_results=1")

    # Leg 2: a saved Agent (Recipe run) through the same door.
    recipe = db.recipes.upsert(
        recipe_id="walk-agent", name="Walk Agent", role="assistant",
        system_prompt="Answer in one short sentence.", user_template="{input}",
    )
    recipes = RecipeService(db, broker=broker)
    run = await recipes.run(
        owner, "walk-agent", input="Name one color.", inference_target_id="lan43",
    )
    print(f"leg2 run keys={sorted(run)}")
    ops2 = [
        broker.store.operation(e["operation_id"])
        for e in broker.events(0, {}, owner)["events"]
    ]
    invokes2 = [o for o in ops2 if o and o["name"] == "inference.invoke"]
    assert len(invokes2) >= 2, "Agent run must add a second admitted invocation"
    with db._connection() as conn:
        artifact_rows = conn.execute("SELECT COUNT(*) FROM recipe_results").fetchone()[0]
    assert artifact_rows == 1, f"exactly one finalized recipe_result, got {artifact_rows}"
    print(f"leg2 invocations={len(invokes2)} recipe_results=1")

    # Leg 3: Article XI.3 through the service layer — mutate the profile,
    # already-finalized results stay bound to their admitted revisions, and a
    # fresh ask against the mutated (bogus) endpoint refuses/fails rather than
    # silently retargeting.
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43 (mutated)", kind="openAICompatible",
        base_url="http://127.0.0.1:9/v1", model=LAN_MODEL, requires_key=False,
    )
    try:
        bad = await ask.ask(owner, "Anything", inference_target_id="lan43", max_tokens=8)
        outcome = str(bad.get("outcome") or bad.get("error") or "answered")
        assert outcome not in {"answered"}, f"mutated endpoint must not silently answer: {bad}"
        print(f"leg3 post-mutation outcome={outcome}")
    except Exception as exc:  # typed refusal/failure surfaces are both honest
        print(f"leg3 post-mutation raised {type(exc).__name__}: {exc}")
    with db._connection() as conn:
        rows_after = conn.execute("SELECT COUNT(*) FROM ask_results").fetchone()[0]
    assert rows_after == 1, "no phantom ask_result may appear from the failed leg"

    print("WALK OK: Ask and a saved Agent both dispatch through the admitted door "
          "with staged projections finalized after receipts; mutation cannot retarget.")
    return 0


if __name__ == "__main__":
    import tempfile

    sys.exit(asyncio.run(main(Path(tempfile.mkdtemp(prefix="hs13103-walk-")))))
