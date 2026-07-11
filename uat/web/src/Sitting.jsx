import React, { useEffect, useRef, useState } from "react";
import { useStore, currentStep, verdictFor } from "./store.js";
import { Recorder, micSupported } from "./record.js";
import { formFactorLabel, isWebSlot, matchingDeviceSession, slotLabel, targetLabel } from "./targets.js";

const VERDICTS = ["pass", "fail", "partial", "observe", "skip"];

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

function nativeRequirements(sitting) {
  const byPair = new Map();
  for (const scenario of sitting?.scenarios || []) {
    for (const step of scenario.steps || []) {
      for (const slot of step.execution_slots || []) {
        if (slot.native) byPair.set(`${slot.target}|${slot.form_factor}`, slot);
      }
    }
  }
  return [...byPair.values()];
}

const EMPTY_DEVICE_FORM = {
  target: "",
  form_factor: "",
  device_name: "",
  os_version: "",
  bundle_id: "",
  build_number: "",
  install_source: "",
  pairing_verified: false,
};

function DeviceAttestationPanel() {
  const sitting = useStore((state) => state.sitting);
  const { registerDeviceSession } = useStore();
  const requirements = nativeRequirements(sitting);
  const [form, setForm] = useState(EMPTY_DEVICE_FORM);
  const [saving, setSaving] = useState(false);
  const run = sitting?.run;

  useEffect(() => {
    if (!requirements.length) return;
    const pairExists = requirements.some((slot) =>
      slot.target === form.target && slot.form_factor === form.form_factor
    );
    if (!pairExists) {
      setForm((current) => ({
        ...current,
        target: requirements[0].target,
        form_factor: requirements[0].form_factor,
      }));
    }
  }, [requirements.map((slot) => `${slot.target}|${slot.form_factor}`).join(",")]); // eslint-disable-line

  if (!requirements.length) return null;

  const targetOptions = [...new Set(requirements.map((slot) => slot.target))];
  const formFactorOptions = requirements
    .filter((slot) => slot.target === form.target)
    .map((slot) => slot.form_factor);
  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await registerDeviceSession(form);
      setForm((current) => ({
        ...EMPTY_DEVICE_FORM,
        target: current.target,
        form_factor: current.form_factor,
      }));
    } catch (_) {
      // The store exposes the API error in the global error banner.
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card device-attestation">
      <div className="card-row">
        <div>
          <h2 style={{ marginBottom: 3 }}>Native device attestation</h2>
          <div className="muted">Native verdicts unlock only for the exact Swift app and device form factor registered here.</div>
        </div>
        <span className="pill">{sitting.device_sessions?.filter((session) => session.pairing_verified).length || 0} verified</span>
      </div>
      <div className="required-device-list">
        {requirements.map((slot) => {
          const matched = matchingDeviceSession(slot, sitting.device_sessions);
          return (
            <div className="device-requirement" key={`${slot.target}|${slot.form_factor}`}>
              <span className={`dot-status ${matched ? "ok" : "bad"}`} />
              <span>{targetLabel(slot.target)} · {formFactorLabel(slot.form_factor)}</span>
              <span className="muted right">{matched ? `verified on ${matched.device_name}` : "locked"}</span>
            </div>
          );
        })}
      </div>
      {run?.lan ? (
        <div className="banner info">
          Pair this exact isolated run: {" "}
          <a className="linkbtn mono" href={run.pairing?.url || "#"} target="_blank" rel="noreferrer">
            {run.pairing?.url || "pairing URL unavailable"}
          </a>
        </div>
      ) : (
        <div className="banner err">This sitting is not LAN-bound. Pairing must still be verified before a native attestation can unlock verdicts.</div>
      )}

      <form className="attestation-form" onSubmit={submit}>
        <label>
          Swift app
          <select
            required
            value={form.target}
            onChange={(event) => {
              const target = event.target.value;
              const firstFactor = requirements.find((slot) => slot.target === target)?.form_factor || "";
              setForm((current) => ({ ...current, target, form_factor: firstFactor }));
            }}
          >
            {targetOptions.map((target) => <option key={target} value={target}>{targetLabel(target)}</option>)}
          </select>
        </label>
        <label>
          Form factor
          <select required value={form.form_factor} onChange={(event) => update("form_factor", event.target.value)}>
            {formFactorOptions.map((factor) => <option key={factor} value={factor}>{formFactorLabel(factor)}</option>)}
          </select>
        </label>
        <label>Device name<input required value={form.device_name} onChange={(event) => update("device_name", event.target.value)} placeholder="Karol's iPad" /></label>
        <label>OS version<input required value={form.os_version} onChange={(event) => update("os_version", event.target.value)} placeholder="iPadOS 19.0" /></label>
        <label>Bundle ID<input required className="mono" value={form.bundle_id} onChange={(event) => update("bundle_id", event.target.value)} placeholder="dev.holdspeak…" /></label>
        <label>Build number<input required className="mono" value={form.build_number} onChange={(event) => update("build_number", event.target.value)} placeholder="42" /></label>
        <label>Install source<input required value={form.install_source} onChange={(event) => update("install_source", event.target.value)} placeholder="Xcode, TestFlight, App Store…" /></label>
        <label className="pairing-check">
          <input type="checkbox" checked={form.pairing_verified} onChange={(event) => update("pairing_verified", event.target.checked)} />
          <span><strong>Pairing verified</strong><span className="muted">I confirmed this installed app is connected to this sitting.</span></span>
        </label>
        <button className="primary" type="submit" disabled={saving}>{saving ? "registering…" : "Register device session"}</button>
      </form>
    </div>
  );
}

