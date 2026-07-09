import React, { useEffect, useRef, useState } from "react";
import { useStore, currentStep, stepAnswered, verdictFor } from "./store.js";
import { Recorder, micSupported } from "./record.js";

const VERDICTS = ["pass", "fail", "partial", "skip"];

// Speak-to-fill mic — rides the product's own transcribe route. Present only
// when the browser supports capture AND the product under test is up; honestly
// absent (or an inline error) otherwise.
function MicButton({ productUp, onText }) {
  const { transcribeNote } = useStore();
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const recRef = useRef(null);

  if (!micSupported() || !productUp) return null;

  const toggle = async () => {
    setErr(null);
    if (!recording) {
      try {
        recRef.current = new Recorder();
        await recRef.current.start();
        setRecording(true);
      } catch (e) {
        setErr("mic blocked");
      }
      return;
    }
    setRecording(false);
    setBusy(true);
    try {
      const wav = await recRef.current.stop();
      const res = await transcribeNote(wav);
      if (res.ok) onText(res.text || "");
      else setErr(res.error || "voice unavailable");
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <span className="shot-row" style={{ marginTop: 0 }}>
      <button type="button" className={`sm ${recording ? "primary" : "ghost"}`} onClick={toggle} disabled={busy}>
        {recording ? "◉ stop & fill" : busy ? "transcribing…" : "🎤 speak"}
      </button>
      {err && <span className="muted" style={{ color: "var(--partial)" }}>{err}</span>}
    </span>
  );
}

function productUrl(run, where) {
  if (!run || !run.pairing) return "#";
  const raw = run.pairing.url || "";
  const [base, query] = raw.split("?");
  const path = where || "";
  return base.replace(/\/$/, "") + path + (query ? `?${query}` : "");
}

function ProgressStrip() {
  const sitting = useStore((s) => s.sitting);
  const p = sitting.progress;
  const pct = p.expected ? Math.round((100 * p.cast) / p.expected) : 0;
  return (
    <div className="progress-strip">
      <div className="bar">
        <span style={{ width: `${pct}%` }} />
      </div>
      <div className="count">{p.cast}/{p.expected}</div>
    </div>
  );
}

function StagingPanel({ scenario, staging }) {
  const { retryStage, setView, busy } = useStore();
  if (!staging) {
    return (
      <div className="card">
        <h2>Staging the world…</h2>
        <div className="staging-line"><span className="dot-status run" /> booting an isolated run and applying {scenario.recipes.join(", ")}</div>
      </div>
    );
  }
  return (
    <div className="card">
      <h2>{staging.ok ? "World staged" : "Staging failed"}</h2>
      {staging.staging?.map((s, i) => (
        <div className="staging-line" key={i}>
          <span className={`dot-status ${s.ok ? "ok" : "bad"}`} />
          <span className="mono">{s.recipe}</span>
          <span className="muted right">{s.ok ? "verified" : "failed"}</span>
        </div>
      ))}
      {!staging.ok && (
        <>
          <div className="banner err">
            {staging.staging?.find((s) => !s.ok)?.error || "The world could not be staged."}
          </div>
          {(() => {
            const failed = staging.staging?.find((s) => s.log_tail);
            return failed ? <div className="log">{failed.log_tail.stderr || failed.log_tail.stdout || "(no log)"}</div> : null;
          })()}
          <div className="btn-row" style={{ marginTop: 12 }}>
            <button className="primary" disabled={busy} onClick={() => retryStage(scenario.id)}>Retry</button>
            <button className="ghost" onClick={() => setView("home")}>Abort to home</button>
          </div>
        </>
      )}
    </div>
  );
}

function SurfaceCard({ scenario, step, surface, meta, productUp }) {
  const { sitting, cast, uploadShot } = useStore();
  const existing = verdictFor(sitting, scenario.id, step.index, surface);
  const [note, setNote] = useState(existing?.note || "");
  const [shot, setShot] = useState(existing?.shot_path || null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    setNote(existing?.note || "");
    setShot(existing?.shot_path || null);
  }, [existing?.verdict, scenario.id, step.index, surface]); // eslint-disable-line

  if (!meta.applicable) {
    return (
      <div className="surface na">
        <div className="surface-head">
          <span className="surface-name">{surface}</span>
          <span className="pill">n/a</span>
        </div>
        <div className="na-reason">{meta.reason}</div>
      </div>
    );
  }

  const pick = (v) =>
    cast({ scenario_id: scenario.id, step_index: step.index, surface, verdict: v, note, shot_path: shot });

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { shot_path } = await uploadShot(scenario.id, step.index, surface, file);
      setShot(shot_path);
      if (existing) pick(existing.verdict); // persist the shot onto the cast verdict
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={`surface ${existing ? "answered" : ""}`}>
      <div className="surface-head">
        <span className="surface-name">{surface}</span>
        {existing && <span className={`pill`}>cast: {existing.verdict}</span>}
      </div>
      <div className="verdict-buttons">
        {VERDICTS.map((v) => (
          <button
            key={v}
            className={`vb ${v} ${existing?.verdict === v ? "sel" : ""}`}
            onClick={() => pick(v)}
          >
            {v}
          </button>
        ))}
      </div>
      <textarea
        className="note-field"
        placeholder="Note (what you saw) — type or speak…"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        onBlur={() => existing && pick(existing.verdict)}
      />
      <div className="shot-row">
        <MicButton
          productUp={productUp}
          onText={(text) => {
            const merged = note ? `${note} ${text}`.trim() : text;
            setNote(merged);
            if (existing) cast({ scenario_id: scenario.id, step_index: step.index, surface, verdict: existing.verdict, note: merged, shot_path: shot });
          }}
        />
        <label className="linkbtn" style={{ cursor: "pointer" }}>
          {shot ? "Replace screenshot" : "Attach screenshot"}
          <input type="file" accept="image/*" style={{ display: "none" }} onChange={onFile} />
        </label>
        {uploading && <span className="muted">uploading…</span>}
        {shot && <span className="muted mono">{shot.split("/").slice(-1)[0]}</span>}
      </div>
    </div>
  );
}

