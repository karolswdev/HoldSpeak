import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { dispatchKey, dismissSettle, useKeymap } from "../keymap";
import { useSettleState } from "../settleState";
import { useDesk } from "../store";
import { registerSurface } from "../shell";
import { RoomActions } from "../components/window/RoomActions";
import { DeskMenuBar } from "../components/DeskMenuBar";

beforeEach(() => {
  useSettleState.setState({ settled: false });
  useDesk.setState({ recording: "idle", recordingExternal: false });
});
afterEach(() => useSettleState.setState({ settled: false }));

describe("Settle in", () => {
  it("uses the registered shortcut without touching window arrangement or capture", () => {
    const before = useDesk.getState();
    expect(
      dispatchKey(
        new KeyboardEvent("keydown", {
          key: "F",
          metaKey: true,
          shiftKey: true,
        }),
      )?.id,
    ).toBe("desk.settle");
    expect(useSettleState.getState().settled).toBe(true);
    expect(useDesk.getState()).toBe(before);
  });

  it("routes Change places through the existing native surface dispatcher", () => {
    const open = vi.fn();
    const off = registerSurface("change-places", open);
    expect(
      dispatchKey(
        new KeyboardEvent("keydown", {
          key: "P",
          ctrlKey: true,
          shiftKey: true,
        }),
      )?.id,
    ).toBe("go.change-places");
    expect(open).toHaveBeenCalledOnce();
    off();
  });

  it("Escape restores chrome before an editor or window can close, without losing a draft", () => {
    const close = vi.fn();
    function Editor() {
      useKeymap();
      return (
        <textarea
          aria-label="Draft"
          defaultValue="Keep this thought"
          onKeyDown={close}
        />
      );
    }
    render(<Editor />);
    const editor = screen.getByRole("textbox");
    editor.focus();
    act(() => useSettleState.getState().setSettled(true));
    fireEvent.keyDown(editor, { key: "Escape" });
    expect(useSettleState.getState().settled).toBe(false);
    expect(close).not.toHaveBeenCalled();
    expect(editor).toHaveValue("Keep this thought");
    expect(editor).toHaveFocus();
    fireEvent.keyDown(editor, { key: "Escape" });
    expect(close).toHaveBeenCalledOnce();
  });

  it("leaves IME composition and already-handled shortcuts alone", () => {
    useSettleState.getState().setSettled(true);
    expect(
      dismissSettle(
        new KeyboardEvent("keydown", { key: "Escape", isComposing: true }),
      ),
    ).toBe(false);
    expect(useSettleState.getState().settled).toBe(true);
    const event = new KeyboardEvent("keydown", {
      key: "F",
      ctrlKey: true,
      shiftKey: true,
      cancelable: true,
    });
    event.preventDefault();
    expect(dispatchKey(event)).toBeNull();
    expect(useSettleState.getState().settled).toBe(true);
  });

  it("keeps an explicit way back and distinguishes meeting capture states", () => {
    useSettleState.getState().setSettled(true);
    render(<RoomActions />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Meeting recorder idle",
    );
    act(() =>
      useDesk.setState({ recording: "recording", recordingExternal: true }),
    );
    expect(screen.getByRole("status")).toHaveTextContent("Recording elsewhere");
    act(() => useDesk.setState({ recording: "busy" }));
    expect(screen.getByRole("status")).toHaveTextContent("Updating recording");
    fireEvent.click(screen.getByRole("button", { name: /Back to Desk/ }));
    expect(useSettleState.getState().settled).toBe(false);
    expect(useDesk.getState().recording).toBe("busy");
  });
  it("dismisses a portaled navigation menu and moves hidden-chrome focus to Back to Desk", () => {
    render(
      <>
        <DeskMenuBar />
        <RoomActions />
      </>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Go" }));
    const item = screen.getAllByRole("menuitem")[0];
    item.focus();
    act(() => useSettleState.getState().setSettled(true));
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Back to Desk/ })).toHaveFocus();
    act(() => useSettleState.getState().setSettled(false));
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });
});
