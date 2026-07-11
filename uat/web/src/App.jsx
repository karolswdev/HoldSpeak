import React, { useEffect, useState } from "react";
import { useStore } from "./store.js";
import { Sitting } from "./Sitting.jsx";
import { formFactorLabel, targetLabel } from "./targets.js";

function CoveragePills({ coverage }) {
  if (!coverage) return null;
  const cell = (label, c) => (
    <span className="pill mono" key={label}>
      {label} {c.covered}/{c.total} · {c.pct}%
    </span>
  );
  const walk = (value, prefix = "") => Object.entries(value || {}).flatMap(([key, item]) => {
    const label = prefix ? `${prefix} · ${key}` : key;
    if (item && Number.isFinite(item.covered) && Number.isFinite(item.total)) {
      return [[item.label || (label === "overall" ? "all" : label.replaceAll("_", " ")), item]];
    }
    return item && typeof item === "object" ? walk(item, label) : [];
  });
  const entries = walk(coverage);
  return (
    <div className="cov">
      {entries.map(([label, value]) => cell(label, value))}
    </div>
  );
}

function RequiredTargets({ targets }) {
  if (!targets?.length) return null;
  return (
    <div className="required-targets" aria-label="Required implementations">
      <strong>Required implementations</strong>
      <div className="pack-facts">
        {targets.map((item, index) => {
          const target = typeof item === "string" ? item : item.target;
          const formFactor = typeof item === "object" ? item.form_factor : null;
          const formFactors = typeof item === "object" ? item.form_factors : null;
          return (
            <span className="pill target-pill" key={`${target}-${formFactor || index}`}>
              {targetLabel(target)}
              {formFactor ? ` · ${formFactorLabel(formFactor)}` : ""}
              {formFactors?.length ? ` · ${formFactors.map(formFactorLabel).join(", ")}` : ""}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function Home() {
  const { packs, sittings, start, open, busy } = useStore();
  const [deviceMode, setDeviceMode] = useState(false);
  const campaigns = packs.filter((pack) => pack.is_campaign);
  const referencePacks = packs.filter((pack) => !pack.is_campaign);

  const packCard = (p) => (
    <div className={`card ${p.quarantined ? "" : "click"} ${p.is_campaign ? "campaign-card" : ""}`} key={p.pack} onClick={() => !busy && !p.quarantined && start(p.pack, null, deviceMode || p.requires_device)} role="button">
      <div className="card-row">
        <div>
          <div className="pack-kicker">{p.is_campaign ? `${p.tier} functional pass` : "reference pack"}</div>
          <h2 style={{ marginBottom: 4 }}>{p.title || p.pack}</h2>
          {p.purpose && <div className="pack-purpose">{p.purpose}</div>}
          <div className="pack-facts">
            {p.estimated_minutes > 0 && <span className="pill">about {p.estimated_minutes} min</span>}
            <span className="pill">{p.scenario_count} scenarios</span>
            <span className="pill">{p.expected_verdicts} observations</span>
            {p.requires_intel && <span className="pill">.43 treatment</span>}
            {p.requires_device && <span className="pill">native device</span>}
          </div>
          <RequiredTargets targets={p.required_targets} />
        </div>
        <button className="primary" disabled={busy || p.quarantined}>{p.quarantined ? "Quarantined" : "Start →"}</button>
      </div>
      {p.is_campaign && p.bootstrap && (
        <div className="bootstrap-line">
          <strong>Bootstrap</strong>
          <span>{p.bootstrap.automatic} automatic</span>
          <span>{p.bootstrap.assisted} assisted</span>
          <span>{p.bootstrap.manual} hands-on</span>
        </div>
      )}
      {p.quarantined && <div className="banner err">Exact Swift implementation unresolved. Classify the installed root before this pack can produce evidence.</div>}
      {p.prerequisites?.length > 0 && (
        <details className="pack-prereqs" onClick={(event) => event.stopPropagation()}>
          <summary>Preflight ({p.prerequisites.length})</summary>
          <ul>{p.prerequisites.map((item, index) => <li key={index}>{item}</li>)}</ul>
        </details>
      )}
      {p.exit_gate?.length > 0 && (
        <details className="pack-prereqs" onClick={(event) => event.stopPropagation()}>
          <summary>Move-on gate</summary>
          <ul>{p.exit_gate.map((item, index) => <li key={index}>{item}</li>)}</ul>
        </details>
      )}
      <CoveragePills coverage={p.coverage} />
    </div>
  );

  return (
    <div>
      <h1>Run the functional verification</h1>
      <p className="sub">Start with phase 1 and work downward. Each phase says what is pre-seeded, what needs your hands, and when to stop for triage.</p>

      <div className={`card device-mode ${deviceMode ? "selected" : ""}`}>
        <label>
          <input
            type="checkbox"
            checked={deviceMode}
            onChange={(event) => setDeviceMode(event.target.checked)}
          />
          <span>
            <strong>Device sitting</strong>
            <span className="muted">LAN-bind the product and issue a per-run pairing URL/token for iPhone or iPad.</span>
          </span>
        </label>
        {deviceMode && (
          <div className="banner info">
            Start the conductor with <span className="mono">UAT_HOST=0.0.0.0</span>, then open this site on the device. The product run will be LAN-bound too.
          </div>
        )}
      </div>

      {packs.length === 0 && <div className="empty">No packs found.</div>}
      {campaigns.map(packCard)}

      {referencePacks.length > 0 && <h3>Reference and diagnostic packs</h3>}
      {referencePacks.map(packCard)}

      <h3>Past sittings</h3>
      {sittings.length === 0 && <div className="muted">None yet.</div>}
      {sittings.map((s) => (
        <div className="card click" key={s.id} onClick={() => open(s.id)} role="button">
          <div className="card-row">
            <div>
              <strong>{s.pack}</strong>{" "}
              <span className="muted mono">{s.id}</span>
              <div className="muted mono">{s.status} · {s.verdicts_cast} verdicts · {s.created_at}</div>
              {s.legacy_invalid && <div className="legacy-tag">legacy protocol · review only</div>}
            </div>
            <button className="ghost sm">{["done", "aborted"].includes(s.status) || s.legacy_invalid ? "Review" : "Resume"} →</button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const { view, error, loadHome, open, setError } = useStore();

  useEffect(() => {
    const sittingId = new URLSearchParams(window.location.search).get("sitting");
    if (sittingId) open(sittingId);
    else loadHome();
  }, [loadHome, open]);

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
