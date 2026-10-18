// HS-117-09 — extracted from HistoryCore.tsx (lines 201-315).
import { useEffect, useState } from "react";
import { openSurfaceOr } from "../../../desk/shell";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import {
  GadgetGroup,
  GadgetRow,
  StringGadget,
} from "../../../desk/surface/gadgets";
import {
  SurfaceSection,
  SurfaceState,
} from "../../../desk/surface/Surface";
import { useAction } from "../core-hooks";
import { IMPORT_ACCEPT, startedAtMs, toDatetimeLocal, whenFromFile } from "./importWhen";

export function ImportSection({
  onDone,
  onImported,
  scope,
  initialFile = null,
}: {
  onDone(): void;
  onImported(): void;
  scope?: string;
  /** Capture C3: the file the head's Import (or a drop on the window) chose. */
  initialFile?: File | null;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [tags, setTags] = useState("");
  const [when, setWhen] = useState("");
  const action = useAction();
  // Capture C3: "When was this?" fills from the file (its VTT/SRT header
  // date, a date in its name, else its modified time). HS-201-10 (rehearsal
  // defect 10) sent `lastModified` unseen, so a WAV copied in June landed
  // under JUN 03; the value is now shown and the owner can change it.
  const choose = (next: File | null) => {
    setFile(next);
    setWhen("");
    if (!next) return;
    void whenFromFile(next).then((found) => {
      if (found) setWhen((current) => current || toDatetimeLocal(found));
    });
  };
  useEffect(() => {
    if (initialFile) choose(initialFile);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialFile]);
  const submit = async () => {
    if (!file) return;
    await action.run(async () => {
      const body = new FormData();
      body.append("file", file);
      if (title.trim()) body.append("title", title.trim());
      if (speaker.trim()) body.append("speaker", speaker.trim());
      if (tags.trim()) body.append("tags", tags.trim());
      const started = startedAtMs(when);
      if (started !== null) body.append("started_at_ms", String(started));
      await apiFetch("/api/meetings/import", { method: "POST", body });
      setFile(null);
      setTitle("");
      setSpeaker("");
      setTags("");
      setWhen("");
      onImported();
      onDone();
    });
  };
  // PHILO-17 (the Today language): two plates side by side: record now,
  // or bring a recording in. ONE filled primary: Record meeting until a
  // file is chosen, then Import.
  return (
    <SurfaceSection
      label="Record or import"
      actions={
        <Button dense variant="ghost" onClick={onDone}>
          Close
        </Button>
      }
    >
      <div className="meetings-import-plates">
        <div className="meetings-import-record" data-testid="meetings-import-record">
          <span className="live-rec" aria-hidden="true"><span className="live-rec-lamp" />REC</span>
          <span className="meetings-import-words">Record a meeting now</span>
          <Button
            variant={file ? "secondary" : "primary"}
            onClick={() => openSurfaceOr("record-live", "/live", scope)}
          >
            Record meeting
          </Button>
        </div>
      <label
        className={"surface-dropwell" + (file ? " has-file" : "")}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          event.stopPropagation();
          const dropped = event.dataTransfer?.files?.[0];
          if (dropped) choose(dropped);
        }}
      >
        <input
          type="file"
          accept={IMPORT_ACCEPT}
          onChange={(event) => choose(event.target.files?.[0] ?? null)}
        />
        {file ? (
          <>
            <span className="surface-dropwell-name surface-primary">
              {file.name}
            </span>
            <small>Drop another file to replace it</small>
          </>
        ) : (
          <>
            <span className="surface-dropwell-glyph" aria-hidden="true">
              ⇣
            </span>
            <span className="surface-primary">Drop it here, or browse</span>
            {/* Rendered as mono tokens (CSS uppercases); the literal
                lowercase suffixes and ffmpeg stay in source — they are
                the wire truth. */}
            <span className="surface-token">.WAV .MP3 .M4A .OGG .FLAC .VTT .SRT .TXT</span>
          </>
        )}
      </label>
      </div>
      {file ? (
        <GadgetGroup>
          <GadgetRow label="When was this?" controlWidth="full">
            <StringGadget
              type="datetime-local"
              label="When was this?"
              value={when}
              onChange={setWhen}
              micDraftScope="import-when"
              inputProps={{ "data-testid": "import-when" } as Record<string, string>}
            />
          </GadgetRow>
          <GadgetRow label="TITLE">
            <StringGadget label="Title" value={title} onChange={setTitle} />
          </GadgetRow>
          <GadgetRow label="SPEAKER">
            <StringGadget
              label="Speaker"
              value={speaker}
              onChange={setSpeaker}
            />
          </GadgetRow>
          <GadgetRow label="TAGS" fact="COMMA SEPARATED">
            <StringGadget label="Tags" value={tags} onChange={setTags} />
          </GadgetRow>
        </GadgetGroup>
      ) : null}
      {action.message ? <SurfaceState error={action.message} /> : null}
      {file ? (
        <div className="surface-actions">
          <Button
            variant="primary"
            loading={action.busy}
            onClick={submit}
          >
            Import
          </Button>
        </div>
      ) : null}
    </SurfaceSection>
  );
}
