#!/usr/bin/env python3
"""HS-202-04 — the red-first proof, one row at a time.

Astra's counsel on #599, finding 3: "there is no committed … red-first
capture" — several rows carried only a green tail. This harness makes the
red reproducible instead of remembered.

For every row this story changed it:

  1. asserts the NEW text is in the file (so a drifted row is a hard stop,
     never a silent skip),
  2. writes the OLD text back in its place,
  3. runs that row's fence and REQUIRES a non-zero exit, printing the
     failing assertion,
  4. restores the file and verifies the bytes are identical by SHA-256.

A row that goes green with the old text back is a fence that proves
nothing; the harness fails on it. Every file is restored in a `finally`,
and the run ends with a whole-tree SHA-256 check over every touched file.

Run:
    HOME=$(mktemp -d) \\
    PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \\
        uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/\\
assets/story-04-shots/red-first.py
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
WEB = REPO / "web"

VITEST = "vitest"
PYTEST = "pytest"


class Row:
    def __init__(
        self,
        row_id: str,
        path: str,
        new: str,
        old: str,
        fence: str,
        kind: str = VITEST,
    ) -> None:
        self.id = row_id
        self.path = REPO / path
        self.new = new
        self.old = old
        self.fence = fence
        self.kind = kind


ROWS: list[Row] = [
    Row(
        "01 live-result-section (F06)",
        "web/src/pages/cores/LiveCore.tsx",
        '''      <SurfaceSection
        label="Summary"
        actions={<LampGadget on tone="ok" label="READY" />}
      >''',
        '''      <SurfaceSection
        label="Intelligence"
        actions={<LampGadget on tone="ok" label="READY" />}
      >''',
        "src/pages/cores/__tests__/summaryName202.test.tsx",
    ),
    Row(
        "02 live-door-section (F06)",
        "web/src/pages/cores/LiveCore.tsx",
        '''      <SurfaceSection label="Summary">
        <div className="surface-actions">''',
        '''      <SurfaceSection label="Intelligence">
        <div className="surface-actions">''',
        "src/pages/cores/__tests__/summaryName202.test.tsx",
    ),
    Row(
        "03 live-facts-row (M6)",
        "web/src/pages/cores/LiveCore.tsx",
        '''  const factsLine = `Link · ${connection || "unknown"}`;''',
        '''  const factsLine = `${connection || "This device"} · ${
    active ? "recording" : "ready"
  }`;''',
        "src/pages/cores/__tests__/summaryName202.test.tsx",
    ),
    Row(
        "04 live-footer-receipt SEG (F21, M6)",
        "web/src/pages/cores/LiveCore.tsx",
        '''            {active ? `REC ${duration}` : "READY"}
          </span>''',
        '''            {active ? `REC ${duration}` : "READY"}
            {segments.length ? ` · ${segments.length} SEG` : ""}
          </span>''',
        "src/pages/cores/__tests__/summaryName202.test.tsx",
    ),
    Row(
        "05 live-summary action items zero (U3)",
        "web/src/pages/cores/LiveCore.tsx",
        '''            <SurfaceFacts
              value={[
                countToken(intelActionCount, "action item", "action items"),
                intelResult.final ? "final" : "",
              ]
                .filter(Boolean)
                .join(" · ")}
            />''',
        '''            <SurfaceFacts
              value={`${intelActionCount} action item${intelActionCount === 1 ? "" : "s"}${
                intelResult.final ? " · final" : ""
              }`}
            />''',
        "src/pages/cores/__tests__/summaryName202.test.tsx",
    ),
    Row(
        "06 live-door queue six zeros (U3)",
        "web/src/pages/cores/LiveCore.tsx",
        '''          empty={!Object.keys(jobFacts).length}
          emptyLabel="No jobs waiting"
          emptyGlyph="○"
          onRetry={() => void pluginJobs.reload()}''',
        '''          onRetry={() => void pluginJobs.reload()}''',
        "src/pages/cores/__tests__/summaryName202.test.tsx",
    ),
    Row(
        "06b live-door queue null next_retry_at (M5)",
        "web/src/pages/cores/LiveCore.tsx",
        '''      if (!["string", "number", "boolean"].includes(typeof value)) continue;
      if (typeof value === "number" && value <= 0) continue;
      if (typeof value === "string" && !value.trim()) continue;''',
        '''      if (typeof value === "number" && value <= 0) continue;''',
        "src/pages/cores/__tests__/summaryName202.test.tsx",
    ),
    Row(
        "07 meetings-door one Retry (F07)",
        "web/src/pages/cores/history/DoorSection.tsx",
        '''{row.meeting_id ? "Retry" : "Retry background work"}''',
        '''{row.meeting_id
                          ? "Retry intelligence"
                          : "Retry background work"}''',
        "src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx",
    ),
    Row(
        "08 meetings one all-clear (M6)",
        "web/src/pages/cores/history/CatalogRail.tsx",
        '''        emptyLabel="Record or import a meeting"''',
        '''        emptyLabel="No meetings yet"''',
        "src/pages/cores/history/__tests__/oneRetryOneAllClear202.test.tsx",
    ),
    Row(
        "09 sequence edit verb (F08)",
        "web/src/desk/pullouts/ChainPullout.tsx",
        '''              actionLabel="Edit Sequence"''',
        '''              actionLabel="Edit chain"''',
        "src/desk/pullouts/__tests__/sequenceVerb202.test.tsx",
    ),
    Row(
        "10 room provenance words (F21)",
        "web/src/features/project-room/RoomPeopleSection.tsx",
        '''  const seg =
    source.segment_index != null ? ` · Segment ${source.segment_index + 1}` : "";
  return `Meeting · ${source.label}${seg}`;''',
        '''  const seg = source.segment_index != null ? ` · SEG ${source.segment_index + 1}` : "";
  return `MTG · ${source.label}${seg}`;''',
        "src/features/project-room/__tests__/provenanceWords202.test.ts",
    ),
    Row(
        "11 settings-hub meetings chip (F06)",
        "web/src/pages/cores/settingsPrefs.tsx",
        '''              ? <StateChip state="success" label={`SUMMARY ON${hub.meetings.auto && hub.meetings.auto !== "off" ? ` · ${autoLabel(hub.meetings.auto)}` : ""}`} />
              : <StateChip state="warning" label="SUMMARY OFF" />}''',
        '''              ? <StateChip state="success" label={`INTELLIGENCE ON${hub.meetings.auto && hub.meetings.auto !== "off" ? ` · ${autoLabel(hub.meetings.auto)}` : ""}`} />
              : <StateChip state="warning" label="INTELLIGENCE OFF" />}''',
        "src/pages/cores/__tests__/settingsSummaryName202.test.tsx",
    ),
    Row(
        "12 settings meetings module row (F06)",
        "web/src/pages/cores/SettingsCore.tsx",
        '''            <GadgetRow label="Summary">
              <CycleGadget
                label="Auto-run the summary"''',
        '''            <GadgetRow label="Intelligence">
              <CycleGadget
                label="Auto-run intelligence"''',
        "tests/e2e/test_hs172_settings_meetings_glass.py",
        PYTEST,
    ),
    Row(
        "12b settings advanced sheet group (F06)",
        "web/src/pages/cores/SettingsCore.tsx",
        """              <GadgetGroup label="Summary">
                {check(["meeting", "intel_cloud_store"], "Cloud store")}""",
        """              <GadgetGroup label="Intelligence">
                {check(["meeting", "intel_cloud_store"], "Cloud store")}""",
        "tests/e2e/test_hs172_settings_meetings_glass.py",
        PYTEST,
    ),
    Row(
        "13 floor list zone accessible name (U3 aria)",
        "web/src/desk/components/DeskListView.tsx",
        '''aria-label={[`${row.title} zone`, countToken(row.count, "item", "items")].filter(Boolean).join(", ")}''',
        '''aria-label={`${row.title} zone, ${row.count} ${row.count === 1 ? "item" : "items"}`}''',
        "src/desk/components/__tests__/zeroCounters202.test.tsx",
    ),
    Row(
        "14 floor list zone cell (U3 text)",
        "web/src/desk/components/DeskListView.tsx",
        '''      render: (row) => row.type === "zone" ? (countToken(row.count, "ITEM") ?? "EMPTY") : row.zoneName.toUpperCase(),''',
        '''      render: (row) => row.type === "zone" ? `${row.count} ${row.count === 1 ? "ITEM" : "ITEMS"}` : row.zoneName.toUpperCase(),''',
        "src/desk/components/__tests__/zeroCounters202.test.tsx",
    ),
    Row(
        "15 spatial floor zone accessible name (U3 aria)",
        "web/src/desk/gl/WorldStage.tsx",
        '''            aria-label={[`${z.title} zone`, countToken(z.count, "item", "items")]
              .filter(Boolean)
              .join(", ")}''',
        '''            aria-label={`${z.title} zone, ${z.count} ${z.count === 1 ? "item" : "items"}`}''',
        "src/desk/components/__tests__/zeroCounters202.test.tsx",
    ),
    Row(
        "16 ask session head (U3)",
        "web/src/desk/components/AskPanel.tsx",
        '''          head={["SESSION", countToken(turnCount, "TURN")]
            .filter(Boolean)
            .join(" · ")}''',
        '''          head={`SESSION · ${turnCount} ${turnCount === 1 ? "TURN" : "TURNS"}`}''',
        "src/desk/components/__tests__/zeroCounters202.test.tsx",
    ),
    Row(
        "17 speak door Runs fact (U3)",
        "web/src/pages/cores/dictation/Readiness.tsx",
        '''        {runs > 0 ? (
          <GadgetRow label="Runs">
            <span className="speak-token-line">{runs}</span>
          </GadgetRow>
        ) : null}''',
        '''        <GadgetRow label="Runs">
          <span className="speak-token-line">{runs}</span>
        </GadgetRow>''',
        "src/pages/cores/dictation/__tests__/readinessZero202.test.tsx",
    ),
    Row(
        "18 speak door raw fold",
        "web/src/pages/cores/dictation/Readiness.tsx",
        '''      <FoldGadget title="RAW · READINESS">''',
        '''      <FoldGadget title="Wire details">''',
        "src/pages/cores/dictation/__tests__/readinessZero202.test.tsx",
    ),
    Row(
        "19 registry: the Segment term",
        "web/src/lib/productLanguage.ts",
        '''  segment: ["Segment", "Segments"],''',
        "",
        "src/lib/productLanguage.test.ts",
    ),
    Row(
        "20 registry: the seg/mtg aliases",
        "web/src/lib/productLanguage.ts",
        '''  seg: "segment",
  mtg: "meeting",''',
        "",
        "src/lib/productLanguage.test.ts",
    ),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_fence(row: Row) -> tuple[int, str]:
    if row.kind == VITEST:
        proc = subprocess.run(
            ["npx", "vitest", "run", row.fence, "--maxWorkers=2"],
            cwd=str(WEB), capture_output=True, text=True,
        )
    else:
        env = dict(os.environ)
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", row.fence, "-x"],
            cwd=str(REPO), capture_output=True, text=True, env=env,
        )
    return proc.returncode, (proc.stdout + proc.stderr)


# jsdom has no WebGL, so every WorldStage render prints a canvas notice.
# It is noise, never the failure this harness is looking for.
_NOISE = (
    "HTMLCanvasElement", "not wrapped in act", "pixi.js", "jsdom/lib",
    "/* assert on the output */", "/* fire events", "act(() =>",
)
_WANTED = (
    "AssertionError", "TestingLibraryElementError", "Unable to find",
    "assert ", "FAILED",
)


def first_failure(output: str) -> str:
    """The failing test's name and its assertion, noise skipped."""
    name = ""
    for line in output.splitlines():
        text = line.strip()
        if text.startswith("×") and not name:
            name = text
        if any(token in text for token in _NOISE):
            continue
        if any(token in text for token in _WANTED) and len(text) > 12:
            return f"{name}\n      {text[:200]}" if name else text[:220]
    return name or "(no assertion line captured)"


