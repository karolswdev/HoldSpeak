# HS-201-08 — story-08-scheduler-muaddib

Invocation confirmed by CLI result: model `claude-fable-5-1`, session `416adc59-a8c4-43b4-9a49-e9db0e8faf36`. Peer clock estimates below are unverified; capture timestamps are UTC. Read-only check.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on interrupting the diagnostic run, 2026-09-20.** I used no tools and no confirmed session id is available. I agree, with conditions.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. Interrupting is the right call. Two reasons:
   - The run is already red, and its only remaining value is the list of failures.
   - About 95% complete with one worker finishing a contiguous glass chunk means you
     would wait many minutes for almost nothing new.
   - A single SIGINT to the pytest controller, PID 86244, is the clean way to get the
     list. pytest-xdist handles the first KeyboardInterrupt by tearing down the workers
     and printing the short summary.
   - Tenet 3 applies. No tenet objects.
2. Amending my built-check C1 is accepted.
   - "Read the current run to its end" was a means. The end it served is "every failure
     named and accounted for, and a complete final run".
   - The replacement wording is: interrupted diagnostic (labelled not-proof) plus one
     complete final run. That is stricter where it matters.
3. `--dist=worksteal` is consistent with the owner's `-n 4` obligation. It changes
   scheduling and leaves selection unchanged.
   - It changes which tests share a worker process and in what order.
   - So it can expose or hide order-dependent state that `load` did not.
   - That is acceptable. If it goes wrong, the symptom will be a new red, not a false
     green.

CONDITIONS:
K1. Send ONE SIGINT, to 86244 only. Do not send a second signal, do not SIGKILL, and do
    not signal the workers.
    - If no summary appears within about 2 minutes, record that plainly and take the
      failures from the `F` positions.
    - Do not fabricate a summary.
    - Afterwards, confirm that no orphaned product processes or Chromium instances
      remain from the glass rigs. UAT conductor tests boot real hubs on scanned ports.
      Leftover listeners would pollute the final run.
K2. Label the capture in its header:
    - "interrupted at ~95%, exit 2";
    - "NOT full-suite proof";
    - "tests not run: unknown set".
    - An interrupted run cannot say which tests never ran. Therefore no "only N
      failures exist" claim may be built on it.
    - Every reported failure is named and classified a/b/c.
K3. Before the final run, restore the tracked PNG churn the glass chunk wrote, and
    confirm with `git status` that the tree is quiet.
    - The final run starts from the staged, fixed tree, with no workers editing.
K4. Requirements for the final run:
    - It reaches 100%.
    - HOME is isolated.
    - The command uses `-n 4 --dist=worksteal --ignore=tests/e2e/test_metal.py`.
    - Nothing else is deselected.
    - No serial markers are added, and no assertion is weakened.
    - It carries the absolute PLAYWRIGHT_BROWSERS_PATH and npm_config_cache.
    - Record the exact command line and the final counts line.
    - The scheduler change is named in evidence as a deviation from the story's written
      command. Amend story-08:25,32 visibly to include `--dist=worksteal`.
K5. If a failure appears under worksteal that was absent under `load`:
    - Classify it as (c) with a named polluter, or as (b), and fix it.
    - Reverting the scheduler to make it disappear is NOT a fix.
    - If a failure present under `load` vanishes under worksteal, treat it as still
      unexplained until someone names the polluter.
K6. If the final run is red, fix and rerun. There is no partial closure, and the story
    stays in-progress. The earlier check conditions stand unchanged:
    - roadmaps: deterministic red first;
    - docs: R1-R3.
    Counsel-on-built is owed on the final tree.

MISSED:
1. The idle-worker imbalance is a standing cost of the `-n auto` / `-n 4` guidance in
   CLAUDE.md.
   - If worksteal proves materially faster and no less stable on this run, put a line
     in the ledger recommending it for the documented fast lane.
   - Do not edit CLAUDE.md in this story.
2. CI does not use xdist at all (test.yml:116, :271).
   - Local worksteal-green does not predict CI ordering.
   - The PR's CI run remains the only proof for the Ubuntu and macOS jobs.

TUESDAY: Not applicable. This ruling covers process only.

UNKNOWN:
- I did not inspect the running processes or the log.
  - PID ownership is root's claim.
  - So are the counts of about 12 failures before 13% and 1 at 36%.
- Whether pytest-xdist will emit a complete short summary on SIGINT in this
  configuration. K1 covers the case where it does not.
```
