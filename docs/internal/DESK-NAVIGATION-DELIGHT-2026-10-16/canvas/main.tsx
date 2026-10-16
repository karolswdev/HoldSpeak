// Direction only: current production library and declared sample meetings.
import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import { Button } from "@w/components/signal/Signal";
import { StringGadget } from "@w/desk/surface/gadgets";
import { wireDayClock } from "@w/desk/surface/format";
import "./canvas.css";

const meetings = [
  { id: "release-review-platform", title: "Release review", startedAt: "2026-10-16T09:30:00", attendees: ["Mira Patel", "Jordan Lee"] },
  { id: "release-review-delivery", title: "Release review", startedAt: "2026-10-16T09:30:00", attendees: ["Alex Chen", "Sam Rivera"] },
];

function Direction() {
  const [query, setQuery] = useState("Release review");
  const [open, setOpen] = useState(true);
  return <RuntimeBusProvider><main className="desk-next direction-floor">
    {!open ? <Button onClick={() => setOpen(true)}>Search</Button> : <aside className="desk-tool-shelf" aria-label="Search direction">
      <div className="desk-tool-search-head">
        <label className="desk-tool-search">
          <StringGadget label="Search tools and Desk items" value={query} onChange={setQuery} placeholder="Search tools and Desk items" />
        </label>
        <Button dense variant="ghost" className="desk-tool-close" onClick={() => setOpen(false)}>Close</Button>
      </div>
      <ul className="desk-deck-list" role="listbox" aria-label="Sample meeting choices">
        {meetings.map((meeting, index) => <li key={`meeting:${meeting.id}`}>
          {index === 0 ? <span className="desk-deck-band">Meetings</span> : null}
          <Button variant="chrome" role="option" aria-selected={index === 0} data-wrap data-meeting className={`desk-deck-row${index === 0 ? " is-selected" : ""}`}>
            <span className="desk-deck-glyph" aria-hidden="true">▣</span>
            <span className="desk-deck-label">
              <span className="desk-deck-title">{meeting.title}</span>
              <span className="desk-deck-meeting-meta">{wireDayClock(meeting.startedAt)} · {meeting.attendees.join(", ")}</span>
            </span>
            <span className="desk-deck-kind">MEETING</span>
          </Button>
        </li>)}
      </ul>
    </aside>}
  </main></RuntimeBusProvider>;
}

createRoot(document.getElementById("root")!).render(<Direction />);
