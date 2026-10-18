// Runs on, the app: the whole window (RunsOnCore with its real hooks, the
// real Meaning search row and the real speech row) against a fake hub.
//
// The test diet (2026-10-11): successors of the browser walks over Runs on.
// Only `fetch` is replaced. Every answer has the hub's own shape:
//   GET  /api/inference/assignments   InferenceAssignmentService.assignment_summary
//                                     (holdspeak/services/inference_assignment_service.py)
//   GET  /api/concierge/detect        holdspeak/web/routes/concierge.py get_detect
//                                     (+ concierge_service._repair_row, summary_assignment_projection)
//   POST /api/setup/discover-models   holdspeak/web/routes/setup.py (422 on a refusal, same body)
//   POST /api/inference/model-library/define-endpoint   {provider: {profile_id, profile_revision}}
//   POST /api/inference/assignments/set|clear           the projection / {cleared, revision}
//   POST /api/concierge/summary-selection               {status, result: {state}, summaryAssignment}
//   GET  /api/memory/meaning-search   MeaningSearchService.status
//   GET  /api/setup/local-ai          the first-run Local AI status with `speech`
// The hub half of the same walks is tests/integration/test_desk_runs_on_hub.py.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useBuilderTools } from "../builderTools";

vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));

import { RunsOnCore } from "../../features/runson/RunsOnCore";

/* ── the hub's shapes ── */

const SUMMARY = "meeting.deferred_analysis";
const GROUPS: Array<[string, string, string]> = [
  ["thoughts_notes", "Thoughts & notes", "ask.answer"],
  ["writing_dictation", "Writing & dictation", "dictation.rewrite"],
  ["speech_recognition", "Speech recognition", "speech.transcribe"],
  ["meetings", "Meetings", SUMMARY],
  ["agents_tools", "Agents & tools", "agent.plan"],
  ["background", "Background", "memory.embed"],
];

type Entry = { profile_id: string; profile_revision: number; label: string; boundary: string; readiness: string };
type Head = { revision: number; entries: Entry[]; cleared: boolean };

/** A fake hub with the state a write changes: assignment heads per key
 *  (`global`, `group:<id>`, `capability:<id>`), the defined profiles. */
class FakeHub {
  heads = new Map<string, Head>();
  profiles = new Map<string, { label: string; baseUrl: string; model: string; revision: number }>();
  engines: Record<string, unknown>[] = [];
  repairs: Record<string, unknown>[] = [];
  speechReady = true;
  calls: Array<{ method: string; path: string; body: unknown }> = [];
  endpoints = new Map<string, string[]>(); // base_url -> models (absent = refused)

  private live(key: string): Head | undefined {
    const head = this.heads.get(key);
    return head && !head.cleared ? head : undefined;
  }

  private projection(head: Head, scope: unknown) {
    return { revision: head.revision, scope, entries: head.entries, issues: [] };
  }

  roster() {
    const global = this.live("global");
    const rows: Record<string, unknown>[] = [
      {
        id: "global",
        label: "Default for AI work",
        inherited_from: null,
        assignment: global ? this.projection(global, { kind: "global" }) : null,
        status: global ? "assigned" : "no_assignment",
        repair: global ? null : "Choose default",
        expected_revision: this.heads.get("global")?.revision ?? 0,
        editor_capability_id: "ask.answer",
      },
    ];
    for (const [id, label, capability] of GROUPS) {
      const own = this.live(`group:${id}`);
      const source = own ?? global;
      rows.push({
        id,
        label,
        editor_capability_id: capability,
        inherited_from: own ? "group" : global ? "global" : null,
        expected_revision: this.heads.get(`group:${id}`)?.revision ?? 0,
        assignment: source ? this.projection(source, own ? { kind: "group", group_id: id } : { kind: "global" }) : null,
        status: source ? "assigned" : "no_assignment",
        repair: null,
      });
    }
    return {
      schema: "InferenceAssignmentSummary@1",
      rows,
      task_overrides: GROUPS.map(([group, glabel, capability]) => ({
        id: capability,
        label: capability,
        group: { id: group, label: glabel },
        has_override: Boolean(this.live(`capability:${capability}`)),
      })),
      issue_count: global ? 0 : 1,
    };
  }

