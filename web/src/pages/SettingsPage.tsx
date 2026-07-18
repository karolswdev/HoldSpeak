// HS-95-07 — thin wrapper; the desk hosts the same core in a window.
import {
  decodeWorkroomContext,
  workroomSubjectId,
} from "../workrooms/context";
import { PageHero } from "./pageSupport";
import { SettingsCore } from "./cores/SettingsCore";

export default function SettingsPage() {
  const workroom = decodeWorkroomContext(window.location.search);
  const subject = workroomSubjectId(workroom, "integration");
  return (
    <div className="page-wrap">
      <SettingsCore
        scope={subject ? `integration:${subject}` : undefined}
        hero={(actions) => (
          <PageHero eyebrow="Configuration" title="Settings" actions={actions}>
            Find and update settings by task.
          </PageHero>
        )}
      />
    </div>
  );
}
