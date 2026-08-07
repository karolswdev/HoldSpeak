import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useState } from "react";
import { CycleGadget, LampGadget, PadGadget } from "../../desk/surface/gadgets";
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

export function ConstitutionalContextCore() {
  const [ctx, setCtx] = useState<ContextState | null>(null);
  const [loadError, setLoadError] = useState("");
  const [draft, setDraft] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [viewingRev, setViewingRev] = useState<number | null>(null);

  const limit = ctx?.char_limit || CHAR_LIMIT;

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
        setSaveError(res.error);
      } else {
        setCtx(res.context ?? null);
        setDirty(false);
        setViewingRev(null);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
        void loadHistory();
      }
    } catch (err: any) {
      setSaveError(err?.message || "Save failed");
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

  const charCount = draft.length;
  const tokenEstimate = Math.ceil(charCount / 4);
  const pct = charCount / limit;
  const overLimit = charCount > limit;
  const nearLimit = pct >= WARN_THRESHOLD && !overLimit;
  const version = viewingRev === null ? "current" : String(viewingRev);

  if (ctx === null) {
    return (
      <div className="desk-surface-body constitutional-context-core">
        {loadError ? (
          <SurfaceState error={loadError} onRetry={() => void load()} />
        ) : (
          <SurfaceState loading />
        )}
      </div>
    );
  }

  return (
    <div className="desk-surface-body constitutional-context-core">
      <SurfaceSection
        label="Status"
        actions={
          <div className="constitutional-context-actions">
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
                  { value: "current", label: "current" },
                  ...history.map((entry) => ({
                    value: String(entry.revision),
                    label: `rev ${entry.revision}`,
                  })),
                ]}
              />
            ) : null}
            {viewingRev !== null ? (
              <button type="button" className="desk-chip quiet" onClick={exitHistory}>
                Cancel
              </button>
            ) : null}
            <button
              type="button"
              className="desk-chip"
              disabled={!dirty || saving || overLimit}
              onClick={() => void save()}
            >
              {saving ? "Saving…" : viewingRev !== null ? "Restore" : "Save"}
            </button>
          </div>
        }
      >
        <div className="constitutional-context-status" aria-live="polite">
          <span className="constitutional-context-fact">rev {ctx?.revision || 0}</span>
          <span className="constitutional-context-fact">~{tokenEstimate.toLocaleString()} tokens</span>
          <LampGadget
            label={`${charCount.toLocaleString()}/${limit.toLocaleString()} chars`}
            on={overLimit || nearLimit}
            tone={overLimit ? "fail" : "warn"}
          />
          {overLimit ? <LampGadget label="over limit" on tone="fail" /> : null}
          {dirty ? <LampGadget label="unsaved" on tone="warn" /> : null}
          {saved ? <LampGadget label="saved" on tone="ok" /> : null}
          {saveError ? <LampGadget label={saveError} on tone="fail" /> : null}
          {viewingRev !== null ? <LampGadget label={`viewing rev ${viewingRev}`} on tone="warn" /> : null}
        </div>
      </SurfaceSection>

      <SurfaceSection label="Constitutional context" className="constitutional-context-editor-section">
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
          placeholder={"Write context that every agent receives.\n\nExample:\nI'm a senior architect at Acme Corp.\nWe use TypeScript, Python, and Go.\nOur LLM provider is OpenRouter.\nNever use React class components.\nPrefer concise, direct communication."}
          rows={10}
          autoGrow
        />
      </SurfaceSection>
      <SurfaceFooter />
    </div>
  );
}
