/* HS-111-02 — correction memory is a machine table: KIND | GIST |
   VALUE | REACH, the arming per row. REACH is the wire's `similar`
   count — what makes the memory legible as equipment. */
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { asRows, useResource } from "../../pageSupport";
import type {
  DictationCorrectionsResponse,
  DictationLearningDigestResponse,
} from "../core-types";
import { presentValue } from "../../../desk/surface/format";
import {
  ConfirmVerb,
  SurfaceFacts,
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  GadgetGroup,
  GadgetTable,
} from "../../../desk/surface/gadgets";

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
    return <p className="speak-token-line">WEEK · TAUGHT 0</p>;
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
  const resource = useResource<DictationCorrectionsResponse>("/api/dictation/corrections", {});
  const digest = useResource<DictationLearningDigestResponse>("/api/dictation/learning-digest", {});
  const rows = asRows(resource.data, ["items", "corrections"]);
  const remove = async (row: Record<string, unknown>) => {
    await apiFetch(
      `/api/dictation/corrections/${encodeURIComponent(String(row.id))}`,
      { method: "DELETE" },
    );
    await resource.reload();
  };
  return (
    <>
      <GadgetGroup label="Correction memory">
        <SurfaceState
          loading={resource.loading}
          error={resource.error}
          empty={!rows.length}
          emptyLabel="Nothing learned yet"
          emptyGlyph="◈"
          onRetry={() => void resource.reload()}
        >
          <GadgetTable
            head={["Kind", "Gist", "Value", "Reach"]}
            rows={rows.map((row) => [
              String(row.kind ?? "—"),
              String(row.gist ?? "—"),
              presentValue(row.value ?? row.replacement) || "—",
              presentValue(row.similar) || "—",
            ])}
            verbs={(index) => (
              <ConfirmVerb
                label="×"
                confirmLabel="Forget?"
                onConfirm={() => void remove(rows[index])}
              />
            )}
          />
        </SurfaceState>
      </GadgetGroup>
      <GadgetGroup label="Learning digest">
        <SurfaceState
          loading={digest.loading}
          error={digest.error}
          onRetry={() => void digest.reload()}
        >
          <LearningDigestFacts digest={digest.data} />
        </SurfaceState>
      </GadgetGroup>
    </>
  );
}
