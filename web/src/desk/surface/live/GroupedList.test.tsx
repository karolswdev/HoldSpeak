import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ListView } from "../index";
afterEach(cleanup);
it("groups rows without making captions selectable or changing click and Return", () => {
  render(<ListView label="Programs" headerless ordered groups={[{id:0,label:"Needs you"},{id:1,label:"Running"}]} columns={[{key:"name",word:"Program"}]}
    rows={[{id:"a",kind:"program",name:"Overnight",group:0,detail:"Step 1 of 4 · Waits on you",leadingLamp:{state:"waiting",label:"Waits on you"},meter:{current:0,total:4,state:"waiting"}},
      {id:"b",kind:"program",name:"Calls",group:1,detail:"Step 3 of 6 · Codex works"}]} />);
  const first=within(screen.getByRole('rowgroup',{name:"Needs you"})).getByRole('row');
  const second=within(screen.getByRole('rowgroup',{name:"Running"})).getByRole('row');
  expect(screen.getAllByRole('row')).toHaveLength(2);
  expect(screen.getByText('Needs you')).not.toHaveAttribute('tabindex');
  expect(within(first).getByText('Step 1 of 4 · Waits on you')).toBeVisible();
  expect(within(first).getByRole('img',{name:'Step 1 of 4'})).toBeInTheDocument();
  first.focus();fireEvent.keyDown(first,{key:"ArrowDown"});expect(second).toHaveFocus();expect(second).toHaveAttribute('aria-selected','true');
  fireEvent.keyDown(second,{key:'ArrowUp'});expect(first).toHaveFocus();
});
it("does not lose rows without a declared group and omits empty groups", () => {
  render(<ListView label="Programs" headerless groups={[{id:0,label:"Empty"}]} rows={[{id:'a',kind:'program',name:'Kept',group:5}]} />);
  expect(screen.getByRole('row')).toHaveTextContent('Kept');expect(screen.queryByText('Empty')).toBeNull();
});
