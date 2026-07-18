// HS-95-07 — thin wrapper; the desk hosts the same core in a window.
import { PageHero } from "./pageSupport";
import { CadenceCore } from "./cores/CadenceCore";

export default function CadencePage() {
  return (
    <div className="page-wrap">
      <CadenceCore
        hero={(actions) => (
          <PageHero eyebrow="Follow-through" title="Cadence" actions={actions}>
            Open loops become prepared next moves; nothing is sent until you
            choose.
          </PageHero>
        )}
      />
    </div>
  );
}