function Walkthrough({ scenario }) {
  const { sitting, runAfter } = useStore();
  const step = currentStep(sitting, scenario);
  const [startedAt] = useState(() => Date.now());

  // When the current step is fully answered and has mid-run actions, run them.
  useEffect(() => {
    if (!step) return;
    if (step.after?.length && stepAnswered(sitting, scenario, step)) {
      runAfter(scenario.id, step.index);
    }
  }, [sitting, scenario, step, runAfter]);

  if (!step) {
    return (
      <div className="card">
        <div className="banner info">Scenario complete. Moving on…</div>
      </div>
    );
  }

  const run = sitting.run;
  const surfaces = step.surfaces;
  return (
    <div>
      <div className="card-row" style={{ marginBottom: 10 }}>
        <div>
          <div className="muted mono">{scenario.pack} · {scenario.id} · step {step.index + 1}/{scenario.steps.length}</div>
          <h2 style={{ margin: "4px 0 0" }}>{scenario.title}</h2>
        </div>
        <a className="linkbtn" href={productUrl(run, step.where)} target="_blank" rel="noreferrer">Open the product ↗</a>
      </div>

      <div className="card">
        <p className="step-do">{step.do}</p>
        <p className="step-expect">Expect: {step.expect}</p>
        <div className="step-meta">
          {step.where && <span>→ {step.where}</span>}
          <span>surfaces: {Object.entries(surfaces).filter(([, v]) => v.applicable).map(([s]) => s).join(", ") || "none"}</span>
        </div>

        <div className="surfaces">
          {["web", "ipad", "iphone"].map((s) => (
            <SurfaceCard key={s} scenario={scenario} step={step} surface={s} meta={surfaces[s]} productUp={run?.status === "up"} />
          ))}
        </div>
      </div>
    </div>
  );
}

const TRIAGE_STATES = ["untriaged", "fix", "wont-fix", "by-design", "duplicate"];

