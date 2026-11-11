import { useState } from "react";
import { fireEvent, render, screen, within, cleanup } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { CycleGadget, SegmentedTabs } from "../index";

afterEach(()=>{cleanup();vi.restoreAllMocks();});
it("fits whole tabs, keeps the selected tab shown and opens hidden panes through More",()=>{
  vi.spyOn(HTMLElement.prototype,"getBoundingClientRect").mockImplementation(function(this:HTMLElement){
    const width=this.classList.contains("surface-segmented-tabs")?250:this.tagName === "BUTTON"?100:250;
    return {width,height:44,left:0,right:width,top:0,bottom:44} as DOMRect;
  });
  function Host(){const [value,setValue]=useState("gate");return <SegmentedTabs label="Records" value={value} onChange={setValue} tabs={[{id:"step",label:"Step"},{id:"requirements",label:"Requirements"},{id:"gate",label:"Gate"},{id:"rounds",label:"Rounds"}]}><p>{value} content</p></SegmentedTabs>;}
  render(<Host/>);
  const strip=screen.getByRole("tablist",{name:"Records"});
  expect(within(strip).getAllByRole("tab").map(tab=>tab.textContent)).toEqual(["Gate"]);
  expect(screen.getByRole("tab",{name:"Gate"})).toHaveAttribute("aria-selected","true");
  fireEvent.click(screen.getByRole("button",{name:"Records more"}));
  fireEvent.click(screen.getByRole("menuitem",{name:"Requirements"}));
  expect(screen.getByRole("tabpanel")).toHaveTextContent("requirements content");
  expect(screen.getByRole("tab",{name:"Requirements"})).toHaveAttribute("aria-selected","true");
  fireEvent.keyDown(screen.getByRole("tab",{name:"Requirements"}),{key:"End"});
  expect(screen.getByRole("tab",{name:"Rounds"})).toHaveFocus();
  expect(strip.scrollLeft).toBe(0);
});

it("cycles fixed words and opens a pop-up for a roster or more than three choices",()=>{
  const change=vi.fn(), words=["Secure","Normal","YOLO"].map(value=>({value}));
  const view=render(<CycleGadget label="Control" value="Secure" options={words} onChange={change}/>);
  fireEvent.click(screen.getByRole("combobox",{name:"Control"}));
  expect(change).toHaveBeenCalledWith("Normal");
  view.rerender(<CycleGadget roster label="Project" value="Secure" options={words} onChange={change}/>);
  fireEvent.click(screen.getByRole("combobox",{name:"Project"}));
  expect(screen.getByRole("listbox")).toBeTruthy();
  fireEvent.keyDown(screen.getByRole("listbox"),{key:"Escape"});
  view.rerender(<CycleGadget label="Review depth" value="Secure" options={[...words,{value:"Deep"}]} onChange={change}/>);
  expect(view.container.querySelector('[data-cycle]')).toBeNull();
});
