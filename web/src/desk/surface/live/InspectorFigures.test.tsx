import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { InspectorFigures, InspectorFacts, Lamp } from "../index";
afterEach(cleanup);
it("names every recap figure, including a meaningful zero", () => {
  render(<InspectorFigures label="Recap" figures={[{value:8,label:"steps done"},{value:0,label:"questions to you"},{value:"1 h 52 min",label:"from start to end"}]} />);
  expect(screen.getAllByRole("term").map(el=>el.textContent)).toEqual(["steps done","questions to you","from start to end"]);
  expect(screen.getAllByRole("definition").map(el=>el.textContent)).toEqual(["8","0","1 h 52 min"]);
});
it("uses the existing inspector head for its title and trailing live state", () => {
  render(<InspectorFacts name="Step 2 · Show the reason" trailing={<><Lamp state="working" label="In work"/>Claude Code works · 0:07</>} rows={[{label:"Then",value:"Recap"}]} />);
  const header=screen.getByText("Step 2 · Show the reason").closest(".surface-pane-inspector-head")!;
  expect(header.querySelector('.surface-inspector-trailing')).toHaveTextContent("Claude Code works · 0:07");
  expect(screen.getAllByText("Step 2 · Show the reason")).toHaveLength(1);
});

it("uses a singular question for one answer",()=>{
  render(<InspectorFigures label="Recap" figures={[{value:1,label:"questions to you"},{value:2,label:"steps done"}]}/>);
  expect(screen.getByText("question to you")).toBeTruthy();
});
