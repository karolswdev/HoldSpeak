// Parked 2026-11-08 with #2006: these two cases drive a Workflow capability (kind "workflow"), a parked kind; only a Mode (kind "recipe") has the capability section now. Moved as text, not collected.

  it("runs the same capability once while busy and keeps the artifact and assignment actions", async () => {
    let finish: (result: unknown) => void = () => {};
    const runCapability = vi.fn(() => new Promise((resolve) => { finish = resolve; }));
    const openPullout = vi.fn();
    useDesk.setState({ runCapability: runCapability as never, openPullout });
    render(<CapabilitySection object={{ kind: "workflow", id: "flow-1", title: "Review", ref: { capability: {
      readiness: { state: "ready" }, input_schema: { required: ["input"] }, effect_classes: ["creates_artifact"], supported_placements: ["this_machine"],
    } } } as never} />);
    fireEvent.change(screen.getByLabelText("Run Review"), { target: { value: "Release notes" } });
    const run = screen.getByRole("button", { name: "Run" });
    expect(run).toHaveClass("btn", "btn--primary");
    fireEvent.click(run);
    expect(screen.getByRole("button", { name: "Running…" })).toBeDisabled();
    expect(runCapability).toHaveBeenCalledOnce();
    expect(runCapability).toHaveBeenCalledWith("workflow", "flow-1", "Release notes");
    await act(async () => { finish({ output: "Kept review", warning: "", state: "complete", artifactId: "artifact-1", invocationId: "invoke-1", actualPlacement: null }); });
    expect(await screen.findByText("Kept review")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open kept Artifact" }));
    expect(openPullout).toHaveBeenCalledWith("artifact-1");
    await waitFor(() => expect(screen.getByRole("button", { name: "Run" })).not.toBeDisabled());
    // W2-BUILDER: where it runs is the Run's hover title (A.9); the engine
    // verb is the window toolbar's Choose engine (openCapabilityEngines).
    expect(screen.getByRole("button", { name: "Run" })).toHaveAttribute("title", "Works on this machine, keeps the result");
    expect(screen.queryByText(/Where it runs/)).toBeNull();
    openCapabilityEngines({ kind: "workflow", id: "flow-1", title: "Review" } as never);
    expect(openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/profiles", "workflow:flow-1");
  });

  it("keeps selected paragraphs and newer edits when a late voice result fills capability material", async () => {
    const scope = "capability:workflow:flow-paragraphs";
    const workflow = { kind: "workflow", id: "flow-paragraphs", name: "Review", capability: {
      readiness: { state: "ready" }, input_schema: { required: ["input"] }, effect_classes: ["creates_artifact"], supported_placements: ["this_machine"],
    } };
    const runCapability = vi.fn(async () => ({ output: "Kept paragraph review", warning: "", state: "complete", artifactId: null, invocationId: null, actualPlacement: null }));
    useDesk.setState({ items: { ...EMPTY_ITEMS,
      note: [{ kind: "note", id: "architecture", title: "Architecture", bodyMarkdown: "First paragraph.\n\nSecond paragraph." }],
      workflow: [workflow],
    } as never, selectedIds: ["note:architecture"], runCapability: runCapability as never });
    const object = { kind: "workflow", id: workflow.id, title: workflow.name, ref: workflow } as never;
    const view = render(<CapabilitySection object={object}/>);
    const material = screen.getByRole("textbox", { name: "Run Review on Architecture" });
    expect(material.tagName).toBe("TEXTAREA");
    expect(material).toHaveValue("## Architecture\nFirst paragraph.\n\nSecond paragraph.");
    expect(screen.getAllByTestId("field-mic").filter((mic) => mic.getAttribute("data-draft-scope") === scope)).toHaveLength(1);
    // Hold the callback from before the edit, as an in-flight capture does.
    const lateVoice = micCallbacks.get(scope)!;
    const edited = "## Architecture\nEdited first paragraph.\n\nSecond paragraph stays.";
    fireEvent.change(material, { target: { value: edited } });
    act(() => lateVoice("New spoken clause."));
    const expected = `${edited} New spoken clause.`;
    expect(material).toHaveValue(expected);
    expect(readDurableDraft(scope)?.text).toBe(expected);
    fireEvent.click(screen.getByRole("button", { name: "Run" }));
    expect(await screen.findByText("Kept paragraph review")).toBeTruthy();
    expect(runCapability).toHaveBeenCalledWith("workflow", workflow.id, expected);
    view.unmount();
    render(<CapabilitySection object={object}/>);
    expect(screen.getByRole("textbox", { name: "Run Review on Architecture" })).toHaveValue(expected);
    expect(screen.getByText("Recovered local run material.")).toBeTruthy();
  });
