// Parked: rail/card assertions are replaced by automations-list.app.test.tsx.
/* ── A7: home, New automation, and starters ─────────────────────────────
 * The hub's answers from test_a_starter_makes_one_automation_and_the_friday
 * _walk_reads_a_result: the starters and an empty desk, then the Friday team
 * update as made, with Claude Code, and after Run now. A step keeps the
 * starters' reads (the hub still answers them). */
const withStarters = (step: unknown): Step => ({
  workbench_id: (step as Step).workbench_id,
  gets: { ...(starters as Step).gets, ...(step as Step).gets },
});

function Desk() {
  const windows = useDesk((state) => state.workbenchWindows);
  return (
    <>
      <AutomationsCore />
      {windows.map((w) => <AutomationWindow key={w.id} workbenchId={w.id} />)}
    </>
  );
}

describe("A7: home, New automation and starters", () => {
  beforeEach(() => {
    // The desk's lists re-read after a create; this test reads the hub's own
    // automation answers only.
    useDesk.setState({ workbenchWindows: [], refresh: vi.fn(async () => undefined) });
  });

  it("DESIGN §6: New → Friday team update → With → Claude Code → Run now reads a result in 5 presses, in the one app window", async () => {
    hub.step = withStarters({ workbench_id: "", gets: {} });
    hub.detect = [detectOf("found"), detectOf("add")];
    render(<Desk />);
    // The empty app: the automation object, the one line, and the starters
    // as pictogram cards in the same window.
    expect(await screen.findByText("An automation does one job for you, again and again.")).toBeInTheDocument();
    expect(await within(screen.getByTestId("automation-home-empty")).findByTestId("automation-starter-friday-team-update")).toBeInTheDocument();
    const object = screen.getByTestId("automation-home-empty").querySelector('.surface-state[data-object="automation"]') as HTMLElement;
    expect(object.querySelector(".surface-state-sprite")?.getAttribute("src")).toMatch(/cartridge\.png$/);
    let presses = 0;

    // New automation keeps the starters in the pane (no second window).
    fireEvent.click(screen.getByTestId("automation-new")); presses += 1;
    const chooser = screen.getByTestId("automation-home-empty");
    const friday = await within(chooser).findByTestId("automation-starter-friday-team-update");
    expect(friday).toHaveAccessibleName("Friday team update");
    const describedBy = friday.getAttribute("aria-describedby");
    expect(describedBy).toBeTruthy();
    const matchingDescriptions = [...document.querySelectorAll<HTMLElement>("[id]")]
      .filter((element) => element.id === describedBy);
    expect(matchingDescriptions).toHaveLength(1);
    expect(chooser.contains(matchingDescriptions[0])).toBe(true);
    // The starter reads in words: never cron, never "Agent".
    expect(friday).toHaveTextContent("Every Friday at 15:00 · My Inbox");
    expect(chooser.textContent).not.toMatch(/\* \* \*|0 15|Agent|TODO|Triage|Morning Brief/);
    // PG14: the rig's engine is one pi can run on, so the Overnight program
    // starter is offered too.
    expect(within(chooser).getAllByRole("button").filter((b) => b.className.includes("automation-starter"))).toHaveLength(7);
    expect(within(chooser).getByTestId("automation-starter-overnight-program")).toHaveTextContent("Every weekday at 23:30");

    hub.afterCreate = [withStarters(fridayNew)];
    fireEvent.click(friday); presses += 1;
    await screen.findByTestId("automation-sentence");
    expect(line("when")).toHaveTextContent("Every Friday at 15:00");
    expect(line("about")).toHaveTextContent("This week's meetings");
    expect(line("about")).toHaveTextContent("This week's notes");
    expect(line("put")).toHaveTextContent("My Inbox");
    // A starter is not a recurring approval: its schedule waits for On.
    expect(within(screen.getByTestId("automation-on")).getByRole("checkbox")).not.toBeChecked();
    const windows = useDesk.getState().workbenchWindows.length;

    fireEvent.click(within(line("with")).getByRole("button")); presses += 1;
    const add = await within(await screen.findByTestId("automation-with-editor")).findByRole("button", { name: "Add Claude Code" });
    hub.afterEngine = [withStarters(fridayClaude)];
    fireEvent.click(add); presses += 1;
    await waitFor(() => expect(line("with")).toHaveTextContent("Claude Code"));

    hub.afterRun = [withStarters(fridayRan)];
    fireEvent.click(screen.getByTestId("automation-run-now")); presses += 1;
    const reading = await waitFor(() => within(newest()).getByTestId("automation-reading"));
    expect(within(reading).getByRole("heading", { name: "Weekly update" })).toBeInTheDocument();
    expect(reading.textContent).not.toMatch(/##|\*\*/);
    expect(presses).toBeLessThanOrEqual(6);
    expect(useDesk.getState().workbenchWindows.length).toBe(windows);
  });

  it("the rail: each automation its name, the spine of its runs and when it runs; a press shows it in the pane", async () => {
    // The list answer and the same automation's detail after its run.
    hub.step = { workbench_id: (homeRows as Step).workbench_id, gets: { ...(fridayRan as Step).gets, ...(homeRows as Step).gets } };
    render(<AutomationsCore />);
    const [item] = await screen.findAllByTestId("automation-rail-item");
    expect(item).toHaveTextContent("Friday team update");
    expect(item).toHaveTextContent("Every Friday at 15:00 · Off");
    // A result not opened yet is the brass dot and the status bar's `1 new`.
    expect(within(item).getByText("New")).toBeInTheDocument();
    expect(item.textContent).not.toMatch(/0 NEW|ITEM|PENDING|RECENT RUNS/);
    // The status bar says the count and what is new, never a zero.
    expect(screen.getByTestId("automation-home-count")).toHaveTextContent("1 automation");
    expect(screen.getByTestId("automation-home-status")).toHaveTextContent("1 new");
    expect(screen.getByTestId("automation-home-status").textContent).not.toMatch(/\b0\b/);
    // The first automation is chosen: its mast and plate are in the pane, in
    // this one window.
    expect(item).toHaveAttribute("aria-current", "true");
    fireEvent.click(item);
    expect(await within(screen.getByTestId("automations-pane")).findByTestId("automation-mast")).toHaveTextContent("Friday team update");
    expect(useDesk.getState().workbenchWindows).toEqual([]);
    expect(useDesk.getState().places["automations/picked"]).toBe((homeRows as Step).workbench_id);
  });

  it("one press makes one automation; a failed press says so, keeps its choice, and a second press makes it", async () => {
    hub.step = withStarters({ workbench_id: "", gets: {} });
    render(<Desk />);
    const friday = await screen.findByTestId("automation-starter-friday-team-update");
    fireEvent.click(friday); // no recorded answer: the hub call fails
    expect(await screen.findByRole("alert")).toHaveTextContent("Friday team update was not made");
    expect(friday).toHaveAttribute("aria-pressed", "true");
    expect(friday).toBeEnabled();
    expect(useDesk.getState().workbenchWindows).toEqual([]);
    hub.afterCreate = [withStarters(fridayNew)];
    fireEvent.click(friday);
    await screen.findByTestId("automation-sentence");
    // The failed press and the one that made it: one automation, shown in
    // the app's pane (no other window).
    expect(hub.calls.filter((c) => c.url.endsWith("/instantiate"))).toHaveLength(2);
    expect(useDesk.getState().workbenchWindows).toEqual([]);
    expect(useDesk.getState().places["automations/picked"]).toBe((fridayNew as Step).workbench_id);
  });

  it("a starter with a blank shows it highlighted until he fills it", async () => {
    hub.step = withStarters({ workbench_id: "", gets: {} });
    render(<AutomationsCore />);
    const prep = await screen.findByTestId("automation-starter-one-on-one-prep");
    expect(prep).toHaveTextContent("About: which people?");
    expect(screen.getByTestId("automation-starter-meeting-follow-ups")).toHaveTextContent("Only when I press Run now · Needs you");
  });
});
