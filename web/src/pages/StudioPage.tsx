import { Link } from "react-router-dom";
import { workroomHref } from "../workrooms/context";
import { PageHero } from "./pageSupport";

const TOOLS = [
  ["/workbench", "Workflow editor", "Build or edit a Workflow."],
  [
    "/companion",
    "Personas and coders",
    "Configure Personas and inspect Coder sessions.",
  ],
  ["/cadence", "Cadence", "Configure scheduled background work."],
  ["/commands", "Commands", "Map spoken phrases to registered actions."],
  ["/profiles", "Runs on", "Configure model and runtime destinations."],
  [
    "/activity",
    "Activity",
    "Inspect work context, sources, rules, and records.",
  ],
] as const;
export default function StudioPage() {
  return (
    <div className="page-wrap">
      <PageHero eyebrow="Focused workspace" title="Studio">
        Build and configure reusable Desk tools.
      </PageHero>
      <div className="studio-grid">
        {TOOLS.map(([href, name, what]) => (
          <Link
            className="studio-card"
            to={workroomHref(href, {
              action: `configure-${name
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/-$/g, "")}`,
            })}
            key={href}
          >
            <span aria-hidden="true">◇</span>
            <strong>{name}</strong>
            <p>{what}</p>
            <b>Configure →</b>
          </Link>
        ))}
      </div>
    </div>
  );
}