  summaryAssignment() {
    const head = this.live(`capability:${SUMMARY}`) ?? this.live("group:meetings") ?? this.live("global");
    const first = head?.entries[0];
    if (!first) {
      return {
        schema: "SummaryAssignmentProjection@1", capabilityId: SUMMARY, status: "unassigned",
        assignmentRevision: this.heads.get(`capability:${SUMMARY}`)?.revision ?? 0,
        profileId: null, profileRevision: null, label: null, boundary: null, readiness: null,
      };
    }
    return {
      schema: "SummaryAssignmentProjection@1", capabilityId: SUMMARY, status: "assigned",
      assignmentRevision: this.heads.get(`capability:${SUMMARY}`)?.revision ?? 0,
      profileId: first.profile_id, profileRevision: first.profile_revision, label: first.label,
      boundary: "lan", readiness: first.readiness,
    };
  }

  detect() {
    const defined = [...this.profiles.entries()].map(([id, p]) => ({
      id: `lan:${id}`, kind: "lan", name: p.label, host: p.baseUrl.split("://")[1].split(":")[0], state: "READY",
      profileId: id, profileRevision: p.revision, baseUrl: p.baseUrl, latencyMs: 12,
      fits: Object.fromEntries(GROUPS.map(([g]) => [g, { state: g === "speech_recognition" ? "INCOMPATIBLE" : "READY" }])),
    }));
    return {
      engines: [...this.engines, ...defined],
      hardware: { capability: { apple_silicon: true, system: "darwin", architecture: "arm64", ram_gb: 36 } },
      runtimes: [],
      checkedAt: "2026-10-11T09:41:00Z",
      summaryAssignment: this.summaryAssignment(),
      repairs: this.repairs,
      lastApply: null,
    };
  }

  private write(key: string, expected: number, entries: Entry[] | null): Head | { conflict: true } {
    const current = this.heads.get(key)?.revision ?? 0;
    if (expected !== current) return { conflict: true };
    const head = { revision: current + 1, entries: entries ?? [], cleared: entries === null };
    this.heads.set(key, head);
    return head;
  }

  private entry(profileId: string, revision: number): Entry {
    const p = this.profiles.get(profileId);
    return { profile_id: profileId, profile_revision: revision, label: p?.label ?? "Missing model", boundary: "private_network", readiness: "ready" };
  }

  answer(method: string, path: string, body: any): [number, unknown] {
    this.calls.push({ method, path, body });
    if (path === "/api/inference/assignments") return [200, this.roster()];
    if (path === "/api/concierge/detect") return [200, this.detect()];
    if (path === "/api/memory/meaning-search")
      return [200, {
        state: "off", percent: 0, bytes_done: 0, bytes_total: 146_146_432, indexed: 0, total: 0, error: "", error_code: "",
        model: { label: "nomic-embed-text v1.5", size_bytes: 146_146_432, on_device: false, source: "huggingface.co", boundary: "local" },
        egress: { destination: "huggingface.co", what: "model file request" },
      }];
    if (path === "/api/setup/local-ai") {
      const landed = this.speechReady;
      return [200, {
        state: "not_started",
        files: [
          { key: "whisper", label: "whisper-base-mlx", size_bytes: 144_000_000, on_device: landed, url: "https://huggingface.co/a" },
          { key: "embed", label: "nomic-embed-text v1.5", size_bytes: 146_000_000, on_device: false },
        ],
        bytes_total: 0, bytes_done: 0, egress: { destination: "huggingface.co" },
        speech: { model: "base", backend: "mlx", state: landed ? "on_device" : "will_download", ready: landed, bytes: landed ? 0 : 144_000_000 },
        error: "",
      }];
    }
    if (path === "/api/setup/discover-models") {
      const models = this.endpoints.get(body.base_url);
      if (!models) return [422, { ok: false, models: [], detail: "Nothing answers at this address." }];
      return [200, { ok: true, models, detail: `Found ${models.length} model.`, status: 200, tools: "no" }];
    }
    if (path === "/api/inference/model-library/define-endpoint") {
      const draft = body.draft;
      const revision = (this.profiles.get(draft.profile_id)?.revision ?? 0) + 1;
      this.profiles.set(draft.profile_id, { label: draft.label, baseUrl: draft.endpoint, model: draft.model, revision });
      return [200, { provider: { profile_id: draft.profile_id, profile_revision: revision } }];
    }
    if (path === "/api/inference/assignments/set") {
      const scope = body.scope;
      const key = scope.kind === "global" ? "global" : scope.kind === "group" ? `group:${scope.group_id}` : `capability:${scope.capability_id}`;
      const head = this.write(key, body.expected_revision, body.entries.map((e: Entry) => this.entry(e.profile_id, e.profile_revision)));
      if ("conflict" in head) return [409, { code: "inference_assignment_revision_conflict" }];
      return [200, this.projection(head, scope)];
    }
    if (path === "/api/inference/assignments/clear") {
      const scope = body.scope;
      const key = scope.kind === "global" ? "global" : scope.kind === "group" ? `group:${scope.group_id}` : `capability:${scope.capability_id}`;
      const head = this.write(key, body.expected_revision, null);
      if ("conflict" in head) return [409, { code: "inference_assignment_revision_conflict" }];
      return [200, { cleared: scope, revision: head.revision }];
    }
    if (path === "/api/concierge/summary-selection") {
      const head = this.write(`capability:${SUMMARY}`, body.expectedAssignmentRevision, [this.entry(body.profileId, body.profileRevision)]);
      if ("conflict" in head)
        return [200, { status: "conflict", capabilityId: SUMMARY, result: { state: "CONFLICT", plainReason: "" }, summaryAssignment: this.summaryAssignment() }];
      return [200, { status: "succeeded", capabilityId: SUMMARY, result: { state: "READY", plainReason: "" }, summaryAssignment: this.summaryAssignment() }];
    }
    throw new Error(`the fake hub has no ${method} ${path}`);
  }
}

