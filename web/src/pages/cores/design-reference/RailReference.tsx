import { useState } from "react";
import { Mast, Rail, Spine } from "../../../desk/surface";

/** Local selection only: the same list, mast and spine used by native apps. */
export function RailReference() {
  const [picked, setPicked] = useState("review");
  return <section className="reference-navigation-sample surface-rail-layout" aria-label="Rail pattern" data-testid="reference-rail">
    <Rail label="Work" picked={picked} onPick={setPicked} groups={[
      { id: "active", label: "In progress", items: [
        { id: "review", label: "Release review", facts: "Today", state: "Waits on you", count: 2, spine: { tone: "brass" } },
        { id: "sources", label: "Read the sources", state: "Running", count: 0, spine: { tone: "steel" } },
      ] },
      { id: "done", label: "Done", items: [{ id: "decision", label: "Release decision", state: "Filed", spine: { tone: "moss" } }] },
    ]} />
    <div className="reference-navigation-pane">
      <Mast kind="program" title={picked === "review" ? "Release review" : picked === "sources" ? "Read the sources" : "Release decision"} />
      <Spine tone={picked === "review" ? "brass" : picked === "sources" ? "steel" : "moss"} />
    </div>
  </section>;
}
