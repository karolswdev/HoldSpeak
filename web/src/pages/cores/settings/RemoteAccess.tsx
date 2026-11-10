// Settings > This Mac > Remote access (HS-174-02/03): the credential ledger,
// the issue well and the desk and project grants. Moved out of SettingsCore.tsx.
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../../lib/api";
import { humanizeWireValue } from "../../../lib/productLanguage";
import { CycleGadget, GadgetGroup, GadgetRow, StringGadget, type CycleOption } from "../../../desk/surface/gadgets";
import { ListView, PreferencePane, ListPane, PaneInspector, InspectorForm, PaneActions, type ListVerb, countToken, StateChip, SurfaceLedger, SurfaceLedgerRow, SurfaceWell } from "../../../desk/surface";
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

const PALETTE_OPTIONS: CycleOption[] = [{ value: "PROJECT" }, { value: "SWEEP" }, { value: "DESK" }, { value: "ALL" }];
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

type ProjectFact = {
  id: string;
  name: string;
  is_archived?: boolean | number | null;
};

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
  bare = false,
  onEnabledChange,
  grantAct = null,
  receiptOpen = false,
  onGrantAct,
}: {
  /** The caller's plate names it; the group draws no label of its own. */
  bare?: boolean;
  /** Report the live enabled state so the parent can update hub chips. */
  onEnabledChange?: (enabled: boolean) => void;
  /** PHILO-7-02: the last grant act's receipt, and whether its well is open
   *  (the footer's receipt Button toggles it; it outlives the row). */
  grantAct?: GrantAct | null;
  receiptOpen?: boolean;
  onGrantAct?: (act: GrantAct) => void;
} = {}) {
  const [projectView, showProjects] = useState(false);
  const [picked, pick] = useState<string | null>(null);
  const [inspecting, inspect] = useState<string | null>(null);
  const [projectPicked, pickProject] = useState<string | null>(null);
  const [wire, setWire] = useState<RemoteWire | null>(null);
  const [loading, setLoading] = useState(true);
  type ReadTarget = "remote" | "projects";
  const [readErrors, setReadErrors] = useState<Partial<Record<ReadTarget, string>>>({});
  const [writeError, setWriteError] = useState<{
    action: string;
    subject: string;
    message: string;
  } | null>(null);
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
      if (order === remoteReads.current)
        setReadErrors((current) => ({
          ...current,
          remote: readableError(err),
        }));
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
      if (order === projectReads.current)
        setReadErrors((current) => ({
          ...current,
          projects: readableError(err),
        }));
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

  useEffect(() => {
    void fetchRemote();
  }, [fetchRemote]);

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
      const code = payload && typeof payload === "object" ? String((payload as Record<string, unknown>).error ?? "") : "";
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
      const result = await apiFetch(`/api/settings/remote/delegations/${encodeURIComponent(identity)}/projects/${encodeURIComponent(projectId)}`, {
        method: verb === "allow" ? "PUT" : "DELETE",
        ...(verb === "allow" ? { json: {} } : {}),
      });
      setRefusals((current) => {
        const next = { ...current };
        delete next[key];
        return next;
      });
      const act = grantActFrom(result, "succeeded", verb, identity, undefined, extra);
      if (act) onGrantAct?.(act);
    } catch (err) {
      const payload = err instanceof ApiError ? err.payload : null;
      const code = payload && typeof payload === "object" ? String((payload as Record<string, unknown>).error ?? "") : "";
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
      const projectEnded = Array.isArray(result?.project_grants_revoked) ? (result.project_grants_revoked as Record<string, unknown>[]) : [];
      if (projectEnded.length > 0) {
        const last = projectEnded[projectEnded.length - 1];
        const act = grantActFrom(last, "succeeded", "stop", identity, undefined, {
          kind: "project",
          project: String(last.project_name ?? ""),
          reason: PROJECT_GRANT_WORDS.credentialRevoked,
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

  if (loading && !wire)
    return (
      <span className="gadget-fact" role="status">
        Reading remote access…
      </span>
    );
  if (readErrors.remote && !wire)
    return (
      <div className="prefs-read-failure" role="alert">
        <span>Remote access read failed · Grants unchanged · Retry</span>
        <Button dense variant="ghost" onClick={() => void fetchRemote()}>
          Retry
        </Button>
      </div>
    );

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
    : allCredentials.filter(
        (c) => c.delegation?.state === "LIVE" || (c.project_delegations ?? []).some((g) => g.state === "LIVE") || (c.active && (Boolean(c.delegation) || (c.project_delegations ?? []).length > 0)),
      );
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
  const addressToken = enabled && wire?.port ? `${wire.bind_host || "0.0.0.0"}:${wire.port}` : null;

  const rows = [
    ...credentials.map((cred) => ({
      id: cred.id,
      kind: "credential" as const,
      name: cred.identity,
      credential: cred,
      delegation: cred.delegation,
    })),
    ...delegations.map((grant) => ({
      id: grant.grant_id,
      kind: "delegation" as const,
      name: grant.identity,
      credential: null,
      delegation: grant,
    })),
    ...projectOrphans.map((grant) => ({
      id: grant.grant_id,
      kind: "project" as const,
      name: grant.identity,
      credential: null,
      delegation: null,
      project: grant,
    })),
  ];
  const selected = rows.find((row) => row.id === picked);
  const current = rows.find((row) => row.id === inspecting);
  const currentCred = current?.credential;
  const projectCapable = currentCred && paletteHolds(currentCred.palette, PROJECT_GRANT_PALETTES, ["project.run_steward"]);
  const canFile = (row: typeof selected) =>
    Boolean(row && (row.delegation?.state === "LIVE" || (row.credential && paletteHolds(row.credential.palette, DESK_GRANT_PALETTES, ["desk.", "zone.", "decision.", "note.", "kb."]))));
  const verbs: ListVerb[] = [
    {
      id: "issue",
      label: "Issue credential",
      symbol: "+",
      enabled: () => enabled && !issuing,
      run: () => {
        setOneTimeToken(null);
        setIssueOpen(true);
      },
    },
    {
      id: "revoke",
      label: "Revoke credential",
      symbol: "−",
      enabled: (row) => Boolean(rows.find((r) => r.id === row?.id)?.credential) && !revoking,
      run: (row) => {
        const cred = rows.find((r) => r.id === row?.id)?.credential;
        if (cred) void revokeCredential(cred.id, cred.identity);
      },
    },
    {
      id: "filing",
      label: selected?.delegation?.state === "LIVE" ? GRANT_WORDS.stop : GRANT_WORDS.allow,
      enabled: (row) => !granting && canFile(rows.find((r) => r.id === row?.id)),
      run: (row) => {
        const source = rows.find((r) => r.id === row?.id);
        if (source) void setGrant(source.name, source.delegation?.state === "LIVE" ? "stop" : "allow");
      },
    },
    { id: "details", label: "Details…", key: "Enter", enabled: (row) => Boolean(rows.find((r) => r.id === row?.id)?.credential), run: (row) => { showProjects(false); inspect(row!.id); } },
    {
      id: "projects",
      label: "Projects…",
      key: "Enter",
      enabled: (row) => {
        const cred = rows.find((r) => r.id === row?.id)?.credential;
        return Boolean(cred && (paletteHolds(cred.palette, PROJECT_GRANT_PALETTES, ["project.run_steward"]) || cred.project_delegations?.some((g) => g.state === "LIVE")));
      },
      run: (row) => {
        showProjects(true);
        inspect(row!.id);
        void fetchProjects();
      },
    },
    {
      id: "stop-project",
      label: PROJECT_GRANT_WORDS.stop,
      enabled: (row) => !granting && rows.some((r) => r.id === row?.id && "project" in r && r.project.state === "LIVE"),
      run: (row) => {
        const source = rows.find((r) => r.id === row?.id);
        if (source && "project" in source) void setProjectGrant(source.name, source.project.project_id, source.project.project_name, "stop");
      },
    },
  ];
  const projectRows = currentCred
    ? [
        ...projects.map((p) => ({ ...p, archived: false })),
        ...(currentCred.project_delegations ?? [])
          .filter((g) => g.project_archived && g.state === "LIVE")
          .map((g) => ({
            id: g.project_id,
            name: g.project_name,
            archived: true,
          })),
      ]
    : [];
  return (
    <PreferencePane label="Remote access">
      <GadgetGroup label={bare ? undefined : "Remote access"}>
        <GadgetRow label="Other devices">
          <CycleGadget
            label="Remote transport"
            value={enabled ? "ON" : "OFF"}
            options={[
              { value: "OFF", label: "Off" },
              { value: "ON", label: "On" },
            ]}
            disabled={toggleBusy || loading}
            onChange={toggleEnabled}
          />
        </GadgetRow>
        {addressToken ? (
          <GadgetRow label="Address">
            <span data-testid="remote-address">{addressToken}</span>
          </GadgetRow>
        ) : null}
      </GadgetGroup>
      <ListPane label="Access inspector" list={(        <ListView
          label="Remote credentials"
          rows={rows.map((row) => ({
            id: row.id,
            kind: row.kind,
            name: row.name,
            state: row.credential && !row.credential.active ? { label: "Expired", tone: "warn" as const } : undefined,
            cells: {
              access: row.credential ? paletteLabel(row.credential.palette) : "No credential",
              filing: row.delegation?.state === "LIVE" ? "May file" : row.delegation ? "Filing stopped" : "",
            },
          }))}
          columns={[
            { key: "name", word: "Name", priority: 100 },
            { key: "access", word: "Access", priority: 20 },
            { key: "filing", word: "Filing", priority: 20 },
            { key: "state", word: "Needs you", priority: 30 },
          ]}
          selectedId={picked}
          onSelect={pick}
          verbs={verbs}
          rowProps={(row) => ({ "data-testid": `credential-row-${row.id}` })}
          defaultVerb="details"
        />)} >
      {oneTimeToken ? (
        <PaneInspector pendingChoice label="Copy this token now" onClose={() => setOneTimeToken(null)}>
          <InspectorForm><GadgetRow label="Token"><code className="surface-command-code" data-testid="token-value">{oneTimeToken}</code><Button dense onClick={copyToken} data-testid="token-copy">Copy</Button></GadgetRow></InspectorForm>
        </PaneInspector>
      ) : issueOpen ? (
        <PaneInspector label="Issue credential">
          <InspectorForm completion={{ cancel: () => setIssueOpen(false), cancelTestId: "issue-cancel", primary: { label: "Issue", disabled: issuing || !issueName.trim(), run: () => void issueCredential(), testId: "issue-submit" } }}>
            <GadgetRow label="Name">
              <StringGadget label="Credential name" value={issueName} onChange={setIssueName} autoFocus />
            </GadgetRow>
            <GadgetRow label="Access">
              <CycleGadget label="Access" value={issuePalette} options={PALETTE_OPTIONS} onChange={setIssuePalette} />
            </GadgetRow>
            <GadgetRow label="Expires after">
              <CycleGadget label="Expires after" value={issueTtl} options={TTL_OPTIONS} onChange={setIssueTtl} />
            </GadgetRow>
          </InspectorForm>
        </PaneInspector>
      ) : currentCred ? (
        <PaneInspector label={projectView ? `${currentCred.identity}: projects` : currentCred.identity} onClose={() => inspect(null)}>
          <InspectorForm>{!projectView ? <>
            <GadgetRow label="Access"><span>{paletteLabel(currentCred.palette)}</span></GadgetRow>
            <GadgetRow label="Expires"><span>{currentCred.active ? formatExpiry(currentCred.expires_at) : "Expired"}</span></GadgetRow>
            <GadgetRow label="Last used"><span>{currentCred.last_used_at ? relativeAge(currentCred.last_used_at) : "Never used"}</span></GadgetRow>
          </> : <GadgetRow label="Projects">
          <ListView
            label="Project access"
            rows={projectRows.map((project) => {
              const grant = currentCred.project_delegations?.find((g) => g.project_id === project.id);
              const live = grant?.state === "LIVE";
              return {
                id: project.id,
                kind: "project",
                name: project.name,
                cells: {
                  access: (
                    <CycleGadget
                      label={`${project.name} access`}
                      value={live ? "allow" : "stop"}
                      disabled={Boolean(granting) || (project.archived && !live) || (!projectCapable && !live)}
                      options={[
                        { value: "stop", label: "Stopped" },
                        { value: "allow", label: "Run and publish" },
                      ]}
                      onChange={(next) => void setProjectGrant(currentCred.identity, project.id, project.name, next as GrantVerbKind)}
                    />
                  ),
                },
              };
            })}
            columns={[
              { key: "name", word: "Project", priority: 100 },
              { key: "access", word: "Access", priority: 20, track: "minmax(0, 2fr)" },
            ]}
            rowProps={(row) => ({ "data-testid": `project-line-${row.id}` })}
            selectedId={projectPicked}
            onSelect={pickProject}
          /></GadgetRow>}</InspectorForm>
        </PaneInspector>
      ) : null}
      </ListPane>
      {receiptOpen && grantAct ? <GrantReceiptWell act={grantAct} /> : null}
      {Object.values(refusals).some(Boolean) ? (
        <PaneActions>
          {Object.entries(refusals).map(([key, refusal]) => (
            <GrantRefusalChip key={key} refusal={refusal} />
          ))}
        </PaneActions>
      ) : null}
      {readErrors.remote ? (
        <PaneActions role="alert" data-testid="remote-read-error">
          <span>
            Remote access read failed · Grants unchanged · Retry
          </span>
          <Button dense disabled={loading} onClick={() => void fetchRemote()}>
            Retry
          </Button>
        </PaneActions>
      ) : null}
      {readErrors.projects ? (
        <PaneActions role="alert" data-testid="remote-projects-error">
          <span>
            Project read failed · Projects unchanged · Retry
          </span>
          <Button dense disabled={projectsLoading} onClick={() => void fetchProjects()}>
            Retry
          </Button>
        </PaneActions>
      ) : null}
      {writeError ? (
        <PaneActions role="alert" data-testid="remote-error">
          <span>
            Change not confirmed · {writeError.action}
            {writeError.subject ? ` · ${writeError.subject}` : ""} · {humanizeWireValue(writeError.message)}
          </span>
          <Button dense onClick={() => void fetchRemote()}>
            Reload current state
          </Button>
        </PaneActions>
      ) : null}
    </PreferencePane>
  );
}
