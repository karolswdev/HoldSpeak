/** Betterment A6 — the Put it in editor (DESIGN §4, RECIPE A6).
 *
 * Where each result goes: My Inbox (a note, the default), Needs you (a row
 * due today), or a saved destination: a file in a folder, GitHub, Jira,
 * Confluence, email, Slack. A destination only PREPARES the send; he presses
 * Send on the result (the egress rule). One press on a choice saves it; the
 * line folds its value in place. Each destination row says where it goes. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { readableError } from "../../../lib/api";
import { EgressChip } from "../../surface";
import { useDestinations } from "../../surface/send";
import { targetName, type Destination } from "../../../features/channels/channels";
import { putWords } from "./model";

const DESTINATION = "destination:";

/** The Put it in line's value: the destination by its saved name. */
export function PutValue({ target }: { target: string | null | undefined }) {
  const value = String(target ?? "inbox");
  if (!value.startsWith(DESTINATION)) return <>{putWords(value)}</>;
  return <DestinationValue id={value.slice(DESTINATION.length)} />;
}

function DestinationValue({ id }: { id: string }) {
  const destinations = useDestinations();
  const found = (destinations.data ?? []).find((d) => d.id === id);
  return <>{putWords(`${DESTINATION}${id}`, found?.name)}</>;
}

function placeOf(d: Destination): { label: string; scope: "local" | "cloud" } {
  if (d.channel === "file") return { label: targetName(d.channel, d.target) || "Folder", scope: "local" };
  return { label: d.channel.toUpperCase(), scope: "cloud" };
}

export function PutEditor({
  target,
  onChoose,
}: {
  target: string | null | undefined;
  /** Save one choice (`inbox`, `needs_you`, `destination:<id>`). */
  onChoose: (next: string) => Promise<void>;
}) {
  const current = String(target ?? "inbox");
  const destinations = useDestinations();
  const [busy, setBusy] = useState<string | null>(null);
  const [refusal, setRefusal] = useState<string | null>(null);

  const choose = async (next: string) => {
    setBusy(next);
    setRefusal(null);
    try {
      await onChoose(next);
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setBusy(null);
    }
  };

  const row = (key: string, name: string, chip?: { label: string; scope: "local" | "cloud" }) => {
    const using = key === current;
    return (
      <li key={key} className="automation-engine" data-testid="automation-put-choice"
        data-in-use={using || undefined}>
        <span className="automation-engine-name">{name}</span>
        {chip ? <EgressChip label={chip.label} scope={chip.scope} title={`The result goes to ${chip.label}`} /> : null}
        {using ? (
          <span className="automation-engine-using">In use</span>
        ) : (
          <Button dense variant="ghost" loading={busy === key}
            disabled={Boolean(busy) && busy !== key}
            aria-label={`Put it in ${name}`}
            onClick={() => void choose(key)}>
            Use
          </Button>
        )}
      </li>
    );
  };

  const saved = (destinations.data ?? []).filter((d) => d.state === "active");
  return (
    <div className="automation-put-editor" data-testid="automation-put-editor">
      <ul className="automation-engine-list">
        {row("inbox", "My Inbox")}
        {row("needs_you", "Needs you")}
      </ul>
      {saved.length ? (
        <section aria-label="Saved destinations">
          <span className="automation-editor-head">Prepare a send (you press Send)</span>
          <ul className="automation-engine-list">
            {saved.map((d) => row(`${DESTINATION}${d.id}`, d.name, placeOf(d)))}
          </ul>
        </section>
      ) : null}
      {destinations.failed ? (
        <div className="automation-failure">
          <p className="automation-failure-words">Could not read the saved destinations. Press Try again.</p>
          <Button dense variant="ghost" onClick={destinations.reload}>Try again</Button>
        </div>
      ) : null}
      {refusal ? <p className="automation-refusal" role="alert">{refusal}</p> : null}
    </div>
  );
}
