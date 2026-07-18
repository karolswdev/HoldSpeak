// HS-95-07 — thin wrapper; the desk hosts the same core in a window.
import { PageHero } from "./pageSupport";
import { ProfilesCore } from "./cores/ProfilesCore";

export default function ProfilesPage() {
  return (
    <div className="page-wrap">
      <ProfilesCore
        hero={(actions) => (
          <PageHero eyebrow="Runtime" title="Runs on" actions={actions}>
            Name where intelligence runs. Credentials remain on the hub and
            never enter this editor.
          </PageHero>
        )}
      />
    </div>
  );
}
