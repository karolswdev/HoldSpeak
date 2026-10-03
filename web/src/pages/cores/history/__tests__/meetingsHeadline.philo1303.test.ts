// PHILO-13-03 (Astra's pass on #736) — Meetings says `All summaries done`
// only when it is true. The rows are the real `GET /api/meetings` list wire,
// minted by the real stop-handoff producer and the REAL intel queue executor
// (scripts/philo13_meetings_headline_fixture.py; the provider is the one
// double). Red on 1e562b76 (a running or queued first run, has_summary=false,
// read `All summaries done`), green after. The process state leads, as on the
// rail: failed, then running, then queued.
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { meetingsHeadline } from "../helpers";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../../..");
const PYTHON = resolve(REPO_ROOT, ".venv/bin/python");
const SCRIPT = resolve(REPO_ROOT, "scripts/philo13_meetings_headline_fixture.py");

type Row = Record<string, unknown>;
let home = "";
let cases: Record<string, Row[]> = {};

beforeAll(() => {
  home = mkdtempSync(join(tmpdir(), "philo13-a2w-headline-"));
  const text = execFileSync(PYTHON, [SCRIPT, "--home", home], {
    cwd: REPO_ROOT,
    env: { ...process.env, HOME: home },
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024,
  });
  cases = (JSON.parse(text) as { cases: Record<string, Row[]> }).cases;
}, 120_000);

afterAll(() => {
  if (home) rmSync(home, { recursive: true, force: true });
});

describe("PHILO-13-03 — the Meetings headline names the live summary fact", () => {
  it("the producer wire is what the cases claim", () => {
    const one = (name: string) => {
      expect(cases[name]).toHaveLength(1);
      return cases[name][0];
    };
    expect(one("stored")).toMatchObject({ intel_status: "ready", has_summary: true });
    expect(one("running")).toMatchObject({ intel_status: "running", has_summary: false });
    expect(one("queued")).toMatchObject({ intel_status: "queued", has_summary: false });
    expect(one("retrying")).toMatchObject({ intel_status: "queued", has_summary: false });
    expect((one("retrying").intel_job as Row).status).toBe("retrying");
    expect(one("failed")).toMatchObject({ intel_status: "error", has_summary: false });
    expect(one("rerun_running")).toMatchObject({ intel_status: "running", has_summary: true });
  });

  it("says All summaries done only over a stored success", () => {
    expect(meetingsHeadline(cases.stored, false)).toEqual({ text: "All summaries done", accent: false });
  });

  it("names a running summary, first run or re-run", () => {
    expect(meetingsHeadline(cases.running, false)).toEqual({ text: "1 summary running", accent: true });
    expect(meetingsHeadline(cases.rerun_running, false)).toEqual({ text: "1 summary running", accent: true });
  });

  it("names a queued or retrying summary as queued", () => {
    expect(meetingsHeadline(cases.queued, false)).toEqual({ text: "1 summary queued", accent: true });
    expect(meetingsHeadline(cases.retrying, false)).toEqual({ text: "1 summary queued", accent: true });
  });

  it("leads with the highest process state: failed, then running, then queued", () => {
    const rows = [...cases.queued, ...cases.running, ...cases.failed, ...cases.stored];
    expect(meetingsHeadline(rows, false)).toEqual({ text: "1 meeting failed", accent: true });
    expect(meetingsHeadline([...cases.queued, ...cases.running, ...cases.stored], false))
      .toEqual({ text: "1 summary running", accent: true });
    expect(meetingsHeadline([...cases.queued, ...cases.stored], false))
      .toEqual({ text: "1 summary queued", accent: true });
  });
});
