// HS-169-02 — the streamlined Door controller.
// One screen: outcome + source rows with in-world pickers + Create.

import { useCallback, useEffect, useRef, useState } from "react";
import { readableError } from "../../../lib/api";
import { openSurface } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import {
  fetchConnections,
  type ConnectionTool,
} from "../../../pages/cores/connections/api";
import { discoverGitHub, discoverJira } from "../setup/api";
import * as doorApi from "./api";
import type { CountToken } from "./api";

/* ── Default watch toggles per provider ── */

export interface WatchDefault {
  key: string;
  label: string;
  templateId: string;
  on: boolean;
}

const GITHUB_DEFAULTS: WatchDefault[] = [
  { key: "open_prs", label: "OPEN PRS", templateId: "watch.github.review_queue", on: true },
  { key: "ci", label: "CI", templateId: "watch.github.branch_ci", on: true },
];

const JIRA_DEFAULTS: WatchDefault[] = [
  { key: "overdue", label: "OVERDUE", templateId: "watch.jira.due_risk", on: true },
  { key: "due_7_days", label: "DUE 7 DAYS", templateId: "watch.jira.delivery_flow", on: true },
  { key: "blocked", label: "BLOCKED", templateId: "watch.jira.blockers", on: false },
];

/* ── Source row state ── */

export type SourceRowState = "unpicked" | "checking" | "live" | "cant_check";

export interface PickerItem {
  value: string;
  label: string;
  detail: string;
  knownBy?: string;
}

export interface SourceRow {
  provider: string;
  connected: boolean;
  connectionState: string;
  scope: string | null;
  scopeRaw: string | { connection_ref: string; projects: string[] } | null;
  state: SourceRowState;
  toggles: Record<string, boolean>;
  counts: CountToken[];
  plain: string;
  host: string;
  reason: string | null;
  pickerOpen: boolean;
  adjustOpen: boolean;
  adjust: {
    base?: string;
    labels?: string;
    drafts?: boolean;
    issueTypes?: string[];
    jql?: string;
  };
  pickerQuery: string;
  pickerItems: PickerItem[];
  pickerCursor: string | null;
  pickerLoading: boolean;
}

function defaultToggles(provider: string): Record<string, boolean> {
  const defs = provider === "github" ? GITHUB_DEFAULTS : JIRA_DEFAULTS;
  const result: Record<string, boolean> = {};
  for (const d of defs) result[d.key] = d.on;
  return result;
}

function enabledWatchKeys(provider: string, toggles: Record<string, boolean>): string[] {
  const defs = provider === "github" ? GITHUB_DEFAULTS : JIRA_DEFAULTS;
  return defs.filter((d) => toggles[d.key]).map((d) => d.key);
}

function makeRow(tool: ConnectionTool): SourceRow {
  const connected = tool.state === "connected";
  return {
    provider: tool.provider_id,
    connected,
    connectionState: tool.state,
    scope: null,
    scopeRaw: null,
    state: "unpicked",
    toggles: defaultToggles(tool.provider_id),
    counts: [],
    plain: "",
    host: tool.egress_host ?? "",
    reason: null,
    pickerOpen: false,
    adjustOpen: false,
    adjust: { base: "main" },
    pickerQuery: "",
    pickerItems: [],
    pickerCursor: null,
    pickerLoading: false,
  };
}

/* ── Provider source ordering ── */

const PROVIDER_ORDER = ["github", "jira"];
const SOURCE_PROVIDERS = new Set(PROVIDER_ORDER);

function buildRows(tools: ConnectionTool[]): SourceRow[] {
  const sourceTools = tools.filter((t) => SOURCE_PROVIDERS.has(t.provider_id));
  const connected = sourceTools.filter((t) => t.state === "connected");
  const notConnected = sourceTools.filter((t) => t.state !== "connected");
  const sorted = [...connected, ...notConnected];
  sorted.sort((a, b) => {
    const ai = PROVIDER_ORDER.indexOf(a.provider_id);
    const bi = PROVIDER_ORDER.indexOf(b.provider_id);
    if (a.state === "connected" && b.state !== "connected") return -1;
    if (a.state !== "connected" && b.state === "connected") return 1;
    return ai - bi;
  });
  return sorted.map(makeRow);
}

/* ── Controller hook ── */

export interface DoorController {
  outcome: string;
  setOutcome: (v: string) => void;
  sources: SourceRow[];
  creating: boolean;
  error: string;
  pickScope: (provider: string, value: string, label: string, rawValue: string) => void;
  toggleWatch: (provider: string, key: string) => void;
  openPicker: (provider: string) => void;
  closePicker: (provider: string) => void;
  openAdjust: (provider: string) => void;
  closeAdjust: (provider: string) => void;
  updateAdjust: (provider: string, patch: Partial<SourceRow["adjust"]>) => void;
  connect: (provider: string) => void;
  create: () => void;
  cancel: () => void;
  searchPicker: (provider: string, query: string) => void;
  loadMorePicker: (provider: string) => void;
}

