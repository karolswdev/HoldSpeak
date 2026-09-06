/* HS-111-02 — the Configure door's learning panel.
   HS-176-05 — the corrections TABLE moved out of the door and became the
   `Learned` wing (settled design D2(c)): "the only path to what the
   pipeline learned is the gear" was the defect, and a wing is the fix.
   `Learned.tsx` owns the rows, the labels, the real `N APPLIED` count and
   the `Forget` verb; this panel keeps what the wing does not carry —
   the LEARNING DIGEST (the windowed week token line, whose
   `reach_for_gist` reach appears on no ledger face, ruling R3). */
import { asRows, useResource } from "../../pageSupport";
import type { DictationLearningDigestResponse } from "../core-types";
import { SurfaceFacts, SurfaceState } from "../../../desk/surface/Surface";
import { GadgetGroup } from "../../../desk/surface/gadgets";

/* HS-111-02 — the digest is a fact token row, never a sentence:
   WEEK · TAUGHT n · CORRECTED n · REACHED n (empty: WEEK · —). */
function LearningDigestFacts({ digest }: { digest: DictationLearningDigestResponse }) {
  const totals = digest.totals ?? {};
  const made = Number(totals.corrections_made ?? 0);
  const corrected = Number(totals.dictations_corrected ?? 0);
  const nudged = Number(totals.similar_nudged ?? 0);
  const topBlocks = asRows(digest, ["by_block"]).slice(0, 3);
  if (!made && !corrected) {
    // The empty week is an honest zero token, never a sentence.
    return <p className="speak-token-line">WEEK · NO CORRECTIONS</p>;
  }
  return (
    <>
      <p className="speak-token-line">
        {[
          "WEEK",
          `TAUGHT ${made}`,
          corrected ? `CORRECTED ${corrected}` : "",
          nudged ? `REACHED ${nudged}` : "",
        ]
          .filter(Boolean)
          .join(" · ")}
      </p>
      {topBlocks.length ? (
        <SurfaceFacts
          value={Object.fromEntries(
            topBlocks.map((row) => [
              String(row.block_id ?? "block"),
              row.count,
            ]),
          )}
        />
      ) : null}
    </>
  );
}

export function Memory() {
  const digest = useResource<DictationLearningDigestResponse>("/api/dictation/learning-digest", {});
  return (
    <GadgetGroup label="Learning digest">
      <SurfaceState
        loading={digest.loading}
        error={digest.error}
        onRetry={() => void digest.reload()}
      >
        <LearningDigestFacts digest={digest.data} />
      </SurfaceState>
    </GadgetGroup>
  );
}
