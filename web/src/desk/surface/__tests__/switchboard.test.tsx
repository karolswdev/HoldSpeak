// PHILO-16 (C) — SurfaceSwitchboard: the species decides nothing; it draws
// five states, solid and dashed wires, and turns a drag or a tap into
// `onPatch` / `onRefuse`.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SurfaceSwitchboard, type SwitchEngine, type SwitchJob, type SwitchWire } from "../index";
import { Button } from "../../../components/signal/Signal";

const JOBS: SwitchJob[] = [
  { id: "speech", name: "Speech", tasks: "SPEECH → TEXT", state: "ready" },
  { id: "meetings", name: "Meetings", tasks: "SUMMARIES", state: "limited" },
  { id: "agents", name: "Agents & tools", tasks: "PLAN · CODE", state: "broken" },
  { id: "bg", name: "Background", tasks: "MEMORY", state: "waiting" },
  { id: "default", name: "Default for AI work", tasks: "EVERY JOB", state: "off", isDefault: true },
];

const ENGINES: SwitchEngine[] = [
  { id: "whisper", emblem: "MAC", name: "Whisper small", tokens: ["MLX", "SPEECH"], lamp: "ok", draggable: true },
  { id: "q27", emblem: "LAN", name: "qwen3.8 27B", tokens: ["32K", "410 MS"], lamp: "ok", draggable: true },
  { id: "vision", emblem: "MAC", name: "Vision file", tokens: ["890 MB"], lamp: "warn", progress: 42 },
];

const WIRES: SwitchWire[] = [
  { job: "speech", engine: "whisper", order: 0 },
  { job: "meetings", engine: "q27", order: 0, tone: "limited" },
  { job: "meetings", engine: "whisper", order: 1 },
  { job: "agents", engine: "q27", order: 0, tone: "broken" },
];

const speechOnly = (job: string, engine: string) =>
  job === "speech" ? (engine === "whisper" ? { ok: true } : { ok: false, reason: "SPEECH ENGINES ONLY" }) : engine === "whisper" ? { ok: false, reason: "TEXT ENGINES ONLY" } : { ok: true };

afterEach(() => {
  vi.restoreAllMocks();
});