export function useDoorController(): DoorController {
  const [outcome, setOutcome] = useState("");
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const mountedRef = useRef(true);
  const connectionToolsRef = useRef<ConnectionTool[]>([]);

  const safe = useCallback(
    <T,>(fn: () => T): T | undefined => {
      if (mountedRef.current) return fn();
      return undefined;
    },
    [],
  );

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const updateRow = useCallback(
    (provider: string, patch: Partial<SourceRow>) => {
      setSources((prev) =>
        prev.map((r) => (r.provider === provider ? { ...r, ...patch } : r)),
      );
    },
    [],
  );

  /* ── Connections read ── */

  const readConnections = useCallback(async () => {
    try {
      const resp = await fetchConnections();
      connectionToolsRef.current = resp.tools;
      safe(() => {
        setSources((prev) => {
          if (prev.length === 0) return buildRows(resp.tools);
          return prev.map((row) => {
            const tool = resp.tools.find((t) => t.provider_id === row.provider);
            if (!tool) return row;
            const wasConnected = row.connected;
            const nowConnected = tool.state === "connected";
            return {
              ...row,
              connected: nowConnected,
              connectionState: tool.state,
              host: tool.egress_host ?? row.host,
              ...(wasConnected || !nowConnected
                ? {}
                : { state: "unpicked" as const }),
            };
          });
        });
      });
      return resp;
    } catch {
      return null;
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    void readConnections();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Settings → Connections round trip (168 D2) ── */

  const openConnectionsInPlace = useCallback(() => {
    useDesk.getState().openSurfaceWindow("configure-settings", "integrations");
  }, []);

  const SETTINGS_WINDOW_ID = "surface-settings";
  useEffect(() => {
    let prevHadSettings = SETTINGS_WINDOW_ID in useDesk.getState().windowsById;
    const unsub = useDesk.subscribe((deskState) => {
      const nowHasSettings = SETTINGS_WINDOW_ID in deskState.windowsById;
      if (prevHadSettings && !nowHasSettings) {
        void readConnections();
      }
      prevHadSettings = nowHasSettings;
    });
    return unsub;
  }, [readConnections]);

  /* ── Jira connection ref resolver ── */

  const jiraConnectionRef = useCallback((): string => {
    const jiraTool = connectionToolsRef.current.find((t) => t.provider_id === "jira");
    if (!jiraTool?.connections?.length) return "";
    const connected = jiraTool.connections.find((c) => c.state === "connected");
    return connected?.connection_ref ?? jiraTool.connections[0]?.connection_ref ?? "";
  }, []);

  /* ── Count fetch ── */

  const fetchCount = useCallback(
    async (
      provider: string,
      scopeRaw: string | { connection_ref: string; projects: string[] },
      toggles: Record<string, boolean>,
      adjust: SourceRow["adjust"],
    ) => {
      const watches = enabledWatchKeys(provider, toggles);
      if (watches.length === 0) {
        safe(() =>
          updateRow(provider, {
            state: "live",
            counts: [],
            plain: "",
            reason: null,
          }),
        );
        return;
      }
      try {
        const resp = await doorApi.doorCount(
          provider,
          scopeRaw,
          watches,
          adjust as Record<string, unknown>,
        );
        safe(() =>
          updateRow(provider, {
            state: resp.state === "cant_check" ? "cant_check" : "live",
            counts: resp.tokens,
            plain: resp.plain,
            host: resp.host || undefined,
            reason: resp.reason,
          }),
        );
      } catch (err) {
        safe(() =>
          updateRow(provider, {
            state: "cant_check",
            counts: [],
            plain: "",
            reason: readableError(err),
          }),
        );
      }
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  /* ── Pick scope ── */

  const pickScope = useCallback(
    (
      provider: string,
      value: string,
      label: string,
      rawValue: string,
    ) => {
      // Build the proper scopeRaw for the provider
      let scopeRaw: string | { connection_ref: string; projects: string[] };
      if (provider === "jira") {
        scopeRaw = {
          connection_ref: jiraConnectionRef(),
          projects: [value],
        };
      } else {
        scopeRaw = rawValue;
      }
      updateRow(provider, {
        scope: label,
        scopeRaw,
        state: "checking",
        pickerOpen: false,
        counts: [],
        plain: "",
        reason: null,
      });
      const row = sources.find((r) => r.provider === provider);
      void fetchCount(provider, scopeRaw, row?.toggles ?? defaultToggles(provider), row?.adjust ?? { base: "main" });
    },
    [sources, updateRow, fetchCount, jiraConnectionRef],
  );

  /* ── Toggle watch ── */

  const toggleWatch = useCallback(
    (provider: string, key: string) => {
      setSources((prev) =>
        prev.map((r) => {
          if (r.provider !== provider) return r;
          const next = { ...r.toggles, [key]: !r.toggles[key] };
          if (r.scopeRaw) {
            void fetchCount(provider, r.scopeRaw, next, r.adjust);
          }
          return { ...r, toggles: next, state: r.scopeRaw ? "checking" : r.state };
        }),
      );
    },
    [fetchCount],
  );

  /* ── Picker ── */

  const discoverItems = useCallback(
    async (provider: string, query: string, cursor?: string) => {
      updateRow(provider, { pickerLoading: true });
      try {
        if (provider === "github") {
          const resp = await discoverGitHub(query || undefined, cursor || undefined);
          const items: PickerItem[] = resp.items.map((item) => ({
            value: item.id || `${item.owner}/${item.name}`,
            label: item.id || `${item.owner}/${item.name}`,
            detail: item.visibility || "public",
          }));
          safe(() =>
            updateRow(provider, {
              pickerItems: cursor
                ? [...(sources.find((r) => r.provider === provider)?.pickerItems ?? []), ...items]
                : items,
              pickerCursor: resp.cursor ?? null,
              pickerLoading: false,
            }),
          );
        } else if (provider === "jira") {
          const connRef = jiraConnectionRef();
          if (!connRef) {
            safe(() => updateRow(provider, { pickerLoading: false }));
            return;
          }
          const resp = await discoverJira(connRef, "projects", {
            query: query || undefined,
            cursor: cursor ? Number(cursor) : undefined,
          });
          const items: PickerItem[] = resp.items.map((item) => ({
            value: item.key ?? item.id ?? "",
            label: `${item.key ?? item.id} · ${item.name}`,
            detail: item.type ?? "software",
          }));
          safe(() =>
            updateRow(provider, {
              pickerItems: cursor
                ? [...(sources.find((r) => r.provider === provider)?.pickerItems ?? []), ...items]
                : items,
              pickerCursor: resp.cursor != null ? String(resp.cursor) : null,
              pickerLoading: false,
            }),
          );
        }
      } catch {
        safe(() => updateRow(provider, { pickerLoading: false }));
      }
    },
    [sources, updateRow, jiraConnectionRef], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const openPicker = useCallback(
    (provider: string) => {
      updateRow(provider, { pickerOpen: true, adjustOpen: false, pickerQuery: "", pickerItems: [], pickerCursor: null });
      void discoverItems(provider, "");
    },
    [updateRow, discoverItems],
  );

  const closePicker = useCallback(
    (provider: string) => {
      updateRow(provider, { pickerOpen: false });
    },
    [updateRow],
  );

  const searchPicker = useCallback(
    (provider: string, query: string) => {
      updateRow(provider, { pickerQuery: query });
      void discoverItems(provider, query);
    },
    [updateRow, discoverItems],
  );

  const loadMorePicker = useCallback(
    (provider: string) => {
      const row = sources.find((r) => r.provider === provider);
      if (row?.pickerCursor) {
        void discoverItems(provider, row.pickerQuery, row.pickerCursor);
      }
    },
    [sources, discoverItems],
  );

  /* ── Adjust ── */

  const openAdjust = useCallback(
    (provider: string) => {
      updateRow(provider, { adjustOpen: true, pickerOpen: false });
    },
    [updateRow],
  );

  const closeAdjust = useCallback(
    (provider: string) => {
      updateRow(provider, { adjustOpen: false });
    },
    [updateRow],
  );

  const updateAdjust = useCallback(
    (provider: string, patch: Partial<SourceRow["adjust"]>) => {
      setSources((prev) =>
        prev.map((r) => {
          if (r.provider !== provider) return r;
          return { ...r, adjust: { ...r.adjust, ...patch } };
        }),
      );
    },
    [],
  );

  /* ── Connect ── */

  const connect = useCallback(
    (_provider: string) => {
      openConnectionsInPlace();
    },
    [openConnectionsInPlace],
  );

  /* ── Create ── */

  const create = useCallback(async () => {
    if (!outcome.trim()) return;
    setCreating(true);
    setError("");
    try {
      const payloads: doorApi.DoorSourcePayload[] = sources
        .filter((r) => r.connected && r.scopeRaw)
        .map((r) => ({
          provider: r.provider,
          scope: r.scopeRaw!,
          watches: enabledWatchKeys(r.provider, r.toggles),
          adjust: r.adjust as Record<string, unknown>,
        }));
      const resp = await doorApi.doorCreate(outcome.trim(), payloads);
      safe(() => {
        setCreating(false);
        // Open the Room, then close the Door so only the Room remains.
        openSurface("open-project-memory", `project:${resp.projectId}`);
        useDesk.getState().closeSurfaceWindow("surface-project-setup");
      });
    } catch (err) {
      safe(() => {
        setCreating(false);
        setError(readableError(err));
      });
    }
  }, [outcome, sources]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Cancel ── */

  const cancel = useCallback(() => {
    useDesk.getState().closeSurfaceWindow("surface-project-setup");
  }, []);

  return {
    outcome,
    setOutcome,
    sources,
    creating,
    error,
    pickScope,
    toggleWatch,
    openPicker,
    closePicker,
    openAdjust,
    closeAdjust,
    updateAdjust,
    connect,
    create,
    cancel,
    searchPicker,
    loadMorePicker,
  };
}
