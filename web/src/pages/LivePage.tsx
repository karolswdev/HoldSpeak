// HS-95-06 — the flat route is a thin wrapper around the shared core;
// the desk hosts the same core in the live meeting window.
import { PageHero } from "./pageSupport";
import { LiveCore } from "./cores/LiveCore";

export default function LivePage() {
  return (
    <div className="page-wrap">
      <LiveCore
        hero={(actions) => (
          <PageHero eyebrow="Meeting room" title="Live meeting" actions={actions}>
            Record a meeting, review its transcript, and keep the result.
          </PageHero>
        )}
      />
    </div>
  );
}
