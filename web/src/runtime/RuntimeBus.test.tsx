import { render, screen, waitFor } from "@testing-library/react";
import { useEffect, useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RuntimeBusProvider, useRuntimeBus } from "./RuntimeBus";

class FakeSocket extends EventTarget {
  static OPEN = 1;
  static CONNECTING = 0;
  static instances: FakeSocket[] = [];
  readyState = FakeSocket.CONNECTING;
  send = vi.fn();
  close = vi.fn(() => this.dispatchEvent(new CloseEvent("close")));

  constructor(
    readonly url: string,
    readonly protocols?: string | string[],
  ) {
    super();
    FakeSocket.instances.push(this);
    queueMicrotask(() => {
      this.readyState = FakeSocket.OPEN;
      this.dispatchEvent(new Event("open"));
    });
  }
}

function Consumer() {
  const { state, subscribe } = useRuntimeBus();
  const [label, setLabel] = useState("");
  useEffect(
    () =>
      subscribe("runtime_activity", (frame) =>
        setLabel(String((frame.data as { label?: string }).label ?? "")),
      ),
    [subscribe],
  );
  return (
    <div>
      {state}:{label}
    </div>
  );
}

describe("RuntimeBusProvider", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    FakeSocket.instances = [];
  });

  it("owns one socket and removes it with the provider", async () => {
    vi.stubGlobal("WebSocket", FakeSocket);
    const view = render(
      <RuntimeBusProvider>
        <Consumer />
      </RuntimeBusProvider>,
    );
    await screen.findByText("connected:");
    expect(FakeSocket.instances).toHaveLength(1);
    expect(FakeSocket.instances[0].url).not.toContain("token=");
    expect(FakeSocket.instances[0].protocols).toEqual(["holdspeak.v1"]);
    FakeSocket.instances[0].dispatchEvent(
      new MessageEvent("message", {
        data: JSON.stringify({
          type: "runtime_activity",
          data: { label: "Listening" },
        }),
      }),
    );
    await screen.findByText("connected:Listening");
    view.unmount();
    await waitFor(() =>
      expect(FakeSocket.instances[0].close).toHaveBeenCalled(),
    );
  });
});