function DebriefPanel() {
  const { debrief, triage, backlog, loadBacklog } = useStore();
  if (!debrief) return null;
  const findings = debrief.findings || [];
  return (
    <div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Findings ({findings.length})</h3>
        {findings.length === 0 && <div className="muted">No non-pass verdicts. Every applicable surface passed.</div>}
        {findings.map((f) => (
          <div key={f.id} className="surface" style={{ marginBottom: 10 }}>
            <div className="surface-head">
              <span className="mono">{f.id}</span>
              <span className={`pill`} style={{ color: f.verdict === "fail" ? "var(--fail)" : "var(--partial)" }}>{f.verdict} · {f.surface}</span>
            </div>
            <div style={{ marginBottom: 6 }}>{f.title}</div>
            {f.note && <div className="muted" style={{ marginBottom: 6 }}>“{f.note}”</div>}
            {f.cross_surface?.is_split && (
              <div className="banner info" style={{ margin: "6px 0" }}>Parity break — passed on {f.cross_surface.passed_on.join(", ")}, {f.verdict} on {f.surface}.</div>
            )}
            <div className="btn-row">
              {TRIAGE_STATES.map((t) => (
                <button key={t} className={`sm ${f.triage_state === t ? "primary" : "ghost"}`} onClick={() => triage(f.id, t, f.disposition)}>{t}</button>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="card-row">
          <h3 style={{ margin: 0 }}>BACKLOG block</h3>
          <button className="ghost sm" onClick={loadBacklog}>Generate</button>
        </div>
        {backlog && <div className="log" style={{ marginTop: 10 }}>{backlog}</div>}
        <div className="muted" style={{ marginTop: 8, fontSize: 13 }}>Triage findings to <span className="mono">fix</span>, then paste this into <span className="mono">pm/roadmap/holdspeak/BACKLOG.md</span> (the commit rides the PMO gate).</div>
      </div>
    </div>
  );
}

function SittingEnd() {
  const { sitting, finish, setView, loadHome } = useStore();
  const [done, setDone] = useState(sitting.status === "done");
  const cov = sitting.coverage;

  const scoreBySurface = {};
  for (const v of sitting.verdicts) {
    scoreBySurface[v.surface] = scoreBySurface[v.surface] || { pass: 0, fail: 0, partial: 0, skip: 0 };
    scoreBySurface[v.surface][v.verdict] = (scoreBySurface[v.surface][v.verdict] || 0) + 1;
  }

  return (
    <div>
      <h1>Sitting complete</h1>
      <p className="sub">Every applicable (step, surface) has a verdict. Here is the tally.</p>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Score per surface</h3>
        {Object.keys(scoreBySurface).length === 0 && <div className="muted">No verdicts.</div>}
        {Object.entries(scoreBySurface).map(([s, sc]) => (
          <div className="card-row" key={s} style={{ padding: "6px 0" }}>
            <strong style={{ textTransform: "capitalize" }}>{s}</strong>
            <div className="btn-row">
              <span className="pill" style={{ color: "var(--pass)" }}>{sc.pass || 0} pass</span>
              <span className="pill" style={{ color: "var(--fail)" }}>{sc.fail || 0} fail</span>
              <span className="pill" style={{ color: "var(--partial)" }}>{sc.partial || 0} partial</span>
              <span className="pill">{sc.skip || 0} skip</span>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Coverage</h3>
        <div className="cov">
          {["overall", "web", "ipad", "iphone"].map((k) => (
            <span className="pill mono" key={k}>{k} {cov[k].covered}/{cov[k].total} · {cov[k].pct}%</span>
          ))}
        </div>
      </div>

      <div className="btn-row">
        {!done && (
          <button className="primary" onClick={async () => { await finish(); setDone(true); }}>
            Finish sitting
          </button>
        )}
        {done && <span className="pill" style={{ color: "var(--pass)" }}>sitting recorded</span>}
        <button className="ghost" onClick={() => { loadHome(); setView("home"); }}>Back to home</button>
      </div>
      {done && <div className="banner info" style={{ marginTop: 12 }}>Debrief packet generated under the run's <span className="mono">debrief/</span> dir (md + json). Triage below.</div>}
      {done && <div className="spacer" />}
      {done && <DebriefPanel />}
    </div>
  );
}

export function Sitting() {
  const { sitting, ensureStaged, staging, stagedIds } = useStore();
  const resume = sitting?.resume;

  const scenario = resume ? sitting.scenarios.find((s) => s.id === resume.scenario_id) : null;

  useEffect(() => {
    if (scenario && !stagedIds[scenario.id]) {
      ensureStaged(scenario.id);
    }
  }, [scenario?.id, ensureStaged, stagedIds]); // eslint-disable-line

  if (!sitting) return <div className="empty">Loading…</div>;
  if (!resume) return <SittingEnd />;

  const staged = stagedIds[scenario.id];
  return (
    <div>
      <ProgressStrip />
      {!staged ? (
        <StagingPanel scenario={scenario} staging={staging} />
      ) : (
        <Walkthrough scenario={scenario} />
      )}
    </div>
  );
}
