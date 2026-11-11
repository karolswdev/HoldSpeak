import {
  act,
  fireEvent,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

/** Press the face's destination choice rather than the retired row chip. */
export async function chooseDestination(
  name: string,
  root: HTMLElement = document.body,
): Promise<HTMLElement> {
  const ui = within(root);
  if (!ui.queryByRole("combobox", { name: "Destination" }) || (ui.queryByRole("combobox", { name: "Destination" }) as HTMLSelectElement)?.disabled) {
    const tab = ui
      .queryAllByRole("tab")
      .find((t) => !["Prepared", "Sent"].includes(t.textContent ?? ""));
    if (tab) fireEvent.click(tab);
  }
  let select = await ui.findByRole("combobox", { name: "Destination" });
  const option = () => within(select).queryByRole("option", { name });
  if (!option()) {
    for (const tab of ui.queryAllByRole("tab")) {
      if (["Prepared", "Sent"].includes(tab.textContent ?? "")) continue;
      fireEvent.click(tab);
      select = await ui.findByRole("combobox", { name: "Destination" });
      if (option()) break;
    }
  }
  const chosen = option() as HTMLOptionElement | null;
  if (!chosen) throw new Error(`No saved destination ${name}`);
  await act(async () => {
    fireEvent.change(select, { target: { value: chosen.value } });
  });
  return await ui.findByTestId("send-well");
}

export async function clearDestination() {
  fireEvent.change(
    await screen.findByRole("combobox", { name: "Destination" }),
    { target: { value: "" } },
  );
  await waitFor(() => expect(screen.queryByTestId("send-open")).toBeNull());
}
