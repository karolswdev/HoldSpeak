// Settings > This Mac > Remote access (HS-174-02/03): the credential ledger,
// the issue well and the desk and project grants. Moved out of SettingsCore.tsx.
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Button } from "../../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../../lib/api";
import { humanizeWireValue } from "../../../lib/productLanguage";
import {
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  StringGadget,
  type CycleOption,
} from "../../../desk/surface/gadgets";
import {
  Disclosure,
  countToken,
  StateChip,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
} from "../../../desk/surface";
import { Token } from "../../../desk/surface/Token";
import {
  DESK_GRANT_PALETTES,
  GRANT_WORDS,
  PROJECT_GRANT_PALETTES,
  PROJECT_GRANT_WORDS,
  GrantChip,
  GrantReceiptWell,
  GrantRefusalChip,
  ProjectGrantChip,
  ProjectGrantSummary,
  formatExpiry,
  grantActFrom,
  paletteHolds,
  type Delegation,
  type GrantAct,
  type GrantRefusal,
  type GrantVerbKind,
  type OrphanDelegation,
  type OrphanProjectDelegation,
  type ProjectDelegation,
} from "./grants";

/* ── HS-174-02/03: Remote Access — the credential ledger + issue well ── */

const PALETTE_OPTIONS: CycleOption[] = [
  { value: "PROJECT" },
  { value: "SWEEP" },
  { value: "DESK" },
  { value: "ALL" },
];
const TTL_OPTIONS: CycleOption[] = [
  { value: "43200", label: "12 H" },
  { value: "86400", label: "24 H" },
  { value: "604800", label: "7 D" },
  { value: "2592000", label: "30 D" },
];
type RemoteCredential = {
  id: string;
  identity: string;
  /** Palette name (string like "PROJECT") or resolved tool list. */
  palette: string | string[] | null;
  /** Epoch seconds (converted from monotonic by the server). */
  expires_at: number;
  last_used_at: number | null;
  /** Authoritative active flag from the server. */
  active: boolean;
};


type ProjectFact = { id: string; name: string; is_archived?: boolean | number | null };

type RemoteWire = {
  enabled: boolean;
  bind_host: string | null;
  port: number | null;
  credentials: (RemoteCredential & {
    delegation?: Delegation | null;
    /** One per project with any stored grant row (absent = never granted). */
    project_delegations?: ProjectDelegation[];
  })[];
  /** Grants LIVE in storage whose identity has no credential row. */
  delegations?: OrphanDelegation[];
  /** Project grants LIVE in storage whose identity has no credential row. */
  project_delegations?: OrphanProjectDelegation[];
  active_count: number;
  total_count: number;
};

/** True when the credential has not expired (epoch seconds vs now). */
function isActive(expiresAt: number): boolean {
  return expiresAt * 1000 > Date.now();
}

/** Relative age string from epoch seconds (e.g. `2 H AGO`, `3 D AGO`). */
function relativeAge(epochSeconds: number): string {
  const seconds = Math.max(0, Math.floor((Date.now() - epochSeconds * 1000) / 1000));
  if (seconds < 60) return `${seconds} S AGO`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} M AGO`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} H AGO`;
  return `${Math.floor(seconds / 86400)} D AGO`;
}

/** The palette label: the name when a string, or the first entry when a list. */
function paletteLabel(palette: string | string[] | null): string {
  if (!palette) return "ALL";
  if (typeof palette === "string") return palette;
  if (palette.length === 0) return "ALL";
  return palette[0];
}

