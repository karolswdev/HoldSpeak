import React, { useEffect } from "react";
import { useStore } from "./store.js";
import { Sitting } from "./Sitting.jsx";

function CoveragePills({ coverage }) {
  if (!coverage) return null;
  const cell = (label, c) => (
    <span className="pill mono" key={label}>
      {label} {c.covered}/{c.total} · {c.pct}%
    </span>
  );
  return (
    <div className="cov">
      {cell("all", coverage.overall)}
      {cell("web", coverage.web)}
      {cell("iPad", coverage.ipad)}
      {cell("iPhone", coverage.iphone)}
    </div>
  );
}

function Home() {
  const { packs, sittings, start, open, busy } = useStore();
  return (
    <div>
      <h1>Choose a pack</h1>
      <p className="sub">Pick a pack. The rig stages the world, then walks you through it beat by beat.</p>

      {packs.length === 0 && <div className="empty">No packs found.</div>}
      {packs.map((p) => (
        <div className="card click" key={p.pack} onClick={() => !busy && start(p.pack)} role="button">
          <div className="card-row">
            <div>
              <h2 style={{ marginBottom: 4 }}>{p.pack}</h2>
              <div className="muted mono">{p.scenario_count} scenarios · {p.expected_verdicts} verdicts</div>
            </div>
            <button className="primary" disabled={busy}>Start sitting →</button>
          </div>
          <CoveragePills coverage={p.coverage} />
        </div>
      ))}

      <h3>Past sittings</h3>
      {sittings.length === 0 && <div className="muted">None yet.</div>}
      {sittings.map((s) => (
        <div className="card click" key={s.id} onClick={() => open(s.id)} role="button">
          <div className="card-row">
            <div>
              <strong>{s.pack}</strong>{" "}
              <span className="muted mono">{s.id}</span>
              <div className="muted mono">{s.status} · {s.verdicts_cast} verdicts · {s.created_at}</div>
            </div>
            <button className="ghost sm">{s.status === "done" ? "Review" : "Resume"} →</button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const { view, error, loadHome, setError } = useStore();

  useEffect(() => {
    loadHome();
  }, [loadHome]);

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">
          <span className="dot" /> HoldSpeak UAT
        </div>
        <div className="crumbs">{view === "home" ? "the rig" : "sitting"}</div>
      </div>

      {error && (
        <div className="banner err">
          {error} <button className="ghost sm right" onClick={() => setError(null)}>dismiss</button>
        </div>
      )}

      {view === "home" && <Home />}
      {view === "sitting" && <Sitting />}
    </div>
  );
}
