"""``uv run python -m uat.stage`` — drive the harness to induce a world, ad-hoc.

The conductor + guided site are for a *sitting*. This is the small door for
"just set up X and let me poke it": boot an isolated HoldSpeak on a chosen deck,
apply state recipes and/or seed manifests (create notes, knowledge blocks,
zones/directories, recipes, chains, workflows, profiles, meetings), print the
run's product URL, and keep it up until Ctrl-C.

Examples:

    # See what you can invoke
    uv run python -m uat.stage --list

    # A seeded desk on golden-local; open the printed URL and poke it
    uv run python -m uat.stage --recipe seeded-desk

    # A specific world, apply a couple of seeds, keep it up
    uv run python -m uat.stage --deck golden-43 --seed dogfood-desk --seed my-zones

    # A real meeting with open actions (needs .43), then tear down at once
    uv run python -m uat.stage --recipe meeting-just-ended-open-actions --once

    # Bind LAN so a device can pair with the run
    uv run python -m uat.stage --recipe seeded-desk --lan

It never imports the ``holdspeak`` package — it drives the product as a
subprocess through the same ``RunManager`` the conductor uses.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from .conductor.induction.decks import DeckRegistry
from .conductor.induction.recipes import RecipeError, RecipeRegistry, RecipeVerifyError
from .conductor.induction.seeds import SeedError, SeedRegistry
from .conductor.runs import RunManager


def _print_catalog() -> None:
    print("Decks:")
    for d in DeckRegistry().all():
        need = " (needs .43)" if "intel" in (d.get("requires") or []) else ""
        print(f"  {d['name']:16} {d.get('title','')}{need}")
    print("\nRecipes (named worlds, deck + seeds + verify probe):")
    for r in RecipeRegistry().all():
        need = " (needs .43)" if "intel" in (r.get("requires") or []) else ""
        print(f"  {r['name']:32} -> deck {r['deck']}{need}")
    print("\nSeed manifests (desk primitives to create):")
    for s in SeedRegistry().names():
        print(f"  {s}")
    print("\nSeed a manifest with any of: notes, kbs (knowledge blocks), recipes,")
    print("chains, workflows, directories (zones), profiles, meetings. See uat/AUTHORING.md.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Induce a HoldSpeak world, ad-hoc.")
    ap.add_argument("--list", action="store_true", help="list decks, recipes, and seeds, then exit")
    ap.add_argument("--deck", default=None, help="boot deck (default: the recipe's deck, or golden-local)")
    ap.add_argument("--recipe", action="append", default=[], help="apply a state recipe (repeatable)")
    ap.add_argument("--seed", action="append", default=[], help="apply a seed manifest (repeatable)")
    ap.add_argument("--lan", action="store_true", help="bind the run LAN-wide (device pairing)")
    ap.add_argument("--no-intel", action="store_true", help="refuse recipes that require .43")
    ap.add_argument("--once", action="store_true", help="apply, report, tear down (do not stay up)")
    ap.add_argument("--boot-timeout", type=float, default=60.0)
    args = ap.parse_args(argv)

    if args.list:
        _print_catalog()
        return 0

    mgr = RunManager(boot_timeout=args.boot_timeout)
    deck = args.deck
    if deck is None and args.recipe:
        # Boot on the first recipe's deck so the world is right from the start.
        try:
            deck = RecipeRegistry().load(args.recipe[0]).deck
        except RecipeError:
            deck = "golden-local"
    deck = deck or "golden-local"

    print(f"Booting an isolated run on deck '{deck}'…")
    try:
        run = mgr.create_run(deck=deck, lan=args.lan)
    except Exception as exc:
        print(f"boot failed: {exc}", file=sys.stderr)
        return 1
    if run.status != "up":
        print(f"product failed to boot ({run.status}):\n{run.error}", file=sys.stderr)
        mgr.teardown_all()
        return 1

    ok = True
    try:
        for recipe in args.recipe:
            print(f"\nApplying recipe '{recipe}'…")
            try:
                result = mgr.apply_recipe(run.id, recipe, allow_intel=not args.no_intel)
                print(f"  probe ok={result.probe.get('ok')}  (already_satisfied={result.already_satisfied})")
            except RecipeVerifyError as exc:
                ok = False
                print(f"  FAILED to verify: {exc}", file=sys.stderr)
                print(f"  probe: {json.dumps(exc.result.probe, indent=2)}", file=sys.stderr)
            except (RecipeError, Exception) as exc:  # noqa: BLE001
                ok = False
                print(f"  ERROR: {exc}", file=sys.stderr)
        for seed in args.seed:
            print(f"\nApplying seed '{seed}'…")
            try:
                outcome = mgr.apply_seed(run.id, seed)
                print(f"  applied: {outcome['applied']}  meetings: +{outcome['meetings_imported']} "
                      f"({outcome['meetings_skipped']} skipped)")
                for err in outcome["errors"]:
                    ok = False
                    print(f"  ! {err}", file=sys.stderr)
            except SeedError as exc:
                ok = False
                print(f"  ERROR: {exc}", file=sys.stderr)

        run = mgr.get(run.id)
        pub = run.to_public()
        print("\n" + "=" * 60)
        print(f"  Run:      {run.id}  ({run.status})")
        print(f"  Product:  {pub['pairing']['url']}")
        if run.token:
            print(f"  Token:    {run.token}")
        print(f"  Deck:     {run.deck}")
        print("=" * 60)

        if args.once:
            return 0 if ok else 2
        print("Open the product URL and poke it. Ctrl-C to tear the run down.")
        while mgr.get(run.id) and mgr.get(run.id).status == "up":
            time.sleep(1.0)
        return 0 if ok else 2
    except KeyboardInterrupt:
        print("\nTearing down…")
        return 0
    finally:
        mgr.teardown_all()


if __name__ == "__main__":
    raise SystemExit(main())