describe("SurfaceSwitchboard (board)", () => {
  it("draws every job with its state and every wire with its order and tone", () => {
    render(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} captions={{ jobs: "What HoldSpeak does", engines: "What you have" }} />);
    expect(screen.getByText("What HoldSpeak does")).toBeTruthy();
    const states = JOBS.map((job) => screen.getByTestId(`switchboard-job-${job.id}`).getAttribute("data-state"));
    expect(states).toEqual(["ready", "limited", "broken", "waiting", "off"]);
    expect(screen.getByTestId("switchboard-job-default").className).toContain("is-default");
    const wires = screen.getAllByTestId("switchboard-wire");
    expect(wires).toHaveLength(4);
    const meetFallback = wires.find((w) => w.getAttribute("data-job") === "meetings" && w.getAttribute("data-order") === "1")!;
    expect(meetFallback.getAttribute("class")).toContain("is-fallback");
    const meetFirst = wires.find((w) => w.getAttribute("data-job") === "meetings" && w.getAttribute("data-order") === "0")!;
    expect(meetFirst.getAttribute("class")).toContain("is-limited");
    expect(meetFirst.getAttribute("class")).not.toContain("is-fallback");
    const agents = wires.find((w) => w.getAttribute("data-job") === "agents")!;
    expect(agents.getAttribute("class")).toContain("is-broken");
    // Every wire carries a cubic path, even in a layout-free DOM.
    for (const wire of wires) expect(wire.getAttribute("d")).toMatch(/^M-?[\d.]+,-?[\d.]+ C/);
  });

  it("lights the selected job's wires hot and pulses the job on trial", () => {
    render(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} selected="meetings" pulse="speech" />);
    const wires = screen.getAllByTestId("switchboard-wire");
    const hot = wires.filter((w) => w.getAttribute("class")!.includes("is-hot")).map((w) => w.getAttribute("data-job"));
    expect(hot).toEqual(["meetings", "meetings"]);
    const pulse = wires.filter((w) => w.getAttribute("class")!.includes("is-pulse"));
    expect(pulse.map((w) => w.getAttribute("data-job"))).toEqual(["speech"]);
    expect(screen.getByTestId("switchboard-job-meetings").className).toContain("is-selected");
  });

  it("fills the download bar on the engine itself and draws the lamp", () => {
    render(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} />);
    const bar = screen.getByTestId("switchboard-bar-vision");
    expect(bar.getAttribute("aria-valuenow")).toBe("42");
    expect((bar.firstElementChild as HTMLElement).style.width).toBe("42%");
    expect(screen.getByTestId("switchboard-lamp-vision").getAttribute("data-lamp")).toBe("warn");
    expect(screen.queryByTestId("switchboard-bar-q27")).toBeNull();
  });

  it("clicking a job selects it; clicking again lets go; a verb inside does not select", () => {
    const onSelect = vi.fn();
    const jobs = JOBS.map((j) => (j.id === "speech" ? { ...j, verb: <Button dense>Try it</Button> } : j));
    const { rerender } = render(<SurfaceSwitchboard jobs={jobs} engines={ENGINES} wires={WIRES} onSelect={onSelect} />);
    fireEvent.click(screen.getByTestId("switchboard-job-meetings"));
    expect(onSelect).toHaveBeenLastCalledWith("meetings");
    rerender(<SurfaceSwitchboard jobs={jobs} engines={ENGINES} wires={WIRES} onSelect={onSelect} selected="meetings" />);
    fireEvent.click(screen.getByTestId("switchboard-job-meetings"));
    expect(onSelect).toHaveBeenLastCalledWith(null);
    onSelect.mockClear();
    fireEvent.click(screen.getByRole("button", { name: "Try it" }));
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("a drag onto a job patches (first); with ⌥ it adds a fallback; a refused drop names why", () => {
    const onPatch = vi.fn();
    const onRefuse = vi.fn();
    render(
      <SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} accepts={speechOnly} onPatch={onPatch} onRefuse={onRefuse} />,
    );
    const target = { current: screen.getByTestId("switchboard-job-meetings") as Element };
    Object.defineProperty(document, "elementFromPoint", { configurable: true, value: () => target.current });
    const board = screen.getByTestId("switchboard");
    const plate = screen.getByTestId("switchboard-engine-q27");

    fireEvent.pointerDown(plate, { pointerId: 1 });
    fireEvent.pointerMove(board, { pointerId: 1, clientX: 10, clientY: 10 });
    expect(screen.getByTestId("switchboard-job-meetings").className).toContain("is-over");
    fireEvent.pointerUp(board, { pointerId: 1, clientX: 10, clientY: 10 });
    expect(onPatch).toHaveBeenLastCalledWith("meetings", "q27", false);

    fireEvent.pointerDown(plate, { pointerId: 2 });
    // jsdom's pointer events carry no modifier keys; a MouseEvent does.
    fireEvent(board, new MouseEvent("pointerup", { bubbles: true, clientX: 10, clientY: 10, altKey: true }));
    expect(onPatch).toHaveBeenLastCalledWith("meetings", "q27", true);

    // Speech takes speech engines only: the hover says no, the drop refuses.
    target.current = screen.getByTestId("switchboard-job-speech");
    fireEvent.pointerDown(plate, { pointerId: 3 });
    fireEvent.pointerMove(board, { pointerId: 3, clientX: 10, clientY: 10 });
    expect(screen.getByTestId("switchboard-job-speech").className).toContain("is-refused");
    fireEvent.pointerUp(board, { pointerId: 3, clientX: 10, clientY: 10 });
    expect(onRefuse).toHaveBeenCalledWith("speech", "q27", "SPEECH ENGINES ONLY");
    expect(onPatch).toHaveBeenCalledTimes(2);
  });

  it("an ⌥-drop on a job with no wire patches it first (nothing to fall back from)", () => {
    const onPatch = vi.fn();
    render(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} onPatch={onPatch} />);
    Object.defineProperty(document, "elementFromPoint", {
      configurable: true,
      value: () => screen.getByTestId("switchboard-job-bg"),
    });
    fireEvent.pointerDown(screen.getByTestId("switchboard-engine-q27"), { pointerId: 1 });
    fireEvent(screen.getByTestId("switchboard"), new MouseEvent("pointerup", { bubbles: true, altKey: true }));
    expect(onPatch).toHaveBeenCalledWith("bg", "q27", false);
  });

  it("an engine with no model record does not drag", () => {
    const onPatch = vi.fn();
    render(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} onPatch={onPatch} />);
    Object.defineProperty(document, "elementFromPoint", {
      configurable: true,
      value: () => screen.getByTestId("switchboard-job-bg"),
    });
    fireEvent.pointerDown(screen.getByTestId("switchboard-engine-vision"), { pointerId: 1 });
    fireEvent.pointerUp(screen.getByTestId("switchboard"), { pointerId: 1 });
    expect(onPatch).not.toHaveBeenCalled();
  });

  it("keyboard twin: with a job selected, Enter on an engine patches; ⌥Enter adds a fallback", () => {
    const onPatch = vi.fn();
    render(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} selected="meetings" onPatch={onPatch} />);
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    expect(onPatch).toHaveBeenLastCalledWith("meetings", "q27", false);
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter", altKey: true });
    expect(onPatch).toHaveBeenLastCalledWith("meetings", "q27", true);
  });

  it("FOUND: a caption with its count and each plate's one verb; none, no caption", () => {
    const found: SwitchEngine[] = [
      { id: "ollama", emblem: "MAC", name: "Ollama · llama 3.3", tokens: ["127.0.0.1:11434"], lamp: "ok", verb: <Button dense>Use it</Button> },
    ];
    const { rerender } = render(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} found={found} />);
    expect(screen.getByTestId("switchboard-found-cap").textContent).toBe("Found · 1");
    const plate = screen.getByTestId("switchboard-engine-ollama");
    expect(plate.className).toContain("is-found");
    expect(within(plate).getByRole("button", { name: "Use it" })).toBeTruthy();
    expect(plate.querySelector(".switchboard-plug")).toBeNull();
    rerender(<SurfaceSwitchboard jobs={JOBS} engines={ENGINES} wires={WIRES} found={[]} />);
    expect(screen.queryByTestId("switchboard-found-cap")).toBeNull();
  });
});

