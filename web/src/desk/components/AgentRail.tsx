// The agent rail (HS-73-07): personas run FROM the world and their results
// land IN the world. A slim right-edge rail of avatars (the iPad's Agents
// rail); tap → an anchored prompt (not a modal) → run through the real
// route → the result renders with a copy affordance. Personas ONLY —
// a coder is a live session, never railed (the Primitive Framework rule).
import { useState } from "react";
import { useDesk } from "../store";

export function AgentRail() {
  const agents = useDesk((s) => s.items.agent);
  const profiles = useDesk((s) => s.profiles);
  const [openId, setOpenId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [output, setOutput] = useState("");
  const [copied, setCopied] = useState(false);

  if (!agents.length) return null;

  const egressDot = (a: any) => {
    const p = profiles.find((x) => x.id === a.profileId);
    if (!p) return null;
    const cloud = (p.kind || "onDevice") !== "onDevice";
    return (
      <span
        className={`desk-rail-egress is-${cloud ? "cloud" : "local"}`}
        title={cloud ? `☁ ${String(p.base_url || "endpoint")}` : "⌂ On device"}
      />
    );
  };

  const run = async (id: string) => {
    setBusyId(id);
    setOutput("");
    setCopied(false);
    try {
      const res = await fetch(`/api/agents/${encodeURIComponent(id)}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input }),
      });
      const data = await res.json().catch(() => ({}));
      setOutput(String(data.output || data.error || `HTTP ${res.status}`));
    } catch (e: any) {
      setOutput(String(e?.message || e));
    } finally {
      setBusyId(null);
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard blocked; the text is selectable */
    }
  };

  return (
    <div className="desk-rail">
      {agents.map((a: any) => (
        <div key={a.id} className="desk-rail-slot">
          <button
            type="button"
            className={
              "desk-rail-avatar" +
              (openId === a.id ? " open" : "") +
              (busyId === a.id ? " working" : "")
            }
            title={String(a.name || a.id)}
            onClick={() => {
              setOpenId((v) => (v === a.id ? null : a.id));
              setOutput("");
              setInput("");
            }}
          >
            <span aria-hidden="true">{String(a.avatar || "🤖")}</span>
            {egressDot(a)}
          </button>
          {openId === a.id && (
            <div className="desk-rail-ask" onPointerDown={(e) => e.stopPropagation()}>
              <div className="desk-rail-ask-row">
                <input
                  autoFocus
                  value={input}
                  placeholder="Ask"
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && input.trim()) void run(a.id);
                    if (e.key === "Escape") setOpenId(null);
                  }}
                />
                <button
                  type="button"
                  className="desk-chip"
                  disabled={busyId === a.id || !input.trim()}
                  onClick={() => void run(a.id)}
                >
                  {busyId === a.id ? "…" : "Run"}
                </button>
              </div>
              {output && (
                <>
                  <pre className="desk-pullout-md">{output}</pre>
                  <button type="button" className="desk-chip quiet" onClick={() => void copy()}>
                    {copied ? "Copied" : "Copy"}
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
