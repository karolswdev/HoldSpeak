// Parked 2026-11-11: this Room drawing is replaced by the shared list and inspector seats.
// @ts-nocheck
// The Room's postures in their order: Review > Update > Steward > Prepare.
// Each one replaces the Room body while it is open. Null when none is open.
import type React from "react";
import { Button } from "../../../components/signal/Signal";
import type { CoreProps } from "../../../pages/cores/core-types";
import { ReviewPosture } from "../review/ReviewPosture";
import type { useReviewController } from "../review/useReviewController";
import { UpdatePosture } from "../update/UpdatePosture";
import type { useUpdateController } from "../update/useUpdateController";
import { fetchUpdate } from "../update/api";
import { StewardPosture } from "../steward/StewardPosture";
import type { useStewardController } from "../steward/useStewardController";
import { PreparePosture } from "../prepare/PreparePosture";
import type { usePrepareController } from "../prepare/usePrepareController";
import type { RoomAsk } from "./Ask";

export function roomPosture({
  hero,
  onRefresh,
  sendFailure,
  reviewCtrl,
  updateCtrl,
  stewardCtrl,
  prepareCtrl,
  askCtrl,
  projectName,
  onOpenRef,
}: {
  hero: CoreProps["hero"];
  onRefresh: () => void;
  sendFailure: React.ReactNode;
  reviewCtrl: ReturnType<typeof useReviewController>;
  updateCtrl: ReturnType<typeof useUpdateController>;
  stewardCtrl: ReturnType<typeof useStewardController>;
  prepareCtrl: ReturnType<typeof usePrepareController>;
  askCtrl: RoomAsk;
  projectName: string;
  onOpenRef: (ref: string) => void;
}): React.ReactElement | null {
  const refresh = () => (hero ? hero(<Button dense variant="ghost" onClick={onRefresh}>Refresh</Button>) : null);

  if (reviewCtrl.posture === "active") {
    return (
      <>
        {refresh()}
        <ReviewPosture ctrl={reviewCtrl} />
      </>
    );
  }

  if (updateCtrl.posture !== "off") {
    return (
      <>
        {refresh()}
        {sendFailure}
        <UpdatePosture ctrl={updateCtrl} />
      </>
    );
  }

  if (stewardCtrl.posture !== "off") {
    return (
      <>
        {refresh()}
        <StewardPosture
          ctrl={stewardCtrl}
          onOpenReview={(reviewId: string) => {
            stewardCtrl.exitSteward();
            void reviewCtrl.enterReview(reviewId);
          }}
          onOpenUpdate={async (updateId: string) => {
            // Read the update first; the Steward posture stays on the
            // receipt until the read lands (a failure is shown there).
            const update = await fetchUpdate(updateId);
            stewardCtrl.exitSteward();
            updateCtrl.openUpdate(update);
          }}
        />
      </>
    );
  }

  if (prepareCtrl.posture !== "off") {
    return (
      <>
        {refresh()}
        <div className="room-body" data-testid="room-body">
          <PreparePosture
            ctrl={prepareCtrl}
            projectName={projectName}
            onOpenRef={onOpenRef}
            onResultChange={(purpose) => {
              // `Result → Answer` walks back to the Room well with his words.
              askCtrl.setPrompt(purpose);
              prepareCtrl.exit();
            }}
          />
        </div>
      </>
    );
  }

  return null;
}
