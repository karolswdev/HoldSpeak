import { fireEvent, screen, within } from "@testing-library/react";

/** Press the reader's one action set, including its folded selection verbs. */
export async function meetingAction(label: string, press = true): Promise<HTMLElement> {
  let verb = screen.queryByRole("button", { name: label });
  if (!verb) {
    if (!screen.queryByRole("menuitem", {name:label})) fireEvent.click(within(screen.getByTestId("meeting-toolbar")).getByRole("button", {name:"Actions ▾"}));
    verb = await screen.findByRole("menuitem", {name:label});
  }
  if (press) fireEvent.click(verb);
  return verb;
}