describe("SurfaceSwitchboard (list, 393)", () => {
  it("opens the selected job to its engine and the alternatives; a tap patches; another job is a tap", () => {
    const onPatch = vi.fn();
    const onSelect = vi.fn();
    render(
      <SurfaceSwitchboard
        layout="list"
        jobs={JOBS}
        engines={ENGINES}
        wires={WIRES}
        selected="meetings"
        accepts={speechOnly}
        onPatch={onPatch}
        onSelect={onSelect}
      />,
    );
    const board = screen.getByTestId("switchboard");
    expect(board.getAttribute("data-layout")).toBe("list");
    expect(screen.getByText("Meetings · runs on")).toBeTruthy();
    // The engine it runs on, then `Or` the alternatives it accepts.
    expect(screen.getByTestId("switchboard-engine-q27")).toBeTruthy();
    expect(screen.queryByTestId("switchboard-tap-whisper")).toBeNull(); // refused: speech only
    expect(screen.queryByTestId("switchboard-tap-vision")).toBeNull(); // no model record
    expect(screen.queryAllByTestId("switchboard-wire")).toHaveLength(0);
    // No raw buttons: every tap is the library Button.
    for (const b of Array.from(board.querySelectorAll("button"))) expect(b.className).toContain("btn");
    fireEvent.click(screen.getByTestId("switchboard-job-agents"));
    expect(onSelect).toHaveBeenCalledWith("agents");
  });

  it("taps an alternative to patch the open job", () => {
    const onPatch = vi.fn();
    const engines = [...ENGINES, { id: "claude", emblem: "API", name: "Claude", tokens: ["$"], lamp: "ok" as const, draggable: true }];
    render(<SurfaceSwitchboard layout="list" jobs={JOBS} engines={engines} wires={WIRES} selected="meetings" accepts={speechOnly} onPatch={onPatch} />);
    fireEvent.click(screen.getByTestId("switchboard-tap-claude"));
    expect(onPatch).toHaveBeenCalledWith("meetings", "claude", false);
  });
});
