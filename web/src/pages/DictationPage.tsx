// HS-95-05 — the flat route is a thin wrapper around the shared core;
// the desk hosts the same core in a window (SurfaceWindows).
import { PageHero } from "./pageSupport";
import { DictationCore } from "./cores/DictationCore";

export default function DictationPage() {
  return (
    <div className="page-wrap">
      <DictationCore
        hero={() => (
          <PageHero eyebrow="Daily cockpit" title="Dictation">
            Readiness first, active work second, expert depth when you ask
            for it.
          </PageHero>
        )}
      />
    </div>
  );
}
