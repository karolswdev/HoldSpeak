// HS-95-06 — the flat route is a thin wrapper around the shared core;
// the desk hosts the same core in the meeting review window.
import {
  decodeWorkroomContext,
  workroomSubjectId,
} from "../workrooms/context";
import { PageHero } from "./pageSupport";
import { HistoryCore } from "./cores/HistoryCore";

export default function HistoryPage() {
  const workroom = decodeWorkroomContext(window.location.search);
  const requested =
    workroomSubjectId(workroom, "meeting") ??
    new URLSearchParams(window.location.search).get("meeting");
  return (
    <div className="page-wrap">
      <HistoryCore
        scope={requested ? `meeting:${requested}` : undefined}
        hero={(actions) => (
          <PageHero eyebrow="Meeting memory" title="Meetings" actions={actions}>
            Review meetings, import recordings, and export retained work.
          </PageHero>
        )}
      />
    </div>
  );
}
