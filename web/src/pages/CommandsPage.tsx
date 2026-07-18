// HS-95-04 — the flat route is a thin wrapper: page chrome around the
// shared core. The desk hosts the same core in a window (SurfaceWindows).
import { PageHero } from "./pageSupport";
import { CommandsCore } from "./cores/CommandsCore";

export default function CommandsPage() {
  return (
    <div className="page-wrap">
      <CommandsCore
        hero={() => (
          <PageHero eyebrow="Voice commands" title="Commands">
            What you see is what fires. Test an action before you trust it.
          </PageHero>
        )}
      />
    </div>
  );
}
