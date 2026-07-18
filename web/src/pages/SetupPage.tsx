// HS-95-07 — thin wrapper; the desk hosts the same core in a window.
import { PageHero } from "./pageSupport";
import { SetupCore } from "./cores/SetupCore";

export default function SetupPage() {
  return (
    <div className="page-wrap">
      <SetupCore
        hero={() => (
          <PageHero eyebrow="Arrival" title="Setup and readiness">
            See exactly what is ready, what is optional, and what needs
            attention.
          </PageHero>
        )}
      />
    </div>
  );
}
