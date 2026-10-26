import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.hoisted(() => vi.fn());
const deskChanges = vi.hoisted(() => new Set<() => void>());

vi.mock("../../../lib/api", () => ({ apiFetch }));
vi.mock("../../useDeskChangedRefresh", async () => {
  const React = await import("react");
  return {
    useOnDeskChanged: (reload: () => void) => {
      React.useEffect(() => {
        deskChanges.add(reload);
        return () => { deskChanges.delete(reload); };
      }, [reload]);
    },
  };
});

import { clearEngineCache, useEngine } from "../useEngine";

function Probe({ capability }: { capability: string }) {
  const engine = useEngine(capability);
  return (
    <output data-testid={capability}>
      {engine.state}|{engine.model}
    </output>
  );
}

const roster = (askLabel: string, thoughtLabel: string) => ({
  task_overrides: [
    {
      id: "ask.answer",
      effective: {
        status: "assigned",
        assignment: {
          entries: [{ profile_id: "profile-ask-internal", label: askLabel, boundary: "same_device" }],
        },
      },
    },
    {
      id: "thought.interview",
      effective: {
        status: "assigned",
        assignment: {
          entries: [{ profile_id: "profile-thought-internal", label: thoughtLabel, boundary: "same_device" }],
        },
      },
    },
  ],
});

describe("useEngine", () => {
  afterEach(() => {
    clearEngineCache();
    deskChanges.clear();
    apiFetch.mockReset();
  });

  it("shares one roster read and refreshes every mounted capability together", async () => {
    apiFetch
      .mockResolvedValueOnce(roster("Ask engine", "Thought engine"))
      .mockResolvedValueOnce(roster("New ask engine", "New thought engine"));
    render(
      <>
        <Probe capability="ask.answer" />
        <Probe capability="thought.interview" />
      </>,
    );

    await screen.findByText("set|Ask engine");
    expect(screen.getByTestId("thought.interview")).toHaveTextContent(
      "set|Thought engine",
    );
    expect(screen.getByTestId("ask.answer")).not.toHaveTextContent("profile-ask-internal");
    expect(apiFetch).toHaveBeenCalledTimes(1);

    act(() => {
      deskChanges.forEach((reload) => reload());
    });
    await waitFor(() =>
      expect(screen.getByTestId("ask.answer")).toHaveTextContent(
        "set|New ask engine",
      ),
    );
    expect(screen.getByTestId("thought.interview")).toHaveTextContent(
      "set|New thought engine",
    );
    expect(apiFetch).toHaveBeenCalledTimes(2);
  });
});