function ManualSetup({ scenario }) {
  const { confirmStaged } = useStore();
  if (!scenario.manual_setup || scenario.manual_setup.length === 0) return null;
  const assisted = scenario.recipes && scenario.recipes.length > 0;
  return (
    <div className="card" style={{ borderColor: "var(--partial)" }}>
      <h2>{assisted ? "Finish the real-world preflight" : "Stage this hands-on boundary"}</h2>
      <p className="muted" style={{ marginTop: 0 }}>
        {assisted
          ? "The product world is verified. Complete only the physical/device/audio facts below, then continue."
          : "This behavior starts outside the harness. Complete the facts below on the real product, then continue."}
      </p>
      <ol style={{ margin: "0 0 12px", paddingLeft: 20 }}>
        {scenario.manual_setup.map((s, i) => (
          <li key={i} style={{ marginBottom: 6 }}>{s}</li>
        ))}
      </ol>
      <button className="primary" onClick={() => confirmStaged(scenario.id)}>Preflight complete — continue →</button>
    </div>
  );
}

function StagingPanel({ scenario, staging }) {
  const { retryStage, setView, busy } = useStore();
  const manualOnly = (!scenario.recipes || scenario.recipes.length === 0) && scenario.manual_setup?.length;
  if (manualOnly) {
    return <ManualSetup scenario={scenario} />;
  }
  if (!staging) {
    return (
      <div className="card">
        <h2>Staging the world…</h2>
        <div className="staging-line"><span className="dot-status run" /> booting an isolated run and applying {scenario.recipes.join(", ")}</div>
        <div className="muted" style={{ marginTop: 8 }}>
          Recipes that run meeting intelligence or mesh probes can take several minutes. The current recipe names above are the active work; a verified result or a log-backed failure will replace this panel.
        </div>
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
      {staging.ok && scenario.manual_setup?.length > 0 && (
        <div style={{ marginTop: 12 }}><ManualSetup scenario={scenario} /></div>
      )}
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

function ExecutionSlotCard({ scenario, step, slot, productUp }) {
  const { sitting, cast, uploadShot } = useStore();
  const existing = verdictFor(sitting, scenario.id, step.index, slot.id);
  const deviceSession = matchingDeviceSession(slot, sitting.device_sessions);
  const locked = slot.native && !deviceSession;
  const [note, setNote] = useState(existing?.note || "");
  const [measurements, setMeasurements] = useState(existing?.measurements || {});
  const [shot, setShot] = useState(existing?.shot_path || null);
  const [uploading, setUploading] = useState(false);
  const [startedAt] = useState(() => new Date().toISOString());

  useEffect(() => {
    setNote(existing?.note || "");
    setMeasurements(existing?.measurements || {});
    setShot(existing?.shot_path || null);
  }, [existing?.verdict, scenario.id, step.index, slot.id]); // eslint-disable-line

  const verdictPayload = (verdict, overrides = {}) => ({
    scenario_id: scenario.id,
    step_index: step.index,
    slot_id: slot.id,
    verdict,
    note,
    shot_path: shot,
    started_at: startedAt,
    measurements,
    ...(slot.native ? { device_session_id: deviceSession?.id || deviceSession?.device_session_id } : {}),
    ...overrides,
  });

  const pick = (verdict) => {
    if (!locked) cast(verdictPayload(verdict));
  };

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { shot_path } = await uploadShot(scenario.id, step.index, slot.id, file);
      setShot(shot_path);
      if (existing) {
        // Persist the path returned by this upload. Calling pick() here would
        // close over the previous React state and silently keep the old path.
        await cast(verdictPayload(existing.verdict, { shot_path }));
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={`execution-slot ${existing ? "answered" : ""} ${locked ? "locked" : ""}`}>
      <div className="slot-head">
        <div>
          <div className={`slot-kind ${slot.native ? "native" : isWebSlot(slot) ? "web" : "local"}`}>{slotLabel(slot)}</div>
          <div className="slot-implementation">{targetLabel(slot.target)} · {formFactorLabel(slot.form_factor)}</div>
          <div className="muted mono slot-id">slot: {slot.id}</div>
        </div>
        {existing && <span className="pill">cast: {existing.verdict}</span>}
      </div>
      {locked && (
        <div className="banner err slot-lock">
          Locked: register a pairing-verified {targetLabel(slot.target)} session on {formFactorLabel(slot.form_factor)} above.
        </div>
      )}
      {slot.native && deviceSession && (
        <div className="verified-device">✓ {deviceSession.device_name} · {deviceSession.os_version} · build {deviceSession.build_number}</div>
      )}
      <div className="verdict-buttons">
        {VERDICTS.map((v) => (
          <button
            key={v}
            className={`vb ${v} ${existing?.verdict === v ? "sel" : ""}`}
            onClick={() => pick(v)}
            disabled={locked}
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
        disabled={locked}
      />
      {step.measurements?.length > 0 && (
        <fieldset className="measurement-fields">
          <legend>Raw measurements</legend>
          {step.measurements.map((measurement) => (
            <label key={measurement.key}>
              <span>
                {measurement.label}
                {measurement.required ? " *" : ""}
              </span>
              <span className="measurement-input">
                <input
                  value={measurements[measurement.key] || ""}
                  onChange={(event) => setMeasurements((current) => ({
                    ...current,
                    [measurement.key]: event.target.value,
                  }))}
                  onBlur={() => existing && pick(existing.verdict)}
                  disabled={locked}
                  aria-required={measurement.required}
                />
                {measurement.unit ? <small>{measurement.unit}</small> : null}
              </span>
            </label>
          ))}
        </fieldset>
      )}
      <div className="shot-row">
        <MicButton
          productUp={productUp && !locked}
          onText={(text) => {
            const merged = note ? `${note} ${text}`.trim() : text;
            setNote(merged);
            if (existing) cast(verdictPayload(existing.verdict, { note: merged }));
          }}
        />
        <label className={`linkbtn ${locked ? "disabled-control" : ""}`} style={{ cursor: locked ? "not-allowed" : "pointer" }}>
          {shot ? "Replace screenshot" : "Attach screenshot"}
          <input disabled={locked} type="file" accept="image/*" style={{ display: "none" }} onChange={onFile} />
        </label>
        {uploading && <span className="muted">uploading…</span>}
        {shot && <span className="muted mono">{shot.split("/").slice(-1)[0]}</span>}
      </div>
    </div>
  );
}

function Walkthrough({ scenario }) {
  const { sitting } = useStore();
  const step = currentStep(sitting, scenario);

  if (!step) {
    return (
      <div className="card">
        <div className="banner info">Scenario complete. Moving on…</div>
      </div>
    );
  }

  const run = sitting.run;
  const slots = step.execution_slots || [];
  const hasWebProduct = slots.some(isWebSlot);
  const nativeTargets = [...new Set(slots.filter((slot) => slot.native).map((slot) => slot.target))];
  return (
    <div>
      <div className="card-row" style={{ marginBottom: 10 }}>
        <div>
          <div className="muted mono">{scenario.pack} · {scenario.id} · step {step.index + 1}/{scenario.steps.length}</div>
          <h2 style={{ margin: "4px 0 0" }}>{scenario.title}</h2>
        </div>
        <div className="btn-row">
          {hasWebProduct && (
            <a className="linkbtn" href={productUrl(run, step.where)} target="_blank" rel="noreferrer">Open React Desk (web) ↗</a>
          )}
          {nativeTargets.map((target) => (
            <span className="pill native-app-label" key={target}>Use {targetLabel(target)}</span>
          ))}
        </div>
      </div>

      <div className="card">
        <p className="step-do">{step.do}</p>
        <p className="step-expect">Expect: {step.expect}</p>
        <div className="step-meta">
          {step.where && <span>→ {step.where}</span>}
          <span>scenario target: {targetLabel(scenario.execution_target)}</span>
          <span>execution slots: {slots.map((slot) => slot.id).join(", ") || "none"}</span>
        </div>

        {slots.length === 0 && (
          <div className="banner err">This step has no execution slots. The protocol is invalid and cannot earn acceptance coverage.</div>
        )}
        <div className="execution-slots">
          {slots.map((slot) => (
            <ExecutionSlotCard key={slot.id} scenario={scenario} step={step} slot={slot} productUp={run?.status === "up"} />
          ))}
        </div>
      </div>
    </div>
  );
}

function TransitionPanel({ transition }) {
  const { runAfter, busy } = useStore();
  return (
    <div className="card" style={{ borderColor: "var(--fail)" }}>
      <h2>State transition needs attention</h2>
      <p className="muted">
        The verdicts are safe, but the conductor could not establish the world
        required by the next beat. Progress is blocked so the next expectation
        cannot be judged against the wrong state.
      </p>
      <div className="mono">
        {transition.scenario_id} · step {transition.step_index + 1} · {transition.status}
      </div>
      {transition.error && <div className="banner err">{transition.error}</div>}
      <div className="log">{JSON.stringify(transition.actions || [], null, 2)}</div>
      <button
        className="primary"
        disabled={busy}
        onClick={() => runAfter(transition.scenario_id, transition.step_index)}
      >
        {busy ? "retrying…" : "Retry transition"}
      </button>
    </div>
  );
}

const TRIAGE_STATES = ["untriaged", "fix", "wont-fix", "by-design", "duplicate"];

function FindingCard({ finding }) {
  const { triage } = useStore();
  const [disposition, setDisposition] = useState(finding.disposition || "");
  return (
    <div className="surface" style={{ marginBottom: 10 }}>
      <div className="surface-head">
        <span className="mono">{finding.id}</span>
        <span className="pill" style={{ color: finding.verdict === "fail" ? "var(--fail)" : finding.verdict === "observe" ? "var(--observe)" : "var(--partial)" }}>
          {finding.verdict} · {finding.slot_id || finding.surface}
        </span>
      </div>
      <div style={{ marginBottom: 6 }}>{finding.title}</div>
      {finding.note && <div className="muted" style={{ marginBottom: 6 }}>“{finding.note}”</div>}
      {(finding.cross_slot?.is_split || finding.cross_surface?.is_split) && (
        <div className="banner info" style={{ margin: "6px 0" }}>
          Implementation split — passed on {(finding.cross_slot || finding.cross_surface).passed_on.join(", ")}, {finding.verdict} on {finding.slot_id || finding.surface}.
        </div>
      )}
      <textarea
        className="note-field"
        placeholder="Disposition — why fix, defer, by-design, or duplicate?"
        value={disposition}
        onChange={(event) => setDisposition(event.target.value)}
      />
      <div className="btn-row" style={{ marginTop: 8 }}>
        {TRIAGE_STATES.map((state) => (
          <button
            key={state}
            className={`sm ${finding.triage_state === state ? "primary" : "ghost"}`}
            onClick={() => triage(finding.id, state, disposition)}
          >
            {state}
          </button>
        ))}
      </div>
    </div>
  );
}

function DebriefPanel() {
  const { debrief, backlog, loadBacklog } = useStore();
  if (!debrief) return null;
  const findings = debrief.findings || [];
  return (
    <div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Findings ({findings.length})</h3>
        {findings.length === 0 && <div className="muted">No acceptance misses or observations were recorded.</div>}
        {findings.map((finding) => <FindingCard key={finding.id} finding={finding} />)}
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

function coverageCells(coverage, prefix = "") {
  const cells = [];
  for (const [key, value] of Object.entries(coverage || {})) {
    const label = prefix ? `${prefix} · ${key}` : key;
    if (value && Number.isFinite(value.covered) && Number.isFinite(value.total)) {
      cells.push([label, value]);
    } else if (value && typeof value === "object") {
      cells.push(...coverageCells(value, label));
    }
  }
  return cells;
}

function slotNameMap(sitting) {
  const names = new Map();
  for (const scenario of sitting.scenarios || []) {
    for (const step of scenario.steps || []) {
      for (const slot of step.execution_slots || []) names.set(slot.id, slotLabel(slot));
    }
  }
  return names;
}

function SittingEnd({ reviewOnly = false }) {
  const { sitting, finish, setView, loadHome, debrief } = useStore();
  const [done, setDone] = useState(sitting.status === "done");
  const superseded = sitting.status === "aborted";
  const closedReview = reviewOnly || superseded;
  const cov = sitting.coverage;
  const slotNames = slotNameMap(sitting);

  const scoreBySlot = {};
  for (const v of sitting.verdicts) {
    const key = v.slot_id || `legacy:${v.surface || "unknown"}`;
    scoreBySlot[key] = scoreBySlot[key] || { pass: 0, fail: 0, partial: 0, observe: 0, skip: 0 };
    scoreBySlot[key][v.verdict] = (scoreBySlot[key][v.verdict] || 0) + 1;
  }

  return (
    <div>
      <h1>{reviewOnly ? "Legacy sitting — review only" : superseded ? "Superseded sitting — evidence preserved" : "Sitting complete"}</h1>
      <p className="sub">
        {reviewOnly
          ? "This sitting used the ambiguous surface protocol. Its evidence is preserved, but it cannot be resumed, finished, or counted as implementation-specific acceptance."
          : superseded
            ? "Feedback from this protocol snapshot remains immutable. Testing restarted from the corrected current protocol."
          : "Every explicit execution slot has a verdict. Here is the implementation-bound tally."}
      </p>

      {reviewOnly && <div className="banner err">No new verdicts can be cast into this sitting. Start a redesigned campaign to collect valid React or Swift evidence.</div>}
      {superseded && <div className="banner info">No new verdicts can be cast here. This is the evidence that caused the protocol or product to change.</div>}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Score per execution slot</h3>
        {Object.keys(scoreBySlot).length === 0 && <div className="muted">No verdicts.</div>}
        {Object.entries(scoreBySlot).map(([slotId, sc]) => (
          <div className="card-row" key={slotId} style={{ padding: "6px 0" }}>
            <div>
              <strong>{slotNames.get(slotId) || slotId}</strong>
              {!slotId.startsWith("legacy:") && <div className="muted mono">{slotId}</div>}
            </div>
            <div className="btn-row">
              <span className="pill" style={{ color: "var(--pass)" }}>{sc.pass || 0} pass</span>
              <span className="pill" style={{ color: "var(--fail)" }}>{sc.fail || 0} fail</span>
              <span className="pill" style={{ color: "var(--partial)" }}>{sc.partial || 0} partial</span>
              <span className="pill" style={{ color: "var(--observe)" }}>{sc.observe || 0} observe</span>
              <span className="pill">{sc.skip || 0} skip</span>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Coverage</h3>
        <div className="cov">
          {coverageCells(cov).map(([label, value]) => (
            <span className="pill mono" key={label}>{label.replaceAll("_", " ")} {value.covered}/{value.total} · {value.pct}%</span>
          ))}
          {coverageCells(cov).length === 0 && <span className="muted">No valid coverage summary.</span>}
        </div>
      </div>

      <div className="btn-row">
        {!closedReview && !done && (
          <button className="primary" onClick={async () => { await finish(); setDone(true); }}>
            Finish sitting
          </button>
        )}
        {done && <span className="pill" style={{ color: "var(--pass)" }}>sitting recorded</span>}
        {reviewOnly && <span className="pill" style={{ color: "var(--partial)" }}>legacy evidence preserved</span>}
        {superseded && <span className="pill" style={{ color: "var(--observe)" }}>feedback evidence preserved</span>}
        <button className="ghost" onClick={() => { loadHome(); setView("home"); }}>Back to home</button>
      </div>
      {debrief && <div className="banner info" style={{ marginTop: 12 }}>Recorded debrief (md + json under the run's <span className="mono">debrief/</span> dir). Review the findings and triage below — this is where we decide what to fix.</div>}
      {debrief && <div className="spacer" />}
      {debrief && <DebriefPanel />}
    </div>
  );
}

export function Sitting() {
  const { sitting, ensureStaged, staging, stagedIds, refresh } = useStore();
  const resume = sitting?.resume;
  // A finished sitting is always in REVIEW mode (even if some slots went
  // unanswered); only an in-progress sitting resumes the walkthrough.
  const legacyReview = sitting?.legacy_invalid === true;
  const reviewing = ["done", "aborted"].includes(sitting?.status) || legacyReview;

  const confirmedIds = useStore((s) => s.confirmedIds);
  const scenario = !reviewing && resume ? sitting.scenarios.find((s) => s.id === resume.scenario_id) : null;
  const hasRecipes = (scenario?.recipes?.length || 0) > 0;
  const needsConfirm = (scenario?.manual_setup?.length || 0) > 0;
  const serverStage = scenario
    ? sitting?.stages?.find((stage) => stage.scenario_id === scenario.id)
    : null;

  useEffect(() => {
    // Only auto-stage when there's a recipe to apply; a manual-setup protocol is
    // staged by hand (the person confirms in the panel).
    if (scenario && hasRecipes && serverStage?.status !== "done" && !stagedIds[scenario.id]) {
      ensureStaged(scenario.id);
    }
  }, [scenario?.id, hasRecipes, serverStage?.status, ensureStaged, stagedIds]); // eslint-disable-line

  useEffect(() => {
    if (!sitting || ["done", "aborted"].includes(sitting.status) || sitting.legacy_invalid) return undefined;
    const timer = window.setInterval(() => refresh(), 2000);
    return () => window.clearInterval(timer);
  }, [sitting?.id, sitting?.status, refresh]);

  if (!sitting) return <div className="empty">Loading…</div>;
  if (reviewing) return <SittingEnd reviewOnly={legacyReview} />;
  if (sitting.blocked_transition) {
    return (
      <div>
        <ProgressStrip />
        <DeviceAttestationPanel />
        <TransitionPanel transition={sitting.blocked_transition} />
      </div>
    );
  }
  if (!resume) return <SittingEnd />;

  const autoStaged = hasRecipes
    ? serverStage?.status === "done" || !!stagedIds[scenario.id]
    : true;
  const manualConfirmed = !!serverStage?.manual_confirmed || !!confirmedIds[scenario.id];
  const ready = autoStaged && (!needsConfirm || manualConfirmed);
  return (
    <div>
      <ProgressStrip />
      <DeviceAttestationPanel />
      {!ready ? (
        <StagingPanel scenario={scenario} staging={staging} />
      ) : (
        <Walkthrough scenario={scenario} />
      )}
    </div>
  );
}