def main() -> int:
    failures: list[str] = []
    baseline = {row.path: sha(row.path) for row in ROWS}

    for row in ROWS:
        original = row.path.read_text(encoding="utf-8")
        if row.new not in original:
            failures.append(f"{row.id}: the NEW text is not in {row.path.name}")
            print(f"  !! {row.id}: DRIFTED — new text absent", flush=True)
            continue
        try:
            row.path.write_text(
                original.replace(row.new, row.old, 1), encoding="utf-8")
            code, output = run_fence(row)
            if code == 0:
                failures.append(f"{row.id}: fence stayed GREEN with the old text")
                print(f"  !! {row.id}: GREEN with the old text — proves nothing",
                      flush=True)
            else:
                print(f"  RED {row.id}\n      fence: {row.fence}\n"
                      f"      {first_failure(output)}", flush=True)
        finally:
            row.path.write_text(original, encoding="utf-8")
            if sha(row.path) != baseline[row.path]:
                failures.append(f"{row.id}: {row.path} did NOT restore")
                print(f"  !! {row.id}: RESTORE FAILED", flush=True)

    # A fence that boots the product builds the web bundle from whatever
    # source is on disk at that moment (`tests/e2e/conftest.py` — build
    # first, universally). Row 12's e2e therefore leaves a bundle compiled
    # from the REVERTED file, and the next rig to serve it photographs the
    # old label from correct source: the stale-bundle scar
    # (`reference_e2e_rigs_stale_bundle_and_xdist.md`). Rebuild before
    # handing the tree back.
    if any(row.kind == PYTEST for row in ROWS):
        print("\n  -- rebuilding the web bundle (a fence rebuilt it from "
              "reverted source) --", flush=True)
        build = subprocess.run(
            ["npm", "run", "build"], cwd=str(WEB),
            capture_output=True, text=True,
        )
        print(f"  build exit={build.returncode}", flush=True)
        if build.returncode != 0:
            failures.append("the web bundle did not rebuild")

    print("\n  -- restore check --", flush=True)
    for path, digest in baseline.items():
        now = sha(path)
        mark = "ok " if now == digest else "BAD"
        print(f"  {mark} {path.relative_to(REPO)}  {now[:12]}", flush=True)
        if now != digest:
            failures.append(f"{path} did not restore")

    print(f"\n  rows: {len(ROWS)}  failures: {len(failures)}", flush=True)
    for line in failures:
        print(f"  FAIL {line}", flush=True)
    print("VERDICT", "PASS — every row proved red first" if not failures
          else "FAIL", flush=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
