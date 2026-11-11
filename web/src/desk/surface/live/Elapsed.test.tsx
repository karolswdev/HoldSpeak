import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { Elapsed } from "../index";
afterEach(()=>{cleanup();vi.useRealTimers();vi.restoreAllMocks();vi.unstubAllGlobals();});
it("ticks all rows from one timer and removes it when the final row unmounts", () => {
  vi.useFakeTimers();vi.setSystemTime(new Date('2026-11-10T10:00:00Z'));
  const start=Date.now();
  const {rerender,unmount}=render(<><Elapsed start={start}/><Elapsed start={start - 1000}/></>);
  expect(vi.getTimerCount()).toBe(1);
  act(()=>vi.advanceTimersByTime(3000)); expect(screen.getByText("0:03")).toBeInTheDocument();expect(screen.getByText("0:04")).toBeInTheDocument();
  rerender(<Elapsed start={start}/>);expect(vi.getTimerCount()).toBe(1);
  unmount();expect(vi.getTimerCount()).toBe(0);
});
it("stops while the tab or its piece is hidden and catches up on return", () => {
  vi.useFakeTimers();vi.setSystemTime(100000);
  const hidden=vi.spyOn(document,'hidden','get').mockReturnValue(false);
  const {rerender}=render(<Elapsed start={100000}/>);
  hidden.mockReturnValue(true);act(()=>document.dispatchEvent(new Event('visibilitychange')));
  expect(vi.getTimerCount()).toBe(0);
  act(()=>vi.advanceTimersByTime(4000));expect(screen.getByText("0:00")).toBeInTheDocument();
  hidden.mockReturnValue(false);act(()=>document.dispatchEvent(new Event('visibilitychange')));
  expect(screen.getByText("0:04")).toBeInTheDocument();expect(vi.getTimerCount()).toBe(1);
  rerender(<Elapsed start={100000} hidden/>);expect(vi.getTimerCount()).toBe(0);
});
it("stops an off-screen or CSS-hidden subscriber through visibility observation", () => {
  vi.useFakeTimers();let notify: IntersectionObserverCallback=()=>{};
  const disconnect=vi.fn();
  vi.stubGlobal('IntersectionObserver',class {constructor(callback:IntersectionObserverCallback){notify=callback;}observe(){}disconnect=disconnect;});
  const {container,unmount}=render(<Elapsed start={Date.now()}/>);
  act(()=>notify([{target:container.firstElementChild,isIntersecting:false}] as IntersectionObserverEntry[],{} as IntersectionObserver));
  expect(vi.getTimerCount()).toBe(0);unmount();expect(disconnect).toHaveBeenCalled();
});
it("shows an acknowledged end and treats invalid or future starts honestly", () => {
  vi.useFakeTimers();vi.setSystemTime(10000);
  const {rerender}=render(<Elapsed start={0} end={112000}/>);expect(screen.getByText("1:52")).toBeInTheDocument();expect(vi.getTimerCount()).toBe(0);
  rerender(<Elapsed start="bad" running={false}/>);expect(screen.getByText("—")).toBeInTheDocument();
  rerender(<Elapsed start={20000} running={false}/>);expect(screen.getByText("0:00")).toBeInTheDocument();
});
