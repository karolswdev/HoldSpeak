import { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { StepTrack, type TrackStep } from "../index";
import css from "./step-track.css?raw";
afterEach(cleanup);
const steps: TrackStep[] = [{id:"a",name:"Store the reason",state:"merged"},{id:"b",name:"Show the reason",state:"working"},{id:"c",name:"Write the recap",state:"planned"}];
it("selects with arrows and a press without moving the current work", () => {
  function Track() {const [selected,setSelected] = useState<string | null>("b"); return <StepTrack steps={steps} current="b" selected={selected} onSelect={setSelected} label="Steps" />;}
  render(<Track />);
  const tabs=screen.getAllByRole("tab"); tabs[1].focus();
  fireEvent.keyDown(tabs[1],{key:"ArrowRight"});
  expect(tabs[2]).toHaveFocus(); expect(tabs[2]).toHaveAttribute("aria-selected","true");
  expect(tabs[1]).toHaveAttribute("aria-current","step");
  fireEvent.keyDown(tabs[2],{key:"Home"});expect(tabs[0]).toHaveFocus();
  fireEvent.keyDown(tabs[0],{key:"End"});expect(tabs[2]).toHaveFocus();
  fireEvent.click(tabs[0]); expect(tabs[0]).toHaveAttribute("aria-selected","true");
});
it.each(["working","waiting","parked","done","planned","limited","checking","findings","merge_ask","failed"])("accepts the producer state %s", state => {
  render(<StepTrack steps={[{id:"one",name:"Check",state}]} current="one" onSelect={()=>{}} label="Step" />);
  expect(screen.getByRole("tab")).toHaveAttribute("aria-current","step");
});
it("ticks the passed station once on forward movement and keeps current in its strip", () => {

  const {rerender}=render(<StepTrack steps={steps} current="b" onSelect={()=>{}} label="Steps" />);
  const next=steps.map(s=>({...s,state:s.id==="b"?"done":s.state}));
  rerender(<StepTrack steps={next} current="c" onSelect={()=>{}} label="Steps" />);
  expect(screen.getAllByRole("tab")[1]).toHaveAttribute("data-ticked","true");
  fireEvent.animationEnd(screen.getAllByRole("tab")[1].firstElementChild!);
  expect(screen.getAllByRole("tab")[1]).not.toHaveAttribute("data-ticked");
  const strip=screen.getByRole("tablist");
  expect(strip.scrollTop).toBe(0);
  rerender(<StepTrack steps={next} current="b" onSelect={()=>{}} label="Steps" />);
  expect(screen.getAllByRole("tab").every(tab=>!tab.hasAttribute("data-ticked"))).toBe(true);
});
it("keeps narrow names whole below a bounded strip and removes reduced-motion travel", () => {
  expect(css).toContain('container: step-track / inline-size');expect(css).toContain('overflow: hidden');
  expect(css).toMatch(/prefers-reduced-motion: reduce[\s\S]*display: none !important/);
});

it("condenses every station to keep a long track in its seat", () => {
  const measure=vi.spyOn(HTMLElement.prototype,"getBoundingClientRect").mockReturnValue({left:0,right:393,width:393,height:24} as DOMRect);
  const longSteps=Array.from({length:12},(_,i)=>({id:String(i),name:`A complete step name ${i}`,state:i===5?"working":"planned"}));
  render(<StepTrack steps={longSteps} current="5" onSelect={()=>{}} label="Long track" />);
  expect(screen.getByRole("tablist").parentElement).toHaveAttribute("data-condensed","true");
  const visible = screen.getAllByRole("tab");
  expect(visible.length).toBeLessThan(longSteps.length);
  expect(visible.find(tab=>tab.getAttribute("aria-current") === "step")).toBeDefined();
  fireEvent.click(screen.getByRole("button", {name:"More ▾"}));
  expect(screen.getAllByRole("menuitem").length + visible.length).toBe(longSteps.length);
  expect(screen.getByRole("tablist").scrollLeft).toBe(0);
  measure.mockRestore();
});
it("colours a link only when its source is done and its destination is done or current",()=>{
  render(<StepTrack steps={[{id:"a",name:"Done",state:"done"},{id:"b",name:"Open",state:"planned"},{id:"c",name:"Waiting",state:"waiting"}]} current="c" onSelect={()=>{}} label="States"/>);
  expect(screen.getAllByRole("tab").every(tab=>!tab.hasAttribute("data-complete"))).toBe(true);
});

it("does not queue a tick when the owner requests reduced motion", () => {
  const media=vi.spyOn(window,"matchMedia").mockReturnValue({matches:true} as MediaQueryList);
  const {rerender}=render(<StepTrack steps={steps} current="a" onSelect={()=>{}} label="Steps" />);
  rerender(<StepTrack steps={steps} current="b" onSelect={()=>{}} label="Steps" />);
  expect(screen.getAllByRole("tab").every(tab=>!tab.hasAttribute("data-ticked"))).toBe(true);
  media.mockRestore();
});

it("reaches a hidden step from More and keeps keyboard selection in the strip", () => {
  const measure=vi.spyOn(HTMLElement.prototype,"getBoundingClientRect").mockReturnValue({left:0,right:393,width:393,height:44} as DOMRect);
  const longSteps=Array.from({length:12},(_,i)=>({id:String(i),name:`Work ${i+1}`,state:i===5?"working":"planned"}));
  function Track() { const [selected,setSelected]=useState("5"); return <StepTrack steps={longSteps} current="5" selected={selected} onSelect={setSelected} label="Long steps"/>; }
  render(<Track/>);
  fireEvent.click(screen.getByRole("button",{name:"More ▾"}));
  fireEvent.click(screen.getByRole("menuitem",{name:"Step 12: Work 12"}));
  const last=screen.getByRole("tab",{name:/Step 12:/});
  expect(last).toHaveAttribute("aria-selected","true");
  fireEvent.keyDown(last,{key:"Home"});
  expect(screen.getByRole("tab",{name:/Step 1:/})).toHaveFocus();
  expect(screen.getByRole("tablist").scrollLeft).toBe(0);
  measure.mockRestore();
});
