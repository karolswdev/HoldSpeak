import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { CycleGadget, PadGadget } from "../../desk/surface/gadgets";
import { StatusBar, Toolbar, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { SurfaceSection, SurfaceState } from "../../desk/surface/Surface";
import { apiFetch } from "../../lib/api";
import type {
  ContextState,
  HistoryEntry,
  ConstitutionalContextResponse,
  ConstitutionalContextHistoryResponse,
  ConstitutionalContextSaveResponse,
} from "./core-types";
import "./constitutional-context.css";

const CHAR_LIMIT = 32_768;
const WARN_THRESHOLD = 0.8;
const NOT_SAVED = "Not saved";

export function ConstitutionalContextCore() {
  const [ctx, setCtx] = useState<ContextState | null>(null);
  const [loadError, setLoadError] = useState("");
  const [draft, setDraft] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [viewingRev, setViewingRev] = useState<number | null>(null);

  const limit = ctx?.char_limit || CHAR_LIMIT;
  // The Toolbar and the editor run edge to edge (window grammar).
  useWindowInterior("editor");

  const load = useCallback(async () => {
    setLoadError("");
    try {
      const res = await apiFetch<ConstitutionalContextResponse>("/api/constitutional-context");
      const data = res.context;
      setCtx(data);
      if (viewingRev === null) {
        setDraft(data.content || "");
        setDirty(false);
      }
    } catch {
      setLoadError("Failed to load constitutional context");
    }
  }, [viewingRev]);

  const loadHistory = useCallback(async () => {
    try {
      const res = await apiFetch<ConstitutionalContextHistoryResponse>("/api/constitutional-context/history");
      setHistory(res.revisions || []);
    } catch { /* */ }
  }, []);

  useEffect(() => { void load(); void loadHistory(); }, [load, loadHistory]);

  const save = async () => {
    setSaving(true);
    setSaveError("");
    try {
      const res = await apiFetch<ConstitutionalContextSaveResponse>("/api/constitutional-context", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: draft }),
      });
      if (res.error) {
        setSaveError(NOT_SAVED);
      } else {
        setCtx(res.context ?? null);
        setDirty(false);
        setViewingRev(null);
        setSavedAt(new Date());
        void loadHistory();
      }
    } catch {
      // The face never prints a server exception. The hub log has the cause.
      setSaveError(NOT_SAVED);
    }
    setSaving(false);
  };

  const restoreRevision = (rev: HistoryEntry) => {
    setDraft(rev.content);
    setViewingRev(rev.revision);
    setDirty(true);
  };

  const exitHistory = () => {
    setViewingRev(null);
    setDraft(ctx?.content || "");
    setDirty(false);
  };

  const revision = ctx?.revision ?? 0;
  const charCount = draft.length;
  const tokenEstimate = Math.ceil(charCount / 4);
  const pct = charCount / limit;
  const overLimit = charCount > limit;
  const nearLimit = pct >= WARN_THRESHOLD && !overLimit;
  const version = viewingRev === null ? "current" : String(viewingRev);

  if (ctx === null) {
    return (
      <div className="constitutional-context-core">
        {loadError ? (
          <SurfaceState error={loadError} onRetry={() => void load()} />
        ) : (
          <SurfaceState loading />
        )}
      </div>
    );
  }

  // Window grammar (2026-10-25 audit): title bar → Toolbar (Version
  // history, Cancel, Save) → the editor → StatusBar (revision, size,
  // unsaved, the Saved time). No "Status" caption, no dead foot.
  const lastSaved = savedAt ?? (() => {
    const current = history.find((entry) => entry.revision === revision);
    const at = current?.created_at ? new Date(current.created_at) : null;
    return at && !Number.isNaN(at.getTime()) ? at : null;
  })();
  const clock = (at: Date) => `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
  // The one fact he asks first (atlas 2026-10-27, Context): is this read
  // now? The saved text, not the draft, is what a run reads
  // (holdspeak/constitutional_context.py: the first system message of
  // every engine run; an empty text sends nothing).
  const live = Boolean((ctx?.content || "").trim());
  const statusItems: Array<StatusBarItem | null> = [
    live
      ? { key: "on", lamp: "ok", text: "Every engine run reads this first", testId: "context-on" }
      : { key: "on", text: "Empty: no run reads it", testId: "context-on" },
    saveError ? { key: "error", lamp: "fail", text: saveError } : null,
    overLimit ? { key: "over", lamp: "fail", text: "Over the limit" } : null,
    viewingRev !== null ? { key: "viewing", lamp: "warn", text: `Viewing revision ${viewingRev}` } : null,
    dirty ? { key: "unsaved", lamp: "warn", text: "Not saved yet" } : null,
    revision > 0 ? { key: "rev", text: `Revision ${revision}` } : null,
    charCount > 0 ? { key: "tokens", text: `About ${tokenEstimate.toLocaleString()} tokens` } : null,
    // One line: the canon scan (A8, no counters of zero) reads the guard with its text.
    charCount > 0 ? { key: "chars", lamp: overLimit ? "fail" : nearLimit ? "warn" : undefined, text: `${charCount.toLocaleString()} of ${limit.toLocaleString()} characters` } : null,
    !dirty && lastSaved ? { key: "saved", lamp: "ok", text: `Saved ${clock(lastSaved)}`, testId: "context-saved" } : null,
  ];

  return (
    <div className="constitutional-context-core">
      <Toolbar label="Engine context" data-testid="context-toolbar">
        {history.length > 0 ? (
          <CycleGadget
            label="Version history"
            value={version}
            onChange={(next) => {
              if (next === "current") {
                exitHistory();
                return;
              }
              const revision = history.find((entry) => entry.revision === Number(next));
              if (revision) restoreRevision(revision);
            }}
            options={[
              { value: "current", label: "Current" },
              ...history.map((entry) => ({
                value: String(entry.revision),
                label: `Revision ${entry.revision}`,
              })),
            ]}
          />
        ) : null}
        {viewingRev !== null ? (
          <Button dense variant="ghost" onClick={exitHistory}>
            Cancel
          </Button>
        ) : null}
        <Button
          dense
          variant="primary"
          disabled={!dirty || saving || overLimit}
          loading={saving}
          onClick={() => void save()}
        >
          {viewingRev !== null ? "Restore" : "Save"}
        </Button>
      </Toolbar>

      <SurfaceSection className="constitutional-context-editor-section">
        <PadGadget
          label="Constitutional context"
          value={draft}
          onChange={(next) => {
            setDraft(next);
            setDirty(true);
            setSaveError("");
          }}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "s") {
              event.preventDefault();
              if (dirty && !overLimit) void save();
            }
          }}
          placeholder={"Role, stack, rules\nOne fact per line"}
          rows={10}
          autoGrow
        />
      </SurfaceSection>
      <StatusBar data-testid="context-status" items={statusItems} />
    </div>
  );
}
