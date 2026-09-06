/* HS-111-02 — correction memory is a machine table: KIND | GIST |
   VALUE | APPLIED, the arming per row.
   HS-176-02 — three fixes on the live defect:
   (1) the route serves the gist as `key` (corrections.py), never
       `gist`, so every GIST cell on the owner's desk read a dash;
   (2) REACH was the wire's `similar` — similar transcripts, counting
       the teaching utterance itself. It is now `applied`: the real
       count of retained journal rows the rule FIRED on, absent at zero
       (rule A.8);
   (3) the remove verb is the library Button `Forget`, not the `×`
       glyph (rule A.1). */
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
            head={["Kind", "Gist", "Value", "Applied"]}
            rows={rows.map((row) => [
              String(row.kind ?? "—").toUpperCase(),
              String(row.key ?? "—"),
              presentValue(row.value ?? row.replacement) || "—",
              Number(row.applied ?? 0) > 0 ? `${Number(row.applied)} APPLIED` : "—",
            ])}
            verbs={(index) => (
              <ConfirmVerb
                label="Forget"
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