let hub: FakeHub;

beforeEach(() => {
  hub = new FakeHub();
  vi.stubGlobal("fetch", vi.fn(async (input: string, init: RequestInit = {}) => {
    const method = init.method ?? "GET";
    const body = typeof init.body === "string" ? JSON.parse(init.body) : undefined;
    const [status, payload] = hub.answer(method, String(input), body);
    return new Response(JSON.stringify(payload), { status, headers: { "content-type": "application/json" } });
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function open() {
  render(<RunsOnCore />);
  await screen.findByTestId("runson-assignments");
  await waitFor(() => expect(hub.calls.some((c) => c.path === "/api/concierge/detect")).toBe(true));
}

/* ── the four repair states (HS-200-04) ── */

// tests/e2e/test_phase200_readiness_glass.py ENGINES and STATES, unchanged.
const ENGINES = [
  { id: "lan:box", kind: "lan", name: "Qwen3.6 35B", host: "192.168.1.43", state: "READY", latencyMs: 41, profileId: "box", baseUrl: "http://192.168.1.43:8080/v1" },
  { id: "local:mlx:whisper-base", kind: "local", name: "Whisper base", host: "THIS DEVICE", state: "READY", runtimeToken: "MLX" },
  { id: "preset:qwen35-08b", kind: "preset", name: "Qwen 3.5 0.8B", host: "THIS DEVICE", state: "WAITING", sizeBytes: 532_000_000, installed: false, presetId: "qwen35-08b" },
];

function repairRow(token: string, verb: string, control: string, over: Record<string, unknown>) {
  // concierge_service._repair_row's keys, in its order.
  return {
    id: `${token.toLowerCase().replace(/ /g, "-")}:${String(over.subject)}`,
    token, subject: "", host: "", scope: "local", groups: [] as string[], groupLabels: [] as string[],
    verb, control, engineId: "", presetId: "", baseUrl: "", detail: "", ...over,
  };
}

const STATES: Record<string, ReturnType<typeof repairRow>> = {
  "credential-expired": repairRow("CREDENTIAL EXPIRED", "Connections", "connections", {
    subject: "Migrated intel endpoint", host: "api.openai.com", scope: "cloud",
    groups: ["thoughts_notes", "writing_dictation"], groupLabels: ["Thoughts & notes", "Writing & dictation"], engineId: "cloud:legacy-intel",
  }),
  "endpoint-unreachable": repairRow("ENDPOINT UNREACHABLE", "Check", "endpoint_editor", {
    subject: "Qwen3.6 35B", host: "192.168.1.43", groups: ["meetings"], groupLabels: ["Meetings"],
    engineId: "lan:box", baseUrl: "http://192.168.1.43:8080/v1",
  }),
  "model-file-missing": repairRow("MODEL FILE MISSING", "Download", "model_library", {
    subject: "Qwen 3.5 0.8B", host: "THIS DEVICE", groups: ["writing_dictation"], groupLabels: ["Writing & dictation"],
    engineId: "local:qwen35-08b", presetId: "qwen35-08b",
  }),
  "tool-incompatible": repairRow("TOOL INCOMPATIBLE", "Choose", "engine_picker", {
    subject: "Whisper base", host: "THIS DEVICE", groups: ["agents_tools"], groupLabels: ["Agents & tools"],
    engineId: "local:mlx:whisper-base", detail: "capability_tools_unsupported",
  }),
};

describe("Runs on — each repair state is drawn on its job with one verb", () => {
  it.each(Object.keys(STATES))("%s", async (state) => {
    // replaces: tests/e2e/test_phase200_readiness_glass.py::test_each_repair_state_is_drawn_with_one_verb
    // (the 393 no-sideways-scroll and chip-not-clipped halves are the generic sweep's, T3)
    hub.engines = ENGINES;
    hub.repairs = [STATES[state]];
    await open();
    const repair = STATES[state];
    const job = repair.groups[0];

    // The state names itself on the job it breaks.
    const said = await screen.findByTestId(`runson-job-repair-${job}`);
    expect(said.textContent).toContain(repair.token);
    expect(["broken", "waiting"]).toContain(screen.getByTestId(`switchboard-job-${job}`).getAttribute("data-state"));

    // ONE verb, and it is the library Button.
    const root = screen.getByTestId("runson-root");
    const verbs = root.querySelectorAll("button[data-testid^='runson-repair-']");
    expect(verbs).toHaveLength(1);
    expect(verbs[0].className.split(" ")).toContain("btn");

    // No raw <button> in the face (UX-CANON A1).
    const raw = [...root.querySelectorAll("button")].filter((b) => {
      const c = b.className.split(" ");
      return !c.includes("btn") && !c.includes("desk-mic") && !c.includes("gadget-chip-egress");
    });
    expect(raw.map((b) => b.textContent)).toEqual([]);

    // No prose: a token, never the service's sentence.
    const words = (said.textContent ?? "").replace(verbs[0].textContent ?? "", "").trim();
    expect(words.length).toBeLessThanOrEqual(40);
    if (repair.detail) expect(screen.getByTestId("runson-assignments").querySelector(".switchboard")!.textContent).not.toContain(repair.detail);
  });
});

/* ── the rows that live under the board ── */

describe("Runs on — the Meaning search row sits in the window", () => {
  it("OFF names the download and its destination; Turn on is the one verb", async () => {
    // replaces: tests/e2e/test_meaning_search_row_glass.py::test_off_and_downloading (the row in Runs on;
    // DOWNLOADING n%, Turn off and the refusals are fenced in features/concierge/__tests__/meaningSearchRow.test.tsx)
    await open();
    const row = await screen.findByTestId("concierge-meaning-search");
    expect(screen.getByTestId("runson-root").contains(row)).toBe(true);
    await waitFor(() => expect(within(row).getByTestId("meaning-search-state").getAttribute("data-state")).toBe("off"));
    expect(row.textContent).toContain("Meaning search");
    expect(row.textContent).toContain("HUGGINGFACE.CO");
    expect(row.textContent).toContain("DOWNLOAD");
    expect(within(row).getByTestId("meaning-search-verb").textContent).toBe("Turn on");
    expect(document.querySelectorAll("[role='dialog']")).toHaveLength(0);
  });
});

describe("Runs on — speech not set up", () => {
  it("the Speech job says it and offers one sized verb with its host", async () => {
    // replaces: tests/e2e/test_philo17_speech_glass.py::test_every_speech_face_says_speech_is_not_set_up (the Runs on face)
    hub.speechReady = false;
    await open();
    const row = await screen.findByTestId("runson-speech-setup");
    expect(screen.getByTestId("runson-speech-setup-line").textContent).toBe("Speech is not set up");
    expect(screen.getByTestId("runson-speech-setup-verb").textContent).toMatch(/^Set up speech · \d+ MB$/);
    expect(row.textContent?.toUpperCase()).toContain("HUGGINGFACE.CO");
  });
});

/* ── a NOT_SUPPORTED row (PHILO-15 05). Since Betterment E4 the hub sends
   this state only for an agent profile it cannot read; the face's rule for
   the state is unchanged. ── */

describe("Runs on — a NOT_SUPPORTED plate reads NOT SUPPORTED YET", () => {
  it("never READY, no verb, a broken lamp, and a job refuses it", async () => {
    // replaces: tests/e2e/test_philo15_05_strong_defaults_glass.py::test_the_runs_on_anthropic_plate_reads_not_supported_yet
    // (the hub's NOT_SUPPORTED is tests/unit/test_philo15_05_anthropic_not_supported.py; the refusal reads
    // the engine's `state` only, features/runson/model.ts acceptsRule)
    hub.engines = [
      // concierge_service.detect's cloud row for the glass's two legacy profiles.
      { id: "cloud:cloud-anthropic", kind: "cloud", name: "Claude", quantToken: null, legacyLabel: "Claude", host: "api.anthropic.com",
        state: "NOT_SUPPORTED", keySet: false, profileId: "cloud-anthropic", baseUrl: "https://api.anthropic.com/v1" },
      { id: "cloud:cloud-openrouter", kind: "cloud", name: "OpenRouter Qwen", quantToken: null, legacyLabel: "OpenRouter Qwen", host: "openrouter.ai",
        state: "NOT_SET", keySet: false, profileId: "cloud-openrouter", baseUrl: "https://openrouter.ai/api/v1" },
    ];
    await open();
    const plate = await screen.findByTestId("switchboard-engine-cloud-anthropic");
    expect(plate.textContent).toContain("NOT SUPPORTED YET");
    expect(plate.textContent).not.toContain("READY");
    expect(plate.querySelectorAll("button")).toHaveLength(0);
    expect(screen.getByTestId("switchboard-lamp-cloud-anthropic").getAttribute("data-lamp")).toBe("broken");
    fireEvent.click(screen.getByTestId("switchboard-job-thoughts_notes"));
    fireEvent.keyDown(plate, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/REFUSED .* NOT SUPPORTED/));
    expect(hub.calls.some((c) => c.path === "/api/inference/assignments/set")).toBe(false);
  });
});

/* ── a stranger connects an engine (HS-201-09) ── */

describe("Runs on — a stranger connects an engine and the face keeps his choice", () => {
  const BAD = "http://127.0.0.1:9/v1";
  const GOOD = "http://192.168.1.50:8080/v1";
  // Betterment E3: one engine for each model, so the model is in the id.
  const KEY = "engine-192-168-1-50-8080-stub-openai-compatible";
  const MODEL = "stub-openai-compatible";

  function field(): HTMLInputElement {
    return within(screen.getByTestId("concierge-add-engine-row")).getAllByRole("textbox")[0] as HTMLInputElement;
  }
  async function patchOnto(job: string) {
    const before = hub.calls.filter((c) => c.path === "/api/inference/assignments/set").length;
    fireEvent.click(screen.getByTestId(`switchboard-job-${job}`));
    fireEvent.keyDown(screen.getByTestId(`switchboard-engine-${KEY}`), { key: "Enter" });
    await waitFor(() => expect(hub.calls.filter((c) => c.path === "/api/inference/assignments/set").length).toBe(before + 1));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^PATCHED /));
    return hub.calls.filter((c) => c.path === "/api/inference/assignments/set").at(-1)!.body as Record<string, unknown>;
  }

  it("refused address, READY check, Add with no wire, Meetings and Default patches, Undo twice, again over the tombstone", async () => {
    // replaces: tests/e2e/test_hs201_09_connect_engine_glass.py::TestConnectAnEngineFromTheFace::test_a_stranger_connects_an_engine_and_the_face_keeps_his_choice
    // (the face half; the hub half is tests/integration/test_desk_runs_on_hub.py. The pixel legs: the
    // reason's box near the verb and no ink overlap at 393, are the generic sweep's, T3.)
    hub.endpoints.set(GOOD, [MODEL]);
    await open();

    // Add an engine is the library Button.
    const add = screen.getByTestId("concierge-add-engine");
    expect(add.tagName).toBe("BUTTON");
    expect(add.className.split(" ")).toContain("btn");
    expect(add.textContent?.trim()).toBe("Add an engine");
    fireEvent.click(add);
    fireEvent.click(screen.getByTestId("runson-kind-lan")); // Betterment E4: the kind first

    // A bad address: the token sits in the add row, beside the verb; Add stays off.
    fireEvent.change(field(), { target: { value: BAD } });
    expect(screen.getByTestId("concierge-add-egress").textContent).toContain("127.0.0.1");
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    const reason = await screen.findByTestId("concierge-add-reason");
    expect(reason.textContent).toBe("127.0.0.1:9");
    const row = screen.getByTestId("concierge-add-engine-row");
    expect(row.contains(reason)).toBe(true);
    expect(row.textContent).toContain("UNREACHABLE");
    expect(row.textContent).not.toContain("Nothing answers"); // tokens, never the server's sentence
    expect(screen.queryByTestId("concierge-add-use")).toBeNull();

    // The engine's address: READY and the picker lists its model, picked by
    // nobody (Betterment E3); an edit drops it.
    fireEvent.change(field(), { target: { value: GOOD } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    const pick = await screen.findByTestId("concierge-add-pick");
    expect(pick.getAttribute("data-model")).toBe(MODEL);
    expect(within(pick).getByTestId("concierge-add-use").textContent?.trim()).toBe("Use");
    fireEvent.change(field(), { target: { value: GOOD.replace("/v1", "/v2") } });
    await waitFor(() => expect(screen.queryByTestId("concierge-add-picker")).toBeNull());
    fireEvent.change(field(), { target: { value: GOOD } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await screen.findByTestId("concierge-add-pick");

    // Use: the engine joins the column, with no wire and no assignment.
    fireEvent.click(screen.getByTestId("concierge-add-use"));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^ADDED /));
    await screen.findByTestId(`switchboard-engine-${KEY}`);
    expect(screen.queryAllByTestId("switchboard-wire").filter((w) => w.getAttribute("data-engine") === KEY)).toHaveLength(0);
    expect(hub.calls.some((c) => c.path === "/api/inference/assignments/set")).toBe(false);

    // Meetings: the group chain AND the exact summary row the queue reads.
    const meetings = await patchOnto("meetings");
    expect(meetings.scope).toEqual({ kind: "group", group_id: "meetings" });
    await waitFor(() => expect(hub.summaryAssignment()).toMatchObject({ status: "assigned", profileId: KEY }));

    // The Default for AI work.
    const global = await patchOnto("default");
    expect(global.scope).toEqual({ kind: "global" });
    expect((global.entries as Array<{ profile_id: string }>).map((e) => e.profile_id)).toEqual([KEY]);
    expect(screen.getAllByTestId("runson-undo")).toHaveLength(1);

    // Undo, Undo: the Default, then Meetings and its summary row back to inheritance.
    fireEvent.click(screen.getByTestId("runson-undo"));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^UNDONE .*Default engine/));
    fireEvent.click(screen.getByTestId("runson-undo"));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^UNDONE .*Meeting summaries$/));
    const summaryTask = hub.roster().task_overrides.find((t) => t.id === SUMMARY)!;
    expect(summaryTask.has_override).toBe(false);

    // Back ON over the tombstone: no CHANGED ELSEWHERE.
    await patchOnto("meetings");
    await waitFor(() => expect(hub.summaryAssignment()).toMatchObject({ status: "assigned", profileId: KEY }));
    expect(screen.getByTestId("runson-receipt").textContent).not.toContain("CHANGED ELSEWHERE");
  });
});

