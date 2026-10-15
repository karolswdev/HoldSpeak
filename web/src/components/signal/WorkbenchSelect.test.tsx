import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button, Select } from "./Signal";
import { CycleGadget } from "../../desk/surface/gadgets";

const choices = <><option value="en">English</option><option value="fr" disabled>French</option><option value="pl">Polish</option><option value="pt">Portuguese</option></>;
function list() { return screen.getByRole("listbox"); }
function option(name: string) { return within(list()).getByRole("option", { name }); }

describe("Workbench picker", () => {
  it("opens a library list with a pointer while the labelled native select owns the form", () => {
    render(<form aria-label="Preferences"><label htmlFor="language">Language</label><Select id="language" name="language" defaultValue="en" required>{choices}</Select></form>);
    const owner = screen.getByRole("combobox", { name: "Language" }) as HTMLSelectElement;
    expect(owner.tagName).toBe("SELECT");
    expect(fireEvent.pointerDown(owner, { button: 0 })).toBe(false);
    expect(owner).toHaveFocus();
    expect(owner).toHaveAttribute("aria-expanded", "true");
    expect(list().parentElement).toBe(document.body);
    expect(option("English")).toHaveAttribute("aria-selected", "true");
    expect(option("English")).toHaveClass("btn--chrome");
    expect(new FormData(screen.getByRole("form") as HTMLFormElement).get("language")).toBe("en");
    expect(owner).toBeRequired();
  });

  it("keeps active choice separate from saved choice and Escape cancels inside the window", () => {
    const changed = vi.fn(), windowKey = vi.fn();
    render(<div onKeyDown={windowKey}><Select aria-label="Language" value="en" onChange={changed}>{choices}</Select></div>);
    const owner = screen.getByRole("combobox");
    owner.focus();
    fireEvent.keyDown(owner, { key: "ArrowDown" });
    fireEvent.keyDown(owner, { key: "ArrowDown" });
    expect(option("Polish")).toHaveAttribute("data-active");
    expect(option("English")).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(owner, { key: "Escape" });
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(owner).toHaveValue("en");
    expect(owner).toHaveFocus();
    expect(changed).not.toHaveBeenCalled();
    expect(windowKey.mock.calls.some(([event]) => event.key === "Escape")).toBe(false);
  });

  it("commits one native input and change event with the new value and original owner", () => {
    const changed = vi.fn(), input = vi.fn();
    render(<Select aria-label="Language" defaultValue="en" onChange={(event) => changed(event.currentTarget, event.target.value)} onInput={input}>{choices}</Select>);
    const owner = screen.getByRole("combobox");
    fireEvent.click(owner);
    fireEvent.click(option("Polish"));
    expect(changed).toHaveBeenCalledExactlyOnceWith(owner, "pl");
    expect(input).toHaveBeenCalledTimes(1);
    expect(owner).toHaveValue("pl");
    expect(owner).toHaveFocus();
    expect(screen.queryByRole("listbox")).toBeNull();
    fireEvent.click(owner);
    fireEvent.click(option("Polish"));
    expect(changed).toHaveBeenCalledTimes(1);
  });

  it("preserves controlled values and keyboard Enter or Space commits only once", () => {
    const changed = vi.fn();
    render(<CycleGadget label="Language" value="en" options={[{value:"en",label:"English"},{value:"pl",label:"Polish"}]} onChange={changed}/>);
    const owner = screen.getByRole("combobox");
    fireEvent.keyDown(owner, { key: " " });
    fireEvent.keyDown(owner, { key: "End" });
    fireEvent.keyDown(owner, { key: "Enter" });
    expect(changed).toHaveBeenCalledExactlyOnceWith("pl");
    expect(owner).toHaveValue("en");
  });

  it("keeps missing values named and unavailable options cannot commit", () => {
    const changed = vi.fn();
    render(<CycleGadget label="Destination" value="Old archive" options={[{value:"ready",label:"Notes"},{value:"held",label:"External notes",disabled:true}]} onChange={changed}/>);
    fireEvent.click(screen.getByRole("combobox"));
    expect(option("Old archive")).toHaveAttribute("aria-selected", "true");
    expect(option("External notes")).toBeDisabled();
    fireEvent.click(option("External notes"));
    expect(changed).not.toHaveBeenCalled();
    expect(list()).toBeInTheDocument();
  });

  it("Home, End and typeahead skip unavailable choices without saving", () => {
    const changed = vi.fn();
    render(<Select aria-label="Language" value="en" onChange={changed}>{choices}</Select>);
    const owner = screen.getByRole("combobox");
    fireEvent.keyDown(owner, {key:"Enter"});
    fireEvent.keyDown(owner, {key:"End"});
    expect(option("Portuguese")).toHaveAttribute("data-active");
    fireEvent.keyDown(owner, {key:"Home"});
    expect(option("English")).toHaveAttribute("data-active");
    fireEvent.keyDown(owner, {key:"p"});
    expect(option("Polish")).toHaveAttribute("data-active");
    fireEvent.keyDown(owner, {key:"p"});
    expect(option("Portuguese")).toHaveAttribute("data-active");
    expect(changed).not.toHaveBeenCalled();
  });

  it("Tab exits to the next control and outside pointer preserves its action", async () => {
    const user = userEvent.setup(), next = vi.fn(), changed = vi.fn();
    render(<><Select aria-label="Language" defaultValue="en" onChange={changed}>{choices}</Select><Button onClick={next}>Next</Button></>);
    const owner = screen.getByRole("combobox");
    owner.focus();
    await user.keyboard("{Enter}{Tab}");
    expect(screen.getByRole("button", {name:"Next"})).toHaveFocus();
    expect(screen.queryByRole("listbox")).toBeNull();
    await user.click(owner);
    await user.click(screen.getByRole("button", {name:"Next"}));
    expect(next).toHaveBeenCalledTimes(1);
    expect(changed).not.toHaveBeenCalled();
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("closes on disable, unmount and ancestor scroll but keeps popup scrolling usable", () => {
    const view = (disabled = false) => <div data-testid="scroller"><Select aria-label="Language" defaultValue="en" disabled={disabled}>{choices}</Select></div>;
    const { rerender, unmount } = render(view());
    fireEvent.click(screen.getByRole("combobox"));
    fireEvent.scroll(list());
    expect(list()).toBeInTheDocument();
    fireEvent.scroll(screen.getByTestId("scroller"));
    expect(screen.queryByRole("listbox")).toBeNull();
    fireEvent.click(screen.getByRole("combobox"));
    rerender(view(true));
    expect(screen.queryByRole("listbox")).toBeNull();
    fireEvent.click(screen.getByRole("combobox"));
    expect(screen.queryByRole("listbox")).toBeNull();
    rerender(view());
    fireEvent.click(screen.getByRole("combobox"));
    unmount();
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("uses external form ownership, native default/reset and producer change events", () => {
    const changed = vi.fn();
    render(<><form id="preferences" aria-label="Preferences"/><Select aria-label="Language" form="preferences" name="lang" defaultValue="pl" onChange={changed}>{choices}</Select></>);
    const owner = screen.getByRole("combobox") as HTMLSelectElement;
    fireEvent.change(owner, {target:{value:"pt"}});
    expect(changed).toHaveBeenCalledTimes(1);
    expect(new FormData(screen.getByRole("form") as HTMLFormElement).get("lang")).toBe("pt");
    (screen.getByRole("form") as HTMLFormElement).reset();
    expect(owner).toHaveValue("pl");
    fireEvent.click(owner);
    expect(option("Polish")).toHaveAttribute("aria-selected", "true");
  });

  it("reads optgroups, uses option label and respects a disabled group", () => {
    render(<Select aria-label="Engine" defaultValue="local"><option value="local" label="On this Mac">Local internal</option><optgroup label="Remote" disabled><option value="cloud">Cloud</option></optgroup></Select>);
    fireEvent.click(screen.getByRole("combobox"));
    expect(option("On this Mac")).toHaveAttribute("aria-selected", "true");
    expect(option("Cloud")).toBeDisabled();
  });

  it("bounds the popup above an edge control and carries the owning theme through the portal", () => {
    render(<Select aria-label="Language" defaultValue="en" style={{"--wb-paper":"rgb(230, 232, 240)"} as React.CSSProperties}>{choices}</Select>);
    const owner = screen.getByRole("combobox");
    vi.spyOn(owner, "getBoundingClientRect").mockReturnValue({left:window.innerWidth-100,right:window.innerWidth-10,top:window.innerHeight-60,bottom:window.innerHeight-20,width:90,height:40,x:0,y:0,toJSON:()=>({})});
    fireEvent.click(owner);
    expect(list().style.bottom).toBe("64px");
    expect(Number.parseFloat(list().style.left) + Number.parseFloat(list().style.width)).toBeLessThanOrEqual(window.innerWidth-8);
    expect(Number.parseFloat(list().style.maxHeight)).toBeLessThanOrEqual(window.innerHeight-72);
    expect(list().style.getPropertyValue("--wb-paper")).toBe("rgb(230, 232, 240)");
  });

  it("closes a stale roster/value snapshot and a resize without saving", () => {
    const changed = vi.fn();
    const {rerender} = render(<Select aria-label="Language" value="en" onChange={changed}>{choices}</Select>);
    fireEvent.click(screen.getByRole("combobox"));
    rerender(<Select aria-label="Language" value="pl" onChange={changed}>{choices}</Select>);
    expect(screen.queryByRole("listbox")).toBeNull();
    fireEvent.click(screen.getByRole("combobox"));
    rerender(<Select aria-label="Language" value="pl" onChange={changed}>{choices}<option value="uk">Ukrainian</option></Select>);
    expect(screen.queryByRole("listbox")).toBeNull();
    fireEvent.click(screen.getByRole("combobox"));
    fireEvent(window, new Event("resize"));
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(changed).not.toHaveBeenCalled();
  });

  it("retains the open popup and active choice when a parent recreates the same logical options", () => {
    const changed = vi.fn();
    const view = () => <CycleGadget label="Language" value="en" options={[{value:"en",label:"English"},{value:"pl",label:"Polish"}]} onChange={changed}/>;
    const {rerender} = render(view());
    const owner = screen.getByRole("combobox");
    fireEvent.keyDown(owner, {key:"Enter"});
    fireEvent.keyDown(owner, {key:"ArrowDown"});
    expect(option("Polish")).toHaveAttribute("data-active");
    rerender(view());
    expect(option("Polish")).toHaveAttribute("data-active");
    expect(option("English")).toHaveAttribute("aria-selected", "true");
    expect(changed).not.toHaveBeenCalled();
  });
});
