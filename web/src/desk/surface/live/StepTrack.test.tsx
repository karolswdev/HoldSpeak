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
  expect(css).toContain('container: step-track / inline-size');expect(css).toContain('overflow-x: auto');
  expect(css).toMatch(/prefers-reduced-motion: reduce[\s\S]*display: none !important/);
});

it("scrolls only its own strip when the current station is outside the view", () => {
  const {rerender}=render(<StepTrack steps={steps} current="a" onSelect={()=>{}} label="Steps" />);
  const strip=screen.getByRole("tablist");
  vi.spyOn(strip,"getBoundingClientRect").mockReturnValue({left:0,right:100,width:100} as DOMRect);
  vi.spyOn(screen.getAllByRole("tab")[2],"getBoundingClientRect").mockReturnValue({left:200,right:288,width:88} as DOMRect);
  rerender(<StepTrack steps={steps} current="c" onSelect={()=>{}} label="Steps" />);
  expect(strip.scrollLeft).toBe(188);expect(strip.scrollTop).toBe(0);
  vi.restoreAllMocks();
});

it("does not queue a tick when the owner requests reduced motion", () => {
  const media=vi.spyOn(window,"matchMedia").mockReturnValue({matches:true} as MediaQueryList);
  const {rerender}=render(<StepTrack steps={steps} current="a" onSelect={()=>{}} label="Steps" />);
  rerender(<StepTrack steps={steps} current="b" onSelect={()=>{}} label="Steps" />);
  expect(screen.getAllByRole("tab").every(tab=>!tab.hasAttribute("data-ticked"))).toBe(true);
  media.mockRestore();
});