/* ── the recorded hub (PHILO-17 test diet, final lane A) ──
 *
 * The SCAR LAW: these describes replay the hub's OWN answers, captured on a
 * real hub by tests/integration/test_desk_runs_on_hub.py (HOLDSPEAK_WIRE_WRITE=1
 * rewrites them; every pytest run fences their shape against the hub). One
 * scenario is one boot: the reads the window makes on open, the answer to each
 * press, and the reads after it. A read the recording does not hold fails. */

const RECORDED = import.meta.glob("./fixtures/runs-on-truth/**/*.json", { eager: true, import: "default" }) as Record<
  string,
  { wire: unknown }
>;

function recorded(scenario: string, name: string): unknown {
  const file = RECORDED[`./fixtures/runs-on-truth/${scenario}/${name}.json`];
  if (!file) throw new Error(`no recorded answer ${scenario}/${name}`);
  return structuredClone(file.wire);
}

/** Replays one scenario. `presses` maps a POST path to [its answer, the stage
 *  the hub is in after it]. */
class RecordedHub {
  stage: string;
  calls: Array<{ method: string; path: string; body: unknown }> = [];
  misses: string[] = [];
  constructor(
    readonly scenario: string,
    first: string,
    readonly presses: Record<string, [string, string | null]> = {},
  ) {
    this.stage = first;
  }
  answer(method: string, path: string, body: unknown): [number, unknown] {
    this.calls.push({ method, path, body });
    if (method === "GET") {
      try {
        return [200, recorded(this.scenario, `${this.stage}${path.replace(/\//g, "_")}`)];
      } catch {
        this.misses.push(`${method} ${path}`);
        return [404, {}];
      }
    }
    const press = this.presses[path];
    if (!press) {
      this.misses.push(`${method} ${path}`);
      return [404, {}];
    }
    if (press[1]) this.stage = press[1];
    return [200, recorded(this.scenario, press[0])];
  }
}

