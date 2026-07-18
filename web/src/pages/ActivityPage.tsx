// HS-95-04 — the flat route is a thin wrapper: page chrome around the
// shared core. The desk hosts the same core in a window (SurfaceWindows).
import { PageHero } from "./pageSupport";
import { ActivityCore } from "./cores/ActivityCore";

export default function ActivityPage() {
  return (
    <div className="page-wrap">
      <ActivityCore
        hero={(actions) => (
          <PageHero
            eyebrow="This-device context"
            title="Activity"
            actions={actions}
          >
            Review captured browsing context, privacy controls, and project
            rules.
          </PageHero>
        )}
      />
    </div>
  );
}
