import { Link } from "react-router-dom";
import { workroomHref } from "../workrooms/context";
import { PageHero } from "./pageSupport";

const TOOLS = [
  ["/workbench", "Workflow editor", "Build or edit a Workflow.", "configure"],
  [
    "/companion",
    "Personas and coders",
    "Review Personas and waiting Coder sessions.",
    "inspect",
  ],
  ["/cadence", "Cadence", "Configure scheduled background work.", "configure"],
  [
    "/commands",
    "Commands",
    "Map spoken phrases to registered actions.",
    "configure",
  ],
  [
    "/profiles",
    "Runs on",
    "Configure model and runtime destinations.",
    "configure",
  ],
  [
    "/activity",
    "Activity",
    "Inspect work context, sources, rules, and records.",
    "inspect",
  ],
] as const;
export default function StudioPage() {
  return (
    <div className="page-wrap">
      <PageHero eyebrow="Focused workspace" title="Studio">
        Build and configure reusable Desk tools.
      </PageHero>
      <div className="studio-grid">
        {TOOLS.map(([href, name, what, mode]) => (
          <Link
            className="studio-card"
            to={workroomHref(href, {
              action: `${mode}-${name
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/-$/g, "")}`,
            })}
            key={href}
          >
            <span aria-hidden="true">◇</span>
            <strong>{name}</strong>
            <p>{what}</p>
            <b>{mode === "inspect" ? "Open →" : "Configure →"}</b>
          </Link>
        ))}
      </div>
    </div>
  );
}