function replay(hub: RecordedHub) {
  vi.stubGlobal("fetch", vi.fn(async (input: string, init: RequestInit = {}) => {
    const method = init.method ?? "GET";
    const body = typeof init.body === "string" ? JSON.parse(init.body) : undefined;
    const [status, payload] = hub.answer(method, String(input), body);
    return new Response(JSON.stringify(payload), { status, headers: { "content-type": "application/json" } });
  }));
}

async function openRecorded(rec: RecordedHub) {
  replay(rec);
  render(<RunsOnCore />);
  await screen.findByTestId("runson-assignments");
  await waitFor(() => expect(rec.calls.some((c) => c.path === "/api/concierge/detect")).toBe(true));
}

describe("Runs on — the engine tells the truth (recorded hub)", () => {
  const ENGINE = "http://127.0.0.1:8099/v1";
  const KEY = "engine-127-0-0-1-8099-stub-qwen";

  it("Check names TOOLS; Add keeps the window (ADDED); the Default patch says PATCHED; Agents reads LIMITED with WITHOUT AGENTS", async () => {
    // replaces: tests/e2e/test_philo15_10_engine_truth_glass.py::TestEngineTruth::test_ready_means_ready_and_every_press_leaves_a_receipt
    // (the hub half is tests/integration/test_desk_runs_on_hub.py::test_ready_means_ready_and_a_default_engine_is_limited_where_it_serves_part,
    // which records these answers. The receipt-under-Undo pixel leg is geometry: it stays in test_philo15_12_ugly_glass.py B27.)
    const rec = new RecordedHub("engine-truth", "0-open", {
      "/api/setup/discover-models": ["check", null],
      "/api/inference/model-library/define-endpoint": ["define", "1-added"],
      "/api/inference/assignments/set": ["set-default", "2-patched"],
    });
    await openRecorded(rec);

    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.click(screen.getByTestId("runson-kind-lan")); // Betterment E4: the kind first
    const field = within(screen.getByTestId("concierge-add-engine-row")).getAllByRole("textbox")[0];
    fireEvent.change(field, { target: { value: ENGINE } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    expect((await screen.findByTestId("concierge-add-tools")).textContent).toBe("TOOLS");

    fireEvent.click(screen.getByTestId("concierge-add-use"));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^ADDED .* · stub-qwen · 127\.0\.0\.1:8099$/));
    await screen.findByTestId(`switchboard-engine-${KEY}`);
    expect(screen.getAllByTestId("runson-root")).toHaveLength(1);

    fireEvent.click(screen.getByTestId("switchboard-job-default"));
    fireEvent.keyDown(screen.getByTestId(`switchboard-engine-${KEY}`), { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^PATCHED /));
    const set = rec.calls.filter((c) => c.path === "/api/inference/assignments/set");
    expect(set).toHaveLength(1);
    expect((set[0].body as { scope: unknown }).scope).toEqual({ kind: "global" });
    expect(screen.getAllByTestId("runson-root")).toHaveLength(1);

    // The board after the hub's own reads: READY only where the whole job runs.
    const agents = screen.getByTestId("switchboard-job-agents_tools");
    await waitFor(() => expect(agents.getAttribute("data-state")).toBe("limited"));
    expect(agents.textContent?.toUpperCase()).toContain("WITHOUT AGENTS");
    expect(screen.getByTestId("switchboard-job-thoughts_notes").getAttribute("data-state")).toBe("ready");
    expect(screen.getByTestId("runson-assignments").querySelector(".switchboard")!.textContent).not.toContain("structured result");
    expect(screen.queryByTestId("switchboard-job-chat_practice")).toBeNull();
    expect(rec.misses).toEqual([]);
  });
});