export function RemoteAccessModule({
  onEnabledChange,
  grantAct = null,
  receiptOpen = false,
  onGrantAct,
}: {
  /** Report the live enabled state so the parent can update hub chips. */
  onEnabledChange?: (enabled: boolean) => void;
  /** PHILO-7-02: the last grant act's receipt, and whether its well is open
   *  (the footer's receipt Button toggles it; it outlives the row). */
  grantAct?: GrantAct | null;
  receiptOpen?: boolean;
  onGrantAct?: (act: GrantAct) => void;
} = {}) {
  const [wire, setWire] = useState<RemoteWire | null>(null);
  const [loading, setLoading] = useState(true);
  type ReadTarget = "remote" | "projects";
  const [readErrors, setReadErrors] = useState<Partial<Record<ReadTarget, string>>>({});
  const [writeError, setWriteError] = useState<{ action: string; subject: string; message: string } | null>(null);
  const remoteReads = useRef(0);
  const projectReads = useRef(0);
  const writes = useRef(0);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [issueOpen, setIssueOpen] = useState(false);
  const [issueName, setIssueName] = useState("");
  const [issuePalette, setIssuePalette] = useState("PROJECT");
  const [issueTtl, setIssueTtl] = useState("43200");
  const [issuing, setIssuing] = useState(false);
  const [oneTimeToken, setOneTimeToken] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [toggleBusy, setToggleBusy] = useState(false);
  const [granting, setGranting] = useState<string | null>(null);
  const [refusals, setRefusals] = useState<Record<string, GrantRefusal>>({});
  // PHILO-9-07: the projects a credential row can grant, and which rows are open.
  const [projects, setProjects] = useState<ProjectFact[]>([]);
  const [openRows, setOpenRows] = useState<string[]>([]);

  const fetchRemote = useCallback(async () => {
    const order = ++remoteReads.current;
    setLoading(true);
    try {
      const data = await apiFetch<RemoteWire>("/api/settings/remote");
      if (order !== remoteReads.current) return;
      setWire(data);
      setReadErrors((current) => ({ ...current, remote: undefined }));
      onEnabledChange?.(data.enabled);
    } catch (err) {
      if (order === remoteReads.current) setReadErrors((current) => ({ ...current, remote: readableError(err) }));
    } finally {
      if (order === remoteReads.current) setLoading(false);
    }
  }, [onEnabledChange]);

  const fetchProjects = useCallback(async () => {
    const order = ++projectReads.current;
    setProjectsLoading(true);
    try {
      const listed = await apiFetch<{ projects?: ProjectFact[] }>("/api/projects");
      if (order !== projectReads.current) return;
      setProjects((listed?.projects ?? []).filter((project) => !project.is_archived));
      setReadErrors((current) => ({ ...current, projects: undefined }));
    } catch (err) {
      if (order === projectReads.current) setReadErrors((current) => ({ ...current, projects: readableError(err) }));
    } finally {
      if (order === projectReads.current) setProjectsLoading(false);
    }
  }, []);

  // A new explicit writer owns its outcome. Reads never accept or retry it.
  const beginWrite = () => {
    const order = ++writes.current;
    setWriteError(null);
    return order;
  };
  const failWrite = (order: number, action: string, subject: string, err: unknown) => {
    if (order === writes.current) setWriteError({ action, subject, message: readableError(err) });
  };

  useEffect(() => { void fetchRemote(); }, [fetchRemote]);

  const toggleEnabled = async (next: string) => {
    const enabled = next === "ON";
    const order = beginWrite();
    setToggleBusy(true);
    try {
      await apiFetch("/api/settings/remote", {
        method: "PUT",
        json: { enabled },
      });
      await fetchRemote();
    } catch (err) {
      failWrite(order, `Turn remote access ${enabled ? "on" : "off"}`, "", err);
    } finally {
      setToggleBusy(false);
    }
  };

  const issueCredential = async () => {
    if (!issueName.trim()) return;
    const identity = issueName.trim();
    const order = beginWrite();
    setIssuing(true);
    try {
      const result = await apiFetch<{
        token: string;
        id: string;
        identity: string;
        palette: string;
        expires_at: number;
      }>("/api/settings/remote/credentials", {
        method: "POST",
        json: {
          identity,
          palette: issuePalette,
          ttl_seconds: Number(issueTtl),
        },
      });
      setOneTimeToken(result.token);
      setIssueOpen(false);
      setIssueName("");
      setIssuePalette("PROJECT");
      setIssueTtl("43200");
      await fetchRemote();
    } catch (err) {
      failWrite(order, "Issue credential", identity, err);
    } finally {
      setIssuing(false);
    }
  };

  /** PHILO-7-02: Allow / Stop filing -- delegation.grant / delegation.revoke. */
  const setGrant = async (identity: string, verb: GrantVerbKind) => {
    const order = beginWrite();
    setGranting(identity);
    try {
      const result = await apiFetch(`/api/settings/remote/delegations/${encodeURIComponent(identity)}`, {
        method: verb === "allow" ? "PUT" : "DELETE",
        ...(verb === "allow" ? { json: {} } : {}),
      });
      setRefusals((current) => {
        const next = { ...current };
        delete next[identity];
        return next;
      });
      const act = grantActFrom(result, "succeeded", verb, identity);
      if (act) onGrantAct?.(act);
    } catch (err) {
      const payload = err instanceof ApiError ? err.payload : null;
      const code = payload && typeof payload === "object"
        ? String((payload as Record<string, unknown>).error ?? "")
        : "";
      if (code) {
        setRefusals((current) => ({ ...current, [identity]: { verb, code } }));
        const act = grantActFrom(payload, "refused", verb, identity, code);
        if (act) onGrantAct?.(act);
      } else {
        failWrite(order, GRANT_WORDS[verb], identity, err);
      }
    } finally {
      setGranting(null);
      await fetchRemote();
    }
  };

  /** PHILO-9-07: Allow / Stop run and publish -- project.delegation.grant / .revoke. */
  const setProjectGrant = async (identity: string, projectId: string, projectName: string, verb: GrantVerbKind) => {
    const key = `${identity}/${projectId}`;
    const extra = { kind: "project" as const, project: projectName };
    const order = beginWrite();
    setGranting(key);
    try {
      const result = await apiFetch(
        `/api/settings/remote/delegations/${encodeURIComponent(identity)}/projects/${encodeURIComponent(projectId)}`,
        { method: verb === "allow" ? "PUT" : "DELETE", ...(verb === "allow" ? { json: {} } : {}) },
      );
      setRefusals((current) => {
        const next = { ...current };
        delete next[key];
        return next;
      });
      const act = grantActFrom(result, "succeeded", verb, identity, undefined, extra);
      if (act) onGrantAct?.(act);
    } catch (err) {
      const payload = err instanceof ApiError ? err.payload : null;
      const code = payload && typeof payload === "object"
        ? String((payload as Record<string, unknown>).error ?? "")
        : "";
      if (code) {
        setRefusals((current) => ({ ...current, [key]: { verb, code } }));
        const act = grantActFrom(payload, "refused", verb, identity, code, extra);
        if (act) onGrantAct?.(act);
      } else {
        failWrite(order, PROJECT_GRANT_WORDS[verb], `${identity} · ${projectName}`, err);
      }
    } finally {
      setGranting(null);
      await fetchRemote();
    }
  };

  const revokeCredential = async (id: string, identity: string) => {
    const order = beginWrite();
    setRevoking(id);
    try {
      const result = await apiFetch<Record<string, unknown>>(`/api/settings/remote/credentials/${id}`, {
        method: "DELETE",
      });
      // Durable first: the credential's LIVE grants were revoked BEFORE the
      // credential, each with its own receipt (credential_revoked).
      const projectEnded = Array.isArray(result?.project_grants_revoked)
        ? (result.project_grants_revoked as Record<string, unknown>[])
        : [];
      if (projectEnded.length > 0) {
        const last = projectEnded[projectEnded.length - 1];
        const act = grantActFrom(last, "succeeded", "stop", identity, undefined, {
          kind: "project", project: String(last.project_name ?? ""), reason: PROJECT_GRANT_WORDS.credentialRevoked,
        });
        if (act) onGrantAct?.(act);
      } else if (result?.grant_revoked) {
        const act = grantActFrom(result, "succeeded", "stop", identity);
        if (act) onGrantAct?.(act);
      }
      await fetchRemote();
    } catch (err) {
      failWrite(order, "Revoke credential", identity, err);
    } finally {
      setRevoking(null);
    }
  };

  const copyToken = () => {
    if (oneTimeToken) {
      void navigator.clipboard.writeText(oneTimeToken);
    }
  };

  if (loading && !wire) return <span className="gadget-fact" role="status">Reading remote access…</span>;
  if (readErrors.remote && !wire) return <div className="prefs-read-failure" role="alert"><span>Remote access read failed · Grants unchanged · Retry</span><Button dense variant="ghost" onClick={() => void fetchRemote()}>Retry</Button></div>;

  const enabled = wire?.enabled ?? false;
  const allCredentials = wire?.credentials ?? [];
  // PHILO-7-02: a grant is authority, whatever the transport switch says.
  // ON: every credential row. OFF: the credential rows with a LIVE desk or
  // (PHILO-9-07) a LIVE project grant, and (GRANT-ROW 2026-10-30) an active
  // credential with a stopped grant: Stop filing keeps its row, which says
  // "Filing stopped" and offers Allow filing in the same place. A credential
  // never granted stays hidden. Always: every grant row with no credential.
  const credentials = enabled
    ? allCredentials
    : allCredentials.filter((c) => c.delegation?.state === "LIVE"
        || (c.project_delegations ?? []).some((g) => g.state === "LIVE")
        || (c.active && (Boolean(c.delegation) || (c.project_delegations ?? []).length > 0)));
  const delegations = wire?.delegations ?? [];
  const projectOrphans = wire?.project_delegations ?? [];
  const toggleRow = (identity: string, open: boolean) => {
    setOpenRows((rows) => (open ? [...rows.filter((r) => r !== identity), identity] : rows.filter((r) => r !== identity)));
    if (open) {
      // The projects the row can grant: every project that is not archived.
      void fetchProjects();
    }
  };
  const activeCount = credentials.filter((c) => c.active).length;
  const totalCount = allCredentials.length;
  const addressToken = enabled && wire?.port
    ? `${wire.bind_host || "0.0.0.0"}:${wire.port}`
    : null;

  return (
    <GadgetGroup material="inset" label="Remote access" actions={enabled && !issueOpen ? (
      <Button variant="ghost" onClick={() => { setOneTimeToken(null); setIssueOpen(true); }} data-testid="issue-credential-btn">Issue credential</Button>
    ) : undefined}>
      {/* The toggle row */}
      {/* PHILO-17 U35: plain words (was "Streamable HTTP", the transport's
          name); the select keeps its "Remote transport" name. */}
      <GadgetRow label="Other devices">
        <CycleGadget
          label="Remote transport"
          value={enabled ? "ON" : "OFF"}
          options={[{ value: "OFF", label: "Off" }, { value: "ON", label: "On" }]}
          disabled={toggleBusy || loading}
          onChange={toggleEnabled}
        />
        {enabled && addressToken ? (
          <span className="gadget-fact" data-testid="remote-address">{addressToken}</span>
        ) : null}
        {enabled && totalCount > 0 ? (
          <Token className="surface-token" data-chip data-testid="remote-total-count">
            {countToken(totalCount, "CREDENTIAL", "CREDENTIALS")}
          </Token>
        ) : null}
      </GadgetRow>

      {/* PHILO-7-02: the ledger renders when any credential row OR any
          grant row is visible, whatever the switch says. */}
      {credentials.length > 0 || delegations.length > 0 || projectOrphans.length > 0 ? (
        <SurfaceLedger
          count={<>
            {GRANT_WORDS.agents}
            {activeCount > 0 ? (
              <> · <Token className="surface-token" data-chip data-testid="remote-active-count">
                {countToken(activeCount, "ACTIVE CREDENTIAL", "ACTIVE CREDENTIALS")}
              </Token></>
            ) : null}
          </>}
          cols="room"
        >
          {credentials.map((cred) => {
            const projectGrants = cred.project_delegations ?? [];
            const projectCapable = paletteHolds(cred.palette, PROJECT_GRANT_PALETTES, ["project.run_steward"]);
            // A LIVE desk grant always keeps its chip and its Stop (a grant is authority).
            const deskCapable = paletteHolds(cred.palette, DESK_GRANT_PALETTES, ["desk.", "zone.", "decision.", "note.", "kb."])
              || cred.delegation?.state === "LIVE";
            const isOpen = projectCapable && openRows.includes(cred.identity);
            const bodyId = `project-lines-${cred.id}`;
            return (
              <SurfaceLedgerRow
                key={cred.id}
                lead={<StateChip state={cred.active ? "success" : "idle"} label="" icon="●" />}
                primary={cred.identity}
                expands={false}
                open={isOpen}
                data-testid={`credential-row-${cred.id}`}
                cells={<>
                  {deskCapable ? <GrantChip grant={cred.delegation} /> : null}
                  <GrantRefusalChip refusal={refusals[cred.identity]} />
                  <ProjectGrantSummary grants={projectGrants} />
                  <Token className="surface-token" data-chip data-testid="palette-token">{paletteLabel(cred.palette)}</Token>
                  {cred.active ? (
                    <Token className="surface-token" data-chip>
                      EXPIRES {formatExpiry(cred.expires_at)}
                    </Token>
                  ) : (
                    <StateChip state="warning" label="EXPIRED" />
                  )}
                  <Token className="surface-token" data-chip data-muted>
                    {cred.last_used_at ? `LAST USED ${relativeAge(cred.last_used_at)}` : "NEVER USED"}
                  </Token>
                </>}
                trailing={<>
                  {projectCapable ? (
                    // The library Disclosure's trigger; its body is the row's own
                    // expansion slot (the HS-200-15 pattern). No popover, no modal.
                    <Disclosure
                      label={PROJECT_GRANT_WORDS.projects}
                      ariaLabel={`${PROJECT_GRANT_WORDS.projects}: ${cred.identity}`}
                      open={isOpen}
                      onOpenChange={(open) => toggleRow(cred.identity, open)}
                      controlsId={bodyId}
                      variant="default"
                    >
                      {null}
                    </Disclosure>
                  ) : null}
                  {deskCapable ? (
                    <Button
                      variant="ghost"
                      dense
                      disabled={granting === cred.identity}
                      onClick={() => void setGrant(cred.identity, cred.delegation?.state === "LIVE" ? "stop" : "allow")}
                      data-testid="grant-verb"
                    >
                      {cred.delegation?.state === "LIVE" ? GRANT_WORDS.stop : GRANT_WORDS.allow}
                    </Button>
                  ) : null}
                  <Button
                    variant="ghost"
                    dense
                    disabled={revoking === cred.id}
                    onClick={() => void revokeCredential(cred.id, cred.identity)}
                    data-testid="credential-revoke"
                  >
                    {GRANT_WORDS.revokeCredential}
                  </Button>
                </>}
              >
                {projectCapable ? (
                  <div id={bodyId} data-testid={`project-lines-${cred.identity}`}>
                    {[
                      ...projects.map((p) => ({ id: p.id, name: p.name, archived: false })),
                      // Archive keeps a grant (the charter): a LIVE grant on an
                      // archived project stays listed, Stop only, never Allow.
                      ...projectGrants
                        .filter((g) => g.project_archived && g.state === "LIVE")
                        .map((g) => ({ id: g.project_id, name: g.project_name, archived: true })),
                    ].map((p) => {
                      const grant = projectGrants.find((g) => g.project_id === p.id) ?? null;
                      const key = `${cred.identity}/${p.id}`;
                      const live = grant?.state === "LIVE";
                      return (
                        <GadgetRow key={p.id} label={p.name} wide controlWidth="full">
                          <span className="prefs-project-line" data-testid={`project-line-${p.id}`}>
                            {p.archived ? (
                              <Token className="surface-token" data-chip data-testid="project-archived">
                                {PROJECT_GRANT_WORDS.archived}
                              </Token>
                            ) : null}
                            <ProjectGrantChip grant={grant} />
                            <GrantRefusalChip refusal={refusals[key]} />
                            {live || !p.archived ? (
                              <Button
                                variant="ghost"
                                dense
                                disabled={granting === key}
                                onClick={() => void setProjectGrant(cred.identity, p.id, p.name, live ? "stop" : "allow")}
                                data-testid="project-grant-verb"
                              >
                                {live ? PROJECT_GRANT_WORDS.stop : PROJECT_GRANT_WORDS.allow}
                              </Button>
                            ) : null}
                          </span>
                        </GadgetRow>
                      );
                    })}
                  </div>
                ) : null}
              </SurfaceLedgerRow>
            );
          })}
          {delegations.map((grant) => (
            <SurfaceLedgerRow
              key={grant.grant_id}
              lead={<StateChip state="idle" label="" icon="●" />}
              primary={grant.identity}
              expands={false}
              data-testid={`delegation-row-${grant.grant_id}`}
              cells={<>
                <GrantChip grant={grant} />
                <GrantRefusalChip refusal={refusals[grant.identity]} />
                <Token className="surface-token" data-chip data-muted>{GRANT_WORDS.noCredential}</Token>
              </>}
              trailing={grant.state === "LIVE" ? (
                <Button
                  variant="ghost"
                  dense
                  disabled={granting === grant.identity}
                  onClick={() => void setGrant(grant.identity, "stop")}
                  data-testid="grant-verb"
                >
                  {GRANT_WORDS.stop}
                </Button>
              ) : undefined}
            />
          ))}
          {/* PHILO-9-07: a LIVE project grant with no credential row (a restart
              or a lost credential), beside Phase 7's desk orphans, with its Stop. */}
          {projectOrphans.map((grant) => {
            const key = `${grant.identity}/${grant.project_id}`;
            return (
              <SurfaceLedgerRow
                key={grant.grant_id}
                lead={<StateChip state="idle" label="" icon="●" />}
                primary={grant.identity}
                expands={false}
                data-testid={`project-delegation-row-${grant.grant_id}`}
                cells={<>
                  <ProjectGrantChip grant={grant} />
                  <GrantRefusalChip refusal={refusals[key]} />
                  <Token className="surface-token" data-chip>{grant.project_name}</Token>
                  {grant.project_archived ? (
                    <Token className="surface-token" data-chip data-testid="project-archived">{PROJECT_GRANT_WORDS.archived}</Token>
                  ) : null}
                  <Token className="surface-token" data-chip data-muted>{GRANT_WORDS.noCredential}</Token>
                </>}
                trailing={grant.state === "LIVE" ? (
                  <Button
                    variant="ghost"
                    dense
                    disabled={granting === key}
                    onClick={() => void setProjectGrant(grant.identity, grant.project_id, grant.project_name, "stop")}
                    data-testid="project-grant-verb"
                  >
                    {PROJECT_GRANT_WORDS.stop}
                  </Button>
                ) : undefined}
              />
            );
          })}
        </SurfaceLedger>
      ) : null}

      {/* The last grant act's receipt: outside the removable ledger, so it
          survives when its row disappears; opened from the footer. */}
      {receiptOpen && grantAct ? <GrantReceiptWell act={grantAct} /> : null}

      {/* Everything below only when ON */}
      {enabled ? (
        <>
          {/* One-time token display (after issue, before dismissal) */}
          {oneTimeToken ? (
            <SurfaceWell>
              <div className="prefs-token-once">
                <code className="prefs-token-value" data-testid="token-value">{oneTimeToken}</code>
                <Button variant="ghost" dense onClick={copyToken} data-testid="token-copy">
                  Copy
                </Button>
              </div>
              <span className="prefs-token-caption" data-tone="warning">
                TOKEN SHOWN ONCE — COPY IT NOW
              </span>
            </SurfaceWell>
          ) : null}

          {/* Issue credential verb + well */}
          {issueOpen ? (
            <SurfaceWell>
              <GadgetRow label="Name" controlWidth="full">
                <StringGadget
                  label="Credential name"
                  value={issueName}
                  placeholder="e.g. sweep-runner"
                  onChange={setIssueName}
                  autoFocus
                />
              </GadgetRow>
              <GadgetRow label="Access">
                <CycleGadget
                  label="Access"
                  value={issuePalette}
                  options={PALETTE_OPTIONS}
                  onChange={setIssuePalette}
                />
              </GadgetRow>
              <GadgetRow label="Expires after">
                <CycleGadget
                  label="Expires after"
                  value={issueTtl}
                  options={TTL_OPTIONS}
                  onChange={setIssueTtl}
                />
              </GadgetRow>
              <div className="prefs-issue-actions">
                <Button variant="primary" disabled={issuing || !issueName.trim()} onClick={() => void issueCredential()} data-testid="issue-submit">
                  Issue
                </Button>
                <Button variant="ghost" onClick={() => { setIssueOpen(false); setIssueName(""); }} data-testid="issue-cancel">
                  Cancel
                </Button>
              </div>
            </SurfaceWell>
          ) : null}
        </>
      ) : null}

      {readErrors.remote ? (
        <div className="prefs-read-failure" role="alert" data-testid="remote-read-error">
          <span>Remote access read failed · Grants unchanged · Retry · {humanizeWireValue(readErrors.remote)}</span>
          <Button dense variant="ghost" disabled={loading} onClick={() => void fetchRemote()}>Retry</Button>
        </div>
      ) : null}
      {readErrors.projects ? (
        <div className="prefs-read-failure" role="alert" data-testid="remote-projects-error">
          <span>Project read failed · Projects unchanged · Retry · {humanizeWireValue(readErrors.projects)}</span>
          <Button dense variant="ghost" disabled={projectsLoading} onClick={() => void fetchProjects()}>Retry</Button>
        </div>
      ) : null}
      {writeError ? (
        <div className="prefs-read-failure" role="alert" data-testid="remote-error">
          <span>Change not confirmed · {writeError.action}{writeError.subject ? ` · ${writeError.subject}` : ""} · {humanizeWireValue(writeError.message)}</span>
          <Button dense variant="ghost" disabled={loading} onClick={() => void fetchRemote()}>Reload current state</Button>
        </div>
      ) : null}
    </GadgetGroup>
  );
}
