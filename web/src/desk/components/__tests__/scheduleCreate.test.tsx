import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";
import { ScheduleCreateWindow } from "../ScheduleCreateWindow";

const create = vi.fn();
beforeEach(() => {
  localStorage.clear(); create.mockReset();
  useDesk.setState({ drafts: {}, scheduleCreateWindow: { origin: null }, createSchedule: create });
});
afterEach(() => { vi.restoreAllMocks(); });

function recurring() {
  fireEvent.change(screen.getByLabelText("Title", { exact: true }), { target: { value: "Release owner check" } });
  fireEvent.change(screen.getByLabelText("Mode", { exact: true }), { target: { value: "recurring" } });
  fireEvent.change(screen.getByLabelText("Cron expression", { exact: true }), { target: { value: "30 14 * * 2" } });
  fireEvent.change(screen.getByLabelText("Duration", { exact: true }), { target: { value: "90" } });
}

function pendingCreate() {
  let resolve!: (accepted: boolean) => void;
  create.mockImplementationOnce(() => new Promise<boolean>((finish) => { resolve = finish; }));
  fireEvent.click(screen.getByTestId("schedule-create-submit"));
  expect(create).toHaveBeenCalledTimes(1);
  return async () => { await act(async () => { resolve(true); }); };
}

describe("new schedule draft custody", () => {
  it("keeps microphone controls in both time modes and rejects a past time without losing it", async () => {
    render(<ScheduleCreateWindow />);
    expect(screen.getByRole("button", { name: /^Speak When(?: ·|$)/ })).toBeTruthy();
    const when = screen.getByLabelText("When");
    expect(when).toHaveAttribute("type", "datetime-local");
    fireEvent.change(when, { target: { value: "2001-01-01T09:00" } });
    fireEvent.click(screen.getByTestId("schedule-create-submit"));
    const refusal = await screen.findByRole("alert");
    expect(refusal.textContent).toContain("Time must be future");
    expect(refusal.closest(".surface-footer-receipt")).toBeTruthy();
    expect(when).toHaveValue("2001-01-01T09:00");
    expect(create).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Mode"), { target: { value: "recurring" } });
    expect(screen.getByRole("button", { name: /^Speak Cron expression(?: ·|$)/ })).toBeTruthy();
  });

  it("keeps edited operation B open when pending operation A succeeds", async () => {
    render(<ScheduleCreateWindow />);
    fireEvent.change(screen.getByLabelText("When"), { target: { value: "2099-10-14T09:00" } });
    recurring();
    const finishA = pendingCreate();
    fireEvent.change(screen.getByLabelText("Title", { exact: true }), { target: { value: "New owner check" } });
    fireEvent.change(screen.getByLabelText("Mode"), { target: { value: "one-shot" } });
    fireEvent.change(screen.getByLabelText("When"), { target: { value: "2099-10-15T14:30" } });
    fireEvent.change(screen.getByLabelText("Duration"), { target: { value: "30" } });
    const draftB = { ...useDesk.getState().drafts };
    const windowB = useDesk.getState().scheduleCreateWindow;
    await finishA();
    expect(useDesk.getState().scheduleCreateWindow).toBe(windowB);
    expect(useDesk.getState().drafts).toEqual(draftB);
    expect(screen.getByLabelText("Title", { exact: true })).toHaveValue("New owner check");
    expect(screen.getByLabelText("Mode")).toHaveValue("one-shot");
    expect(screen.getByLabelText("When")).toHaveValue("2099-10-15T14:30");
    expect(screen.getByLabelText("Duration")).toHaveValue("30");
    expect(create).toHaveBeenCalledTimes(1);
    expect(create).toHaveBeenCalledWith(expect.objectContaining({ title: "Release owner check", one_shot: false, cron_expr: "30 14 * * 2", duration_minutes: 90 }));
  });

  it("keeps reopened draft B when operation A from the previous form succeeds", async () => {
    render(<ScheduleCreateWindow />); recurring();
    const finishA = pendingCreate();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    act(() => useDesk.getState().openScheduleCreate());
    fireEvent.change(screen.getByLabelText("Title", { exact: true }), { target: { value: "Reopened owner check" } });
    fireEvent.change(screen.getByLabelText("Cron expression"), { target: { value: "15 10 * * 3" } });
    fireEvent.change(screen.getByLabelText("Duration"), { target: { value: "120" } });
    const draftB = { ...useDesk.getState().drafts };
    const windowB = useDesk.getState().scheduleCreateWindow;
    await finishA();
    expect(useDesk.getState().scheduleCreateWindow).toBe(windowB);
    expect(useDesk.getState().drafts).toEqual(draftB);
    expect(screen.getByLabelText("Title", { exact: true })).toHaveValue("Reopened owner check");
    expect(screen.getByLabelText("Mode")).toHaveValue("recurring");
    expect(screen.getByLabelText("Cron expression")).toHaveValue("15 10 * * 3");
    expect(screen.getByLabelText("Duration")).toHaveValue("120");
    expect(create).toHaveBeenCalledTimes(1);
  });

  it("does not acknowledge a reopened form even when its draft values are unchanged", async () => {
    render(<ScheduleCreateWindow />); recurring();
    const finishA = pendingCreate();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    act(() => useDesk.getState().openScheduleCreate());
    const draftB = { ...useDesk.getState().drafts };
    const windowB = useDesk.getState().scheduleCreateWindow;
    await finishA();
    expect(useDesk.getState().scheduleCreateWindow).toBe(windowB);
    expect(useDesk.getState().drafts).toEqual(draftB);
    expect(screen.getByLabelText("Title", { exact: true })).toHaveValue("Release owner check");
    expect(create).toHaveBeenCalledTimes(1);
  });

  it("reopens the same recurring operation and duration without creating a schedule", () => {
    const view = render(<ScheduleCreateWindow />); recurring();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(useDesk.getState().scheduleCreateWindow).toBeNull();
    act(() => useDesk.getState().openScheduleCreate());
    expect(screen.getByLabelText("Title", { exact: true })).toHaveValue("Release owner check");
    expect(screen.getByLabelText("Mode", { exact: true })).toHaveValue("recurring");
    expect(screen.getByLabelText("Cron expression", { exact: true })).toHaveValue("30 14 * * 2");
    expect(screen.getByLabelText("Duration", { exact: true })).toHaveValue("90");
    expect(create).not.toHaveBeenCalled(); view.unmount();
  });

  it("keeps all fields after refusal and clears them only after an accepted save", async () => {
    create.mockResolvedValueOnce(false).mockResolvedValueOnce(true);
    render(<ScheduleCreateWindow />); recurring();
    fireEvent.click(screen.getByTestId("schedule-create-submit"));
    const refusal = await screen.findByRole("alert");
    expect(refusal.textContent).toBe("Not saved · Kept");
    expect(refusal.closest(".surface-footer-receipt")).toBeTruthy();
    expect(screen.getByLabelText("Mode", { exact: true })).toHaveValue("recurring");
    expect(screen.getByLabelText("Cron expression", { exact: true })).toHaveValue("30 14 * * 2");
    expect(screen.getByLabelText("Duration", { exact: true })).toHaveValue("90");
    fireEvent.click(screen.getByTestId("schedule-create-submit"));
    await waitFor(() => expect(useDesk.getState().scheduleCreateWindow).toBeNull());
    expect(create).toHaveBeenLastCalledWith(expect.objectContaining({ title: "Release owner check", one_shot: false, cron_expr: "30 14 * * 2", duration_minutes: 90 }));
    expect(Object.keys(useDesk.getState().drafts).filter((key) => key.startsWith("schedule/new/"))).toEqual([]);
  });

  it("keeps an emptied cron empty across a close", () => {
    render(<ScheduleCreateWindow />); recurring();
    fireEvent.change(screen.getByLabelText("Cron expression"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    act(() => useDesk.getState().openScheduleCreate());
    expect(screen.getByLabelText("Cron expression")).toHaveValue("");
    expect(create).not.toHaveBeenCalled();
  });
});