/** The board measures its container (Switchboard.tsx useSwitchboardLayout);
 *  jsdom measures 0, so the phone list is asked for by giving it 393 px. */
function atPhoneWidth() {
  return vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    width: 393, height: 852, top: 0, left: 0, right: 393, bottom: 852, x: 0, y: 0, toJSON: () => ({}),
  } as DOMRect);
}

describe("Runs on — a record-less engine is refused on the drop (recorded hub)", () => {
  it("each job names the refusal with its token, and nothing is written", async () => {
    // replaces: tests/e2e/test_philo15_10_engine_truth_glass.py::TestTwoFailures::test_every_failed_group_is_named_with_its_token [1440]
    // (hub half: test_desk_runs_on_hub.py::test_a_record_less_engine_is_on_the_board_with_no_revision_and_the_hub_refuses_a_write_for_it)
    const rec = new RecordedHub("no-record", "0-open");
    await openRecorded(rec);
    const plate = await screen.findByTestId("switchboard-engine-old-box");
    for (const [job, label] of [["thoughts_notes", "ANSWERS AND NOTES"], ["agents_tools", "CUSTOM TASKS"]]) {
      fireEvent.click(screen.getByTestId(`switchboard-job-${job}`));
      fireEvent.keyDown(plate, { key: "Enter" });
      await waitFor(() =>
        expect(screen.getByTestId("runson-receipt").textContent).toMatch(new RegExp(`^REFUSED · ${label} · NO MODEL RECORD$`)),
      );
    }
    expect(rec.calls.filter((c) => c.method !== "GET")).toEqual([]);
    expect(rec.misses).toEqual([]);
  });

  it("the phone list never offers it to a job", async () => {
    // replaces: tests/e2e/test_philo15_10_engine_truth_glass.py::TestTwoFailures::test_every_failed_group_is_named_with_its_token [393]
    const spy = atPhoneWidth();
    try {
      const rec = new RecordedHub("no-record", "0-open");
      await openRecorded(rec);
      await waitFor(() => expect(screen.getByTestId("runson-assignments").querySelector(".switchboard")!.getAttribute("data-layout")).toBe("list"));
      for (const job of ["thoughts_notes", "agents_tools"]) {
        fireEvent.click(screen.getByTestId(`switchboard-job-${job}`));
        await screen.findByText(/ · engine$/i); // the job's card is open
        expect(screen.queryByTestId("switchboard-tap-old-box")).toBeNull();
      }
      expect(rec.calls.filter((c) => c.method !== "GET")).toEqual([]);
    } finally {
      spy.mockRestore();
    }
  });
});

