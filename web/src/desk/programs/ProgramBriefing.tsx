import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { PaneActions, PaneNotice, InspectorQuestion } from "../surface";
import {
  briefable,
  copyPageLink,
  pageWords,
  programRef,
  revokePage,
  type OpenPage,
} from "../reach";
import { bindingId, programFailure } from "./liveModel";
import type { Program, YourTurnItem } from "./types";
export function ProgramBriefing({
  program,
  item,
  onError,
}: {
  program: Program;
  item: YourTurnItem;
  onError(words: string): void;
}) {
  const [page, setPage] = useState<OpenPage | null>(item.page ?? null),
    [revoke, setRevoke] = useState(false),
    [busy, setBusy] = useState(false);
  const copy = async () => {
    if (busy) return;
    setBusy(true);
    try {
      setPage(await copyPageLink(programRef(program.id, item.id)));
      onError("");
    } catch (e) {
      onError(programFailure(e));
    } finally {
      setBusy(false);
    }
  };
  if (!briefable(item.kind)) return null;
  return (
    <>
      {revoke && page ? (
        <InspectorQuestion
          actionId="revoke-briefing"
          targetId={`${bindingId(program, item.step_id ?? "")}:${page.package_id}`}
          question="Revoke this page link?"
          keeps={["The question in Programs"]}
          clears="Access through the page link"
          cancel={() => setRevoke(false)}
          verb={{
            label: "Revoke link",
            busy,
            run: () => {
              setBusy(true);
              void revokePage(page.package_id)
                .then(() => {
                  setPage(null);
                  setRevoke(false);
                })
                .catch((e) => onError(programFailure(e)))
                .finally(() => setBusy(false));
            },
          }}
        />
      ) : (
        <PaneActions>
          <Button variant="ghost" disabled={busy} onClick={() => void copy()}>
            Copy page link
          </Button>
          {page ? (
            <Button
              variant="ghost"
              disabled={busy}
              onClick={() => setRevoke(true)}
            >
              Revoke link
            </Button>
          ) : null}
        </PaneActions>
      )}
      {page ? <PaneNotice>{pageWords(page)}</PaneNotice> : null}
    </>
  );
}
