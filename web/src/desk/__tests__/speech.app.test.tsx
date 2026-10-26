// Speech not set up, on every face that needs speech (PHILO-17 speech).
//
// The test diet (2026-10-11): the browser test staged each face on a fresh
// hub with no speech model and read the row. Here each face renders whole,
// with its real hooks, against a fake hub: `fetch` answers GET
// /api/setup/local-ai with the first-run Local AI status the hub gives
// (`speech` = whisper_models.speech_readiness, as in
// desk/firstrun/__tests__/SpeechSetup.test.tsx), and every other read with
// the hub's own 404 body, so no face is fed a shape the hub never sends.
// Live meeting's runtime socket (RuntimeBus) is the one other transport,
// held quiet. The Runs on face is fenced in runs-on.app.test.tsx.

import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

import { SpeakFace } from "../../pages/cores/dictation/SpeakFace";
import { LiveCore } from "../../pages/cores/LiveCore";
import { SetupCore } from "../../pages/cores/SetupCore";

const VERB = /^Set up speech · \d+ MB$/;

// The hub with no speech model (the rig's isolated HOME): `will_download`.
const LOCAL_AI = {
  state: "not_started",
  files: [
    { key: "whisper", label: "whisper-base-mlx", size_bytes: 144_000_000, on_device: false, url: "https://huggingface.co/a" },
    { key: "embed", label: "nomic-embed-text v1.5", size_bytes: 146_000_000, on_device: false },
  ],
  bytes_total: 0,
  bytes_done: 0,
  egress: { destination: "huggingface.co" },
  speech: { model: "base", backend: "mlx", state: "will_download", ready: false, bytes: 144_000_000 },
  error: "",
};

// GET /api/setup/status on that hub (setup_status.build_setup_status): the
// doctor's "Speech model" check fails (commands/doctor.py _check_speech_model).
const SETUP_STATUS = {
  overall: "blocked",
  first_run: false,
  sections: [
    {
      id: "speech-model", label: "Speech model", status: "fail",
      detail: "Speech is not set up: Whisper base (mlx) is not on this device", fix: "Set up speech",
    },
  ],
};

const SETUP_FOUND = {
  rows: [{
    id: "speech", kind: "speech", label: "Speech", detail: "Whisper base · 144 MB",
    state: "found", reason: "", egress_host: "huggingface.co", verb: "Set up speech",
    action: "speech", payload: {},
  }],
  owner_name: "",
  people: [],
  suggestions: [],
  first_run: true,
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      const path = String(input).split("?")[0];
      const [status, body] =
        path === "/api/setup/local-ai" ? [200, LOCAL_AI] : path === "/api/setup/status" ? [200, SETUP_STATUS] : [404, { detail: "Not Found" }];
      if (path === "/api/setup/found") return new Response(JSON.stringify(SETUP_FOUND), { status: 200, headers: { "content-type": "application/json" } });
      if (path === "/api/setup/lan") return new Response(JSON.stringify({ rows: [] }), { status: 200, headers: { "content-type": "application/json" } });
      if (path === "/api/settings") return new Response(JSON.stringify({ owner: { name: "", aliases: [] }, _revision: "1" }), { status: 200, headers: { "content-type": "application/json" } });
      return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
    }),
  );
});

afterEach(() => vi.unstubAllGlobals());

function expectTheRow(testId: string, withLine = true) {
  const verb = screen.getByTestId(`${testId}-verb`);
  expect(verb.textContent?.trim()).toMatch(VERB);
  expect(verb.className.split(" ")).toContain("btn");
  if (withLine) expect(screen.getByTestId(`${testId}-line`).textContent).toBe("Speech is not set up");
  // Egress where the fetch happens: the host chip beside the verb.
  expect(screen.getByTestId(testId).textContent?.toUpperCase()).toContain("HUGGINGFACE.CO");
}

describe("every speech face says speech is not set up", () => {
  // replaces: tests/e2e/test_philo17_speech_glass.py::test_every_speech_face_says_speech_is_not_set_up

  it("Speak: Talk is live and its press opens the setup in place (betterment C8, one Talk rule)", async () => {
    render(<SpeakFace />);
    const talk = await screen.findByTestId("speak-speech-setup-key");
    expect(talk).not.toBeDisabled();
    fireEvent.click(talk);
    await screen.findByTestId("speak-speech-setup-verb");
    // The press is "where you pressed Talk": the verb alone, no sentence.
    expectTheRow("speak-speech-setup", false);
  });

  it("Live meeting: the exact audio-only state, never the old Ready to record", async () => {
    render(<LiveCore />);
    const verb = await screen.findByTestId("live-speech-setup-verb");
    expect(verb.textContent?.trim()).toMatch(VERB);
    expect(verb.className.split(" ")).toContain("btn");
    // Window grammar + UX-CANON A.9 (2026-10-25): the verb is a toolbar
    // item; the host is its hover title, never a chip on the row.
    expect(verb.closest('[role="toolbar"]')).not.toBeNull();
    expect(verb.getAttribute("title")).toContain("huggingface.co");
    expect(screen.getByTestId("live-speech-setup").textContent?.toUpperCase()).not.toContain("HUGGINGFACE.CO");
    // The state is the status bar's words: Ready · audio only · Speech not set up.
    const bar = screen.getByTestId("live-statusbar");
    expect(bar).toHaveTextContent(/Ready.*audio only.*Speech not set up/);
    expect(screen.queryByText("Ready to record", { exact: true })).toBeNull();
    expect(screen.queryByText("Ready to record audio only", { exact: true })).toBeNull();
  });

  it("Setup: the producer-backed face says it; the verb stands alone on it", async () => {
    render(<SetupCore />);
    const face = await screen.findByTestId("setup-face");
    expect(within(face).getByRole("button", { name: "Set up speech" })).toBeTruthy();
    expect(face).toHaveTextContent("huggingface.co");
  });
});
