# Evidence - HS-111-08

- **Story:** HS-111-08 - Interactive elements
- **Status:** done
- **Date:** 2026-08-02

## Proof

### Captured run — 2026-08-02T06:22:24Z

- **Command:** `uv run pytest -q tests/unit tests/integration --deselect tests/integration/test_web_aftercare_file_issue.py::test_filed_proposal_never_executes_until_approved_and_enabled`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 673b102892f1ba55c5c4083559e2ac5dd277d125

```text
........................................................................ [  1%]
........................................................................ [  3%]
........................................................................ [  5%]
........................................................................ [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 17%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 81%]
..........................................................F............. [ 83%]
.................................s...................................... [ 85%]
........................................................................ [ 87%]
..........................ss............................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 99%]
........................................                                 [100%]
=================================== FAILURES ===================================
__________________ test_live_stream_snapshot_then_ansi_delta ___________________

live_pane = ('hs94-term-536dd9c3', '%2906')

    def test_live_stream_snapshot_then_ansi_delta(live_pane) -> None:
        session, pane = live_pane
        targets = TerminalTargetRegistry()
        stream = TerminalStreamService(targets)
        issued = targets.issue(f"pane:{pane}")
        assert issued["status"] == "issued"
        assert issued["pane_id"] == pane
    
        snap = stream.read(issued["target_id"], issued["target_generation"])
        assert snap["status"] == "snapshot"
        assert snap["ansi"] is True
        base_sequence = snap["sequence"]
    
        marker = f"ansi-{uuid.uuid4().hex[:8]}"
        subprocess.run(
            [
                "tmux",
                "send-keys",
                "-t",
                pane,
                f"printf '\\033[1;31m{marker}\\033[0m\\n'",
                "Enter",
            ],
            check=True,
            timeout=10,
        )
        time.sleep(0.6)
    
        out = stream.read(
            issued["target_id"], issued["target_generation"], resume_sequence=base_sequence
        )
        assert out["status"] == "deltas", out
        joined = "".join(d["data"] for d in out["deltas"])
        assert marker in joined
        # tmux re-emits SGR state as it captured it; the escapes themselves
        # must cross untouched (peek strips them, the stream must NOT).
>       assert "\x1b[31m" in joined and "\x1b[0m" in joined
E       assert ('\x1b[31m' in "printf '\\033[1;31mansi-830fde8c\\033[0m\\n'\n\nThe default interactive shell is now zsh.\nTo update your account to use zsh, please run `chsh -s /bin/zsh`.\nFor more details, please visit https://support.apple.com")

tests/integration/test_delivery_terminal_live.py:117: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
FAILED tests/integration/test_delivery_terminal_live.py::test_live_stream_snapshot_then_ansi_delta
1 failed, 4212 passed, 3 skipped, 1 deselected in 1324.54s (0:22:04)
```

### Captured run — 2026-08-02T06:45:48Z

- **Command:** `uv run pytest -q tests/unit tests/integration --deselect tests/integration/test_web_aftercare_file_issue.py::test_filed_proposal_never_executes_until_approved_and_enabled`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 673b102892f1ba55c5c4083559e2ac5dd277d125

```text
........................................................................ [  1%]
........................................................................ [  3%]
........................................................................ [  5%]
........................................................................ [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 17%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 83%]
.................................s...................................... [ 85%]
........................................................................ [ 87%]
..........................ss............................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 99%]
........................................                                 [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
4213 passed, 3 skipped, 1 deselected in 681.23s (0:11:21)
```

(The clean captured run: unit 3450 + integration 763, 3 pre-existing
model skips, 1 deselection — see "the verification trail" below. The
first capture above records exit 1 honestly: a load-flake on a live
test that passes in isolation. Web ran separately, output read:
exit 0 — **74 test files / 432 tests**, tokens/gates/typecheck/build
green.)

## What shipped

The conformance sweep — the two-dialect era ends. The kit ruled the
seven refit rooms; the legacy Signal dialect still ruled the six
small cores (29 InlineMessage sites, 16 TextInputs, 14 StatusPills,
20 Disclosures). Per the verified audit (.tmp/hs-111-08-audit.md),
on the ratified cut line:

- **Roving focus is kit law**: useRovingRows (roving-tabindex ARIA,
  editor guard, Home/End/PageUp/Down, type-ahead) lives inside
  SurfaceLedger and GadgetTable — EVERY ledger in the OS inherited
  "arrows walk, Tab exits" in one change (Meetings catalog, Speak
  journal, crew board, process monitor, delivery boards, the list
  view). Focus is a visible accent band (it was literally identical
  to hover before).
- **The unarmed × is extinct**: arming two-step (× → DELETE?/FORGET?)
  is the GadgetTable default, no opt-out.
- **FoldGadget** is the ONE disclosure (details semantics, token
  slot; all 20 sites migrated); **PadGadget** gives multiline its
  mic by construction; LampGadget gained `fail`; EditInPlace grew
  the mic; the Wings pill (flagged in the phase's first audit)
  reforged into sunken beveled tab gadgets.
- **The six small cores joined the kit** through the pageSupport
  chokepoint (SurfaceState load/error faces) + per-core control
  swaps; ComponentsCore rewritten as the kit's LIVING STYLE GUIDE.
- **Eleven species deleted as dead code** — including Dialog and
  ConfirmAction, the OS's only modals (zero consumers): the
  no-modals law is now structurally true. Retired-species grep in
  live code: zero.
- The design-system guard and DESIGN_SYSTEM.md were updated
  TOGETHER (the matrix now pins the kit roster; the assert lives).

## The verification trail (three failure species, none the story's)

1. The builder attributed one integration failure to "dirty backend
   work" — DISPROVEN by a stash test (fails with clean python too).
2. Real root cause: **a test-hermeticity bug** — the aftercare
   file-issue test isolates the DB but NOT Config, so the live hub's
   control posture leaks in; the hub flipped to YOLO between runs
   (YOLO refuses ad-hoc destinations by design, so the decide
   returns the refusal shape). The test passed at 04:30 and failed
   at 05:30 with identical code. Deselected from the capture WITH
   THIS RECORD; CI (clean env) is the arbiter. The hermeticity gap
   rides to HS-111-10's debt list.
3. One load-flake on test_delivery_terminal_live during a 22-minute
   run on the busy live machine (200 belt runs) — passes in 4.9s in
   isolation; the failed capture is preserved above, the clean
   recapture follows it.

## Live proof (real hub, :8765)

Assets in [assets/hs-111-08/](./assets/hs-111-08/): the accent focus
band mid-arrow-walk on the Meetings catalog, the armed × → DELETE?
beside an unarmed sibling, the reforged wings, the kit gallery, a
small-core face, mobile gallery. Full 19-shot set reviewed
(.tmp/hs-111-08-after/), error leg included (real aborted-feed ⚠ +
Try again, in-flow).

## Named debt riding to HS-111-10 (the ratified cut)

(a) the desk-component InlineMessage/naked-message long tail
(PrReceipts/Dossier/Conveyor/Pullout — their Disclosures ARE
migrated); (b) the naked chrome-input mic sweep (AttentionDrawer,
InfoWindow rename, SystemShade, zone rename, palette input);
(c) InlineEditor's native cluster (Field/TextInput/TextArea/Select
survive in Signal.tsx solely for it, header-documented);
(d) composer→PadGadget migrations; (e) the config-hermeticity gap in
live-posture-sensitive integration tests.
