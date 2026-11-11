import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { LiveReference } from "./LiveReference";
afterEach(()=>{cleanup();vi.useRealTimers();});
it("moves a waiting example into work with the same track, lamp, screen and clock", () => {
  render(<LiveReference preset="waiting" />);
  fireEvent.click(screen.getByRole('button',{name:'Go on'}));
  expect(screen.getByRole('tab',{name:/Step 2: Show the reason.*In work/})).toHaveAttribute('aria-current','step');
  expect(screen.getByRole('log',{name:'Agent screen'})).toHaveAttribute('data-working','true');
  expect(screen.getByText('0:00')).toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'Go on'})).toBeNull();
});
it("parks the selected local example and keeps other rows in work", () => {
  render(<LiveReference preset="working" />);
  const calls=screen.getByText('Calls on the home box').closest<HTMLElement>('[role=row]')!;
  fireEvent.click(calls);
  fireEvent.click(screen.getByRole('button',{name:'Park'}));
  const parked=screen.getByText('Calls on the home box').closest<HTMLElement>('[role=row]')!;
  expect(parked).toHaveTextContent('Parked at step 3');
  expect(within(parked).getByRole('img',{name:'parked'})).toHaveAttribute('data-state','off');
  expect(screen.getByText('Overnight on the home box').closest('[role=row]')).toHaveTextContent('Claude Code works');
});
it("the finished recap has no live screen or elapsed timer", () => {
  vi.useFakeTimers();render(<LiveReference preset="done" />);
  expect(screen.getByText('questions to you')).toBeInTheDocument();
  expect(screen.queryByRole('log')).toBeNull();expect(vi.getTimerCount()).toBe(0);
});
