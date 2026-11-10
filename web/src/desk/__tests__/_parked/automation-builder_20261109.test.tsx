// Parked: the five-step wizard is replaced by the same editable sentence.
function blankBuilderDetail(): AutomationDetail {
  const detail = ((fridayNew as Step).gets[DETAIL_OF(fridayNew)] as { workbench: unknown }).workbench;
  return {
    ...(detail as AutomationDetail),
    instruction: "",
    instruction_shown: "",
    results: [],
    items: [],
  };
}

function renderBuilder(
  overrides: Partial<ComponentProps<typeof AutomationBuilder>> = {},
) {
  const callbacks = {
    onSaveDo: vi.fn(async () => true),
    onSaveSources: vi.fn(async () => true),
    onChooseEngine: vi.fn(async () => true),
    onSpendLimit: vi.fn(async () => true),
    onChooseWhen: vi.fn(async () => true),
    onChoosePut: vi.fn(async () => true),
    onChooseReview: vi.fn(async () => true),
    onPending: vi.fn(),
    onDone: vi.fn(),
  };
  render(
    <AutomationBuilder
      detail={blankBuilderDetail()}
      pending={false}
      whenSaving={null}
      saveError={null}
      {...callbacks}
      {...overrides}
    />,
  );
  return callbacks;
}

describe("the guided automation setup", () => {
  it("cannot skip an empty Do through the step rail and finish setup", () => {
    const callbacks = renderBuilder();
    const put = screen.getByTestId("automation-setup-step-put");
    expect(put).toBeDisabled();
    fireEvent.click(put);
    expect(screen.getByTestId("automation-setup-do")).toBeInTheDocument();
    expect(screen.queryByTestId("automation-setup-done")).toBeNull();
    expect(callbacks.onDone).not.toHaveBeenCalled();
    expect(callbacks.onSaveDo).not.toHaveBeenCalled();
  });

  it("keeps a Do draft when Back returns from About", async () => {
    const callbacks = renderBuilder();
    const box = screen.getByRole("textbox", { name: "What it does" });
    fireEvent.change(box, { target: { value: "Keep this draft" } });
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await screen.findByTestId("automation-setup-about");
    expect(callbacks.onSaveDo).toHaveBeenCalledWith("run", "Keep this draft");
    fireEvent.click(screen.getByTestId("automation-setup-back"));
    expect(screen.getByRole("textbox", { name: "What it does" })).toHaveValue("Keep this draft");
  });

  it("stays on Do and keeps the draft when its save fails", async () => {
    const onSaveDo = vi.fn(async () => false);
    renderBuilder({ onSaveDo });
    const box = screen.getByRole("textbox", { name: "What it does" });
    fireEvent.change(box, { target: { value: "Do not lose this" } });
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await waitFor(() => expect(onSaveDo).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId("automation-setup-about")).toBeNull();
    expect(screen.getByRole("textbox", { name: "What it does" })).toHaveValue("Do not lose this");
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await waitFor(() => expect(onSaveDo).toHaveBeenCalledTimes(2));
  });

  it("does not run while Next advances through setup or when Done returns", async () => {
    const onDone = vi.fn();
    renderBuilder({ onDone });
    fireEvent.change(screen.getByRole("textbox", { name: "What it does" }), { target: { value: "Prepare it" } });
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await screen.findByTestId("automation-setup-about");
    for (const step of ["with", "when", "put"] as const) {
      fireEvent.click(screen.getByTestId("automation-setup-next"));
      await screen.findByTestId(`automation-setup-${step}`);
    }
    fireEvent.click(screen.getByTestId("automation-setup-done"));
    expect(onDone).toHaveBeenCalledTimes(1);
  });
});

  it("the guided Do step offers Run a program and needs a template before Next", async () => {
    const callbacks = renderBuilder();
    fireEvent.click(screen.getByTestId("automation-do-run-program"));
    fireEvent.change(screen.getByRole("textbox", { name: "Goal" }), { target: { value: "Clear the bug list." } });
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    expect(await screen.findByText("Choose a template before Next.")).toBeInTheDocument();
    expect(callbacks.onSaveDo).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("automation-program-template-race"));
    fireEvent.click(screen.getByTestId("automation-program-control-secure"));
    fireEvent.click(screen.getByTestId("automation-setup-next"));
    await waitFor(() => expect(callbacks.onSaveDo).toHaveBeenCalledWith(
      "run_program", "Clear the bug list.", { template: "race", control: "secure", runsOn: [] }));
    expect(await screen.findByTestId("automation-setup-about")).toBeInTheDocument();
  });