// HS-117-09 — extracted from HistoryCore.tsx (lines 201-315).
import { useState } from "react";
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

export function ImportSection({
  onDone,
  onImported,
  scope,
}: {
  onDone(): void;
  onImported(): void;
  scope?: string;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [tags, setTags] = useState("");
  const action = useAction();
  const submit = async () => {
    if (!file) return;
    await action.run(async () => {
      const body = new FormData();
      body.append("file", file);
      if (title.trim()) body.append("title", title.trim());
      if (speaker.trim()) body.append("speaker", speaker.trim());
      if (tags.trim()) body.append("tags", tags.trim());
      body.append("started_at_ms", String(file.lastModified));
      await apiFetch("/api/meetings/import", { method: "POST", body });
      setFile(null);
      setTitle("");
      setSpeaker("");
      setTags("");
      onImported();
      onDone();
    });
  };
  return (
    <SurfaceSection
      actions={
        <Button dense variant="ghost" onClick={onDone}>
          Close
        </Button>
      }
    >
      <div className="surface-record-lead">
        <Button
          variant="primary"
          onClick={() => openSurfaceOr("record-live", "/live", scope)}
        >
          Record meeting
        </Button>
        <span className="quiet">or drop a recording below</span>
      </div>
      <label
        className={"surface-dropwell" + (file ? " has-file" : "")}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          event.stopPropagation();
          const dropped = event.dataTransfer?.files?.[0];
          if (dropped) setFile(dropped);
        }}
      >
        <input
          type="file"
          accept="audio/*,.wav,.mp3,.m4a,.ogg,.flac,.vtt,.srt,.txt"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        {file ? (
          <>
            <span className="surface-dropwell-name surface-primary">
              {file.name}
            </span>
            <small>drop another file to replace it</small>
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
            <small>.wav direct · .mp3 .m4a .ogg .flac via ffmpeg · .vtt .srt .txt</small>
          </>
        )}
      </label>
      {file ? (
        <GadgetGroup>
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
      <div className="surface-actions">
        <Button
          variant="primary"
          loading={action.busy}
          disabled={!file}
          onClick={submit}
        >
          Import
        </Button>
      </div>
    </SurfaceSection>
  );
}
