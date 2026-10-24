import { useCallback, useLayoutEffect, useMemo, useRef, useState } from "react";
import { StateChip } from "../../../desk/surface";
import { RoomFiledNotesSection, type FiledNoteAdapter, type FiledNoteRequest } from "../../../features/project-room/RoomFiledNotesSection";
import type { ResourcesRead, ResourcesState } from "../../../desk/drawer/useDrawerData";

export type FiledNotesPreset = "filed-notes" | "files-not-read" | "not-filed" | "unavailable";
const ref = "note:review-record" as const;

/** Local data only. The same Files controller and view used by the Room
 * receive a small read/Open adapter; no Project, Note, or model route runs. */
export function FiledNotesReference({ preset }: { preset: FiledNotesPreset }) {
  const [resourcesState, setResourcesState] = useState<ResourcesState>(preset === "files-not-read" ? "failed" : "ok");
  const [request, setRequest] = useState<FiledNoteRequest>(
    preset === "not-filed" || preset === "unavailable" ? { ref, seq: 1 } : null,
  );
  const [opened, setOpened] = useState<{ noteRef: string; projectId: string } | null>(null);
  const outcomeRef = useRef<HTMLParagraphElement | null>(null);
  const refs = useMemo(() => preset === "not-filed" ? [] : [ref], [preset]);
  const refreshResources = useCallback(async (): Promise<ResourcesRead> => {
    setResourcesState("ok");
    return { state: "ok", refs };
  }, [refs]);
  const followCurrentResources = useCallback(async (result: ResourcesRead) => result, []);
  const adapter = useMemo<FiledNoteAdapter>(() => ({
    read: async () => preset === "unavailable" ? { state: "unavailable" } : { state: "ok", title: "Review record" },
    open: (noteRef, context) => setOpened({ noteRef, projectId: context.projectReturn.projectId }),
  }), [preset]);
  useLayoutEffect(() => {
    if (opened) outcomeRef.current?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
  }, [opened]);
  return <section className="reference-example reference-filed-notes" data-testid="reference-filed-notes" aria-label="Filed notes pattern">
    <div className="reference-example-head"><h2>Project room · Files</h2><StateChip state="idle" label="LOCAL SPECIMEN" /></div>
    <RoomFiledNotesSection projectId="local-project" resourceRefs={refs} resourcesState={resourcesState}
      refreshResources={refreshResources} followCurrentResources={followCurrentResources}
      members={[]} request={request} onRequestHandled={() => setRequest(null)} adapter={adapter} />
    {opened ? <p ref={outcomeRef} className="reference-receipt" role="status">
      OPENED LOCALLY · {opened.noteRef} · {opened.projectId}
    </p> : null}
  </section>;
}