describe("Runs on — Anthropic is a service, never a NOT SUPPORTED YET dead end (recorded hub)", () => {
  it("with no key held the plate reads NO KEY, never NOT SUPPORTED YET or READY", async () => {
    // Betterment E4 (DECISIONS #9): Anthropic runs through its OpenAI-compatible
    // endpoint. The hub half is test_desk_runs_on_hub.py::test_an_anthropic_profile_is_a_service_on_the_hub.
    const rec = new RecordedHub("anthropic", "0-open");
    await openRecorded(rec);
    const plate = await screen.findByTestId("switchboard-engine-cloud-anthropic");
    expect(plate.textContent).toContain("NO KEY");
    expect(plate.textContent).not.toContain("NOT SUPPORTED");
    expect(plate.textContent).not.toContain("READY");
    expect(rec.calls.filter((c) => c.method !== "GET")).toEqual([]);
    expect(rec.misses).toEqual([]);
  });

  it("at 393 the job list offers no tap for it", async () => {
    // replaces: tests/e2e/test_philo15_05_strong_defaults_glass.py::test_the_runs_on_anthropic_plate_reads_not_supported_yet [393]
    // Since E4 the reason is the legacy profile's missing model record, not the provider.
    const spy = atPhoneWidth();
    try {
      const rec = new RecordedHub("anthropic", "0-open");
      await openRecorded(rec);
      await waitFor(() => expect(screen.getByTestId("runson-assignments").querySelector(".switchboard")!.getAttribute("data-layout")).toBe("list"));
      fireEvent.click(screen.getByTestId("switchboard-job-thoughts_notes"));
      await screen.findByText(/ · engine$/i); // the job's card is open
      expect(screen.queryByTestId("switchboard-tap-cloud-anthropic")).toBeNull();
    } finally {
      spy.mockRestore();
    }
  });
});

// Betterment E5 (DECISIONS #8): the drag switchboard these tests drive is
// parked behind Builder tools; What runs where is engines.app.test.tsx.
beforeEach(() => {
  useBuilderTools.getState().setOn(true);
});
afterEach(() => {
  useBuilderTools.getState().setOn(false);
});
