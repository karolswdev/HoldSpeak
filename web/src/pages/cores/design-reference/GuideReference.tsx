/** Local guide specimen. No connector, engine or saved record. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { GuideNote, ListPane, ListView } from "../../../desk/surface";
export function GuideReference() {
  const [body, setBody] = useState<HTMLDivElement | null>(null);
  const owner = body?.closest<HTMLElement>('[data-layer="window"]') ?? body;
  const [step, setStep] = useState(-1);
  const [picked, setPicked] = useState<string | null>(null);
  const target = body?.querySelector<HTMLElement>(
    step === 0 ? ".object-list-row" : step === 1 ? '[data-testid="guide-example-new"]' : ".surface-list-pane-preview",
  );
  const stop = () => {
    setStep(-1);
    setPicked(null);
  };
  return (
    <div ref={setBody} className="surface-preference-pane">
      <Button
        variant="secondary"
        onClick={() => {
          setStep(0);
          setPicked("tracing");
        }}
      >
        Show the guide note
      </Button>
      <ListPane
        label="Selected decision"
        list={
          <ListView
            label="Example decisions"
            rows={[
              {
                id: "tracing",
                kind: "decision",
                name: "Adopt tracing for every service",
              },
            ]}
            selectedId={picked}
            onSelect={setPicked}
            onClearSelection={() => setPicked(null)}
          />
        }
      >
        {picked
          ? "Every service sends traces through one collector."
          : "Select a decision"}
      </ListPane>
      <Button
        variant="secondary"
        data-testid="guide-example-new"
        onClick={stop}
      >
        New decision
      </Button>
      {owner && step >= 0 ? (
        <GuideNote
          owner={owner}
          target={target}
          words={
            step === 0
              ? "Click a decision to select it. Its text shows below the list."
              : step === 1 ? "New decision opens a form in this window." : "The selected decision stays in its reading well."
          }
          count={`${step + 1} of 3`}
          last={step === 2}
          onStop={stop}
          onNext={() => (step < 2 ? setStep(step + 1) : stop())}
        />
      ) : null}
    </div>
  );
}
