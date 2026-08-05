import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";

const CHAR_LIMIT = 32_768;
const WARN_THRESHOLD = 0.8;

interface ContextState {
  content: string;
  revision: number;
  content_hash: string;
  char_limit?: number;
}

interface HistoryEntry {
  content: string;
  revision: number;
  content_hash: string;
  created_at: string;
}

export function ConstitutionalContextCore() {
  const [ctx, setCtx] = useState<ContextState | null>(null);
  const [draft, setDraft] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [viewingRev, setViewingRev] = useState<number | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const limit = ctx?.char_limit || CHAR_LIMIT;

  const load = useCallback(async () => {
    try {
      const res = await apiFetch<any>("/api/constitutional-context");
      const data = res.context;
      setCtx(data);
      if (viewingRev === null) {
        setDraft(data.content || "");
        setDirty(false);
      }
    } catch { /* honest empty state */ }
  }, [viewingRev]);

  const loadHistory = useCallback(async () => {
    try {
      const res = await apiFetch<any>("/api/constitutional-context/history");
      setHistory(res.revisions || []);
    } catch { /* */ }
  }, []);

  useEffect(() => { void load(); void loadHistory(); }, [load, loadHistory]);

  const save = async () => {
    setSaving(true);
    setSaveError("");
    try {
      const res = await apiFetch<any>("/api/constitutional-context", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: draft }),
      });
      if (res.error) {
        setSaveError(res.error);
      } else {
        setCtx(res.context);
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

  return (
    <div className="desk-surface-body" style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Status bar */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", borderBottom: "1px solid var(--border-rule)", fontFamily: "var(--font-mono)", fontSize: "11px", flexWrap: "wrap" }}>
        <span style={{ opacity: 0.6 }}>
          rev {ctx?.revision || 0}
        </span>
        <span style={{ opacity: 0.6 }}>
          ~{tokenEstimate.toLocaleString()} tokens
        </span>
        <span style={{
          color: overLimit ? "var(--danger-signal, #f87171)" : nearLimit ? "var(--warn-signal, #fbbf24)" : "var(--text-faint)",
          fontWeight: overLimit || nearLimit ? 700 : 400,
        }}>
          {charCount.toLocaleString()}/{limit.toLocaleString()}
        </span>
        {overLimit ? (
          <span style={{ color: "var(--danger-signal, #f87171)", fontWeight: 700 }}>OVER LIMIT</span>
        ) : null}
        {dirty ? (
          <span style={{ color: "var(--accent-text, orange)" }}>UNSAVED</span>
        ) : null}
        {saved ? (
          <span style={{ color: "var(--ok, #34d399)" }}>SAVED</span>
        ) : null}
        {saveError ? (
          <span style={{ color: "var(--danger-signal, #f87171)" }}>{saveError}</span>
        ) : null}
        {viewingRev !== null ? (
          <span style={{ color: "var(--warn-signal, #fbbf24)" }}>
            VIEWING REV {viewingRev}
          </span>
        ) : null}
        <span style={{ flex: 1 }} />
        {history.length > 0 ? (
          <select
            value={viewingRev ?? ""}
            onChange={(e) => {
              const val = e.target.value;
              if (!val) { exitHistory(); return; }
              const rev = history.find((h) => h.revision === Number(val));
              if (rev) restoreRevision(rev);
            }}
            style={{ fontFamily: "var(--font-mono)", fontSize: "10px" }}
            aria-label="Version history"
          >
            <option value="">current</option>
            {history.map((h) => (
              <option key={h.revision} value={h.revision}>
                rev {h.revision}
              </option>
            ))}
          </select>
        ) : null}
        {viewingRev !== null ? (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={exitHistory}
          >
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

      {/* Editor */}
      <textarea
        ref={textareaRef}
        value={draft}
        onChange={(e) => { setDraft(e.target.value); setDirty(true); setSaveError(""); }}
        onKeyDown={(e) => {
          if ((e.metaKey || e.ctrlKey) && e.key === "s") {
            e.preventDefault();
            if (dirty && !overLimit) void save();
          }
        }}
        placeholder={"Write context that every agent receives.\n\nExample:\nI'm a senior architect at Acme Corp.\nWe use TypeScript, Python, and Go.\nOur LLM provider is OpenRouter.\nNever use React class components.\nPrefer concise, direct communication."}
        style={{
          flex: 1,
          resize: "none",
          border: "none",
          outline: "none",
          padding: "12px",
          fontFamily: "var(--font-mono)",
          fontSize: "13px",
          lineHeight: "1.6",
          background: "transparent",
          color: "inherit",
        }}
        aria-label="Constitutional context"
      />
    </div>
  );
}
