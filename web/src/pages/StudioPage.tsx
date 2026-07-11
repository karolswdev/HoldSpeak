import { Link } from "react-router-dom";
import { PageHero } from "./pageSupport";

const TOOLS = [
  [
    "/workbench",
    "Workbench",
    "Wire primitives into a runnable workflow on a node canvas.",
  ],
  ["/", "Desk", "Author meetings, notes, agents and more in a spatial world."],
  [
    "/companion",
    "Agent Desk",
    "See your recipes and the coding agents waiting on you.",
  ],
  [
    "/cadence",
    "Cadence",
    "A background chief-of-staff that pushes with receipts.",
  ],
  ["/commands", "Commands", "Map a spoken keyword to an explicit action."],
  [
    "/profiles",
    "Profiles",
    "Name model and runtime destinations without exposing keys.",
  ],
  [
    "/activity",
    "Activity",
    "Review local work context, sources, rules and records.",
  ],
] as const;
export default function StudioPage() {
  return (
    <div className="page-wrap">
      <PageHero eyebrow="Advanced" title="Studio">
        Power tools for when you want them. Optional; the two daily modes need
        none of this.
      </PageHero>
      <div className="studio-grid">
        {TOOLS.map(([href, name, what]) => (
          <Link className="studio-card" to={href} key={href}>
            <span aria-hidden="true">◇</span>
            <strong>{name}</strong>
            <p>{what}</p>
            <b>Open →</b>
          </Link>
        ))}
      </div>
    </div>
  );
}
