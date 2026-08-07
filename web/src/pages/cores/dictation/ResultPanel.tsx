// The response display with correction form (verdict + teach).
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceCode,
} from "../../../desk/surface/Surface";
import {
  CycleGadget,
  FoldGadget,
  GadgetRow,
  StringGadget,
} from "../../../desk/surface/gadgets";

export function ResultPanel({
  result,
  verdict,
  setVerdict,
  correctionKind,
  setCorrectionKind,
  correctionValue,
  setCorrectionValue,
  busy,
  onTeach,
  announce,
}: {
  result: Record<string, unknown>;
  verdict: "" | "right" | "wrong";
  setVerdict: (next: "" | "right" | "wrong") => void;
  correctionKind: string;
  setCorrectionKind: (next: string) => void;
  correctionValue: string;
  setCorrectionValue: (next: string) => void;
  busy: boolean;
  onTeach: () => void;
  announce: (text: string, tone?: "ok" | "warn") => void;
}) {
  return (
    <section className="speak-result" aria-label="Pipeline result">
      <SurfaceCode>{`FINAL_TEXT: ${String(result.final_text ?? result.text ?? result.output ?? "")}`}</SurfaceCode>
      <div className="speak-result-facts">
        {result.intent ? <span>INTENT {String(result.intent)}</span> : null}
        {result.total_ms ? (
          <span>LATENCY {String(result.total_ms)} MS</span>
        ) : null}
        {result.target_profile ? (
          <span>TARGET {String(result.target_profile)}</span>
        ) : null}
      </div>
      <div
        className="surface-actions speak-result-verdict"
        aria-label="Rate this result"
      >
        <Button
          dense
          onClick={() => {
            setVerdict("right");
            announce("Marked OK · no correction written");
          }}
        >
          OK
        </Button>
        <Button dense variant="ghost" onClick={() => setVerdict("wrong")}>
          Wrong
        </Button>
      </div>
      {verdict === "wrong" ? (
        <div
          className="speak-correct"
          role="group"
          aria-label="Correct this result"
        >
          <GadgetRow label="Field">
            <CycleGadget
              label="Correction field"
              value={correctionKind}
              options={[
                { value: "target", label: "Delivery target" },
                { value: "intent", label: "Intent" },
              ]}
              onChange={setCorrectionKind}
            />
          </GadgetRow>
          <GadgetRow label="Value">
            <StringGadget
              label="Correct value"
              value={correctionValue}
              onChange={setCorrectionValue}
            />
          </GadgetRow>
          <div className="surface-actions">
            <Button
              dense
              loading={busy}
              disabled={!correctionValue.trim()}
              aria-label="Teach correction"
              onClick={onTeach}
            >
              Teach
            </Button>
          </div>
        </div>
      ) : null}
      <FoldGadget title="RAW · TRACE">
        <SurfaceCode>{JSON.stringify(result, null, 2)}</SurfaceCode>
      </FoldGadget>
    </section>
  );
}
