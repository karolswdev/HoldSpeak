/* First run C1 — the You card: his name and the other names for him.
 *
 * Stored in `config.owner` through the settings API (`GET/PUT
 * /api/settings`, section `owner: { name, aliases }`). The needs-you rule
 * reads them as "me" (holdspeak/services/needs_you_membership.py). */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { useFlushOnLeave } from "../../lib/flushOnLeave";

export interface OwnerSetting {
  name: string;
  aliases: string[];
}

export interface OwnerNameAdapter {
  read(): Promise<{ owner?: Partial<OwnerSetting>; _revision?: string }>;
  write(owner: OwnerSetting, revision?: string, options?: { keepalive?: boolean }): Promise<{
    settings?: { owner?: OwnerSetting; _revision?: string };
  }>;
}

export type OwnerField = "name" | "aliases";
export type OwnerFieldStatus = "Edited" | "Saving" | "Saved" | "Not saved";

/** The production IO remains the current settings endpoint and payload. */
export const apiOwnerNameAdapter: OwnerNameAdapter = {
  read: () => apiFetch<{ owner?: Partial<OwnerSetting>; _revision?: string }>("/api/settings"),
  write: (owner, revision, options) => apiFetch<{ settings?: { owner?: OwnerSetting; _revision?: string } }>("/api/settings", {
    method: "PUT",
    json: revision ? { owner, _revision: revision } : { owner },
    keepalive: options?.keepalive,
  }),
};

function sameField(field: OwnerField, a: OwnerSetting, b: OwnerSetting): boolean {
  return field === "name"
    ? a.name === b.name
    : a.aliases.length === b.aliases.length && a.aliases.every((alias, i) => alias === b.aliases[i]);
}

function sameOwner(a: OwnerSetting, b: OwnerSetting): boolean {
  return sameField("name", a, b) && sameField("aliases", a, b);
}

const SAVE_AFTER_MS = 600;

/** Split typed aliases on commas; trim; drop empties and repeats. */
export function splitAliases(raw: string, existing: string[], name: string): string[] {
  const seen = new Set([...existing, name].map((n) => n.trim().toLowerCase()).filter(Boolean));
  const out: string[] = [];
  for (const part of raw.split(",")) {
    const alias = part.trim().replace(/\s+/g, " ");
    const key = alias.toLowerCase();
    if (!alias || seen.has(key)) continue;
    seen.add(key);
    out.push(alias);
  }
  return out;
}

export function useOwnerName(adapter: OwnerNameAdapter = apiOwnerNameAdapter) {
  const [name, setNameState] = useState("");
  const [aliases, setAliases] = useState<string[]>([]);
  const [aliasDraft, setAliasDraftState] = useState("");
  const [saved, setSaved] = useState<OwnerSetting>({ name: "", aliases: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [readError, setReadError] = useState("");
  const loaded = useRef(false);
  const timer = useRef(0);
  const latest = useRef<OwnerSetting>({ name: "", aliases: [] });
  const latestAliasDraft = useRef("");
  const acknowledged = useRef<OwnerSetting>({ name: "", aliases: [] });
  const writes = useRef<Array<{ id: number; owner: OwnerSetting; guarded: boolean }>>([]);
  const nextWriteId = useRef(0);
  const acknowledgedWriteId = useRef(0);
  const live = useRef(true);
  const failed = useRef<OwnerSetting | null>(null);
  const uncertain = useRef(false);
  const [, refreshStatus] = useState(0);
  const touched = useRef(false);
  /** An edit not yet sent. */
  const pending = useRef(false);
  /** The settings revision the next PUT echoes (HS-130-07 opt-in guard). */
  const revision = useRef<string | undefined>(undefined);
  /** Astra r2 on #1090: ONE save in flight; a later edit waits and coalesces
   *  to the newest value, so an older PUT never lands after a newer one. */
  const inFlight = useRef(false);
  const again = useRef(false);

  const beginWrite = useCallback((owner: OwnerSetting, writeRevision?: string) => {
    const id = ++nextWriteId.current;
    writes.current = [...writes.current, { id, owner, guarded: Boolean(writeRevision) }];
    failed.current = null;
    uncertain.current = false;
    if (live.current) refreshStatus((n) => n + 1);
    return id;
  }, []);
  const endWrite = useCallback((id: number) => {
    const index = writes.current.findIndex((write) => write.id === id);
    if (index !== -1) writes.current.splice(index, 1);
    if (live.current) refreshStatus((n) => n + 1);
  }, []);
  const acknowledge = useCallback((owner: OwnerSetting, writeRevision: string | undefined, id: number) => {
    if (id < acknowledgedWriteId.current) return false;
    acknowledgedWriteId.current = id;
    revision.current = writeRevision ?? revision.current;
    acknowledged.current = owner;
    uncertain.current = false;
    if (live.current) {
      setSaved(owner);
      if (sameOwner(latest.current, owner)) setError("");
    }
    return true;
  }, []);

  const reconcileUnguardedWrite = useCallback(async (newerId: number) => {
    const draftAtStart = latest.current;
    // A revisionless older request may have applied after the newer ACK.
    // Its response cannot certify the current draft until a fresh read does.
    failed.current = acknowledged.current;
    uncertain.current = true;
    if (live.current) refreshStatus((n) => n + 1);
    try {
      const settings = await adapter.read();
      if (acknowledgedWriteId.current !== newerId) return;
      const owner: OwnerSetting = {
        name: String(settings.owner?.name ?? ""),
        aliases: Array.isArray(settings.owner?.aliases) ? settings.owner.aliases.map(String) : [],
      };
      revision.current = settings._revision ?? revision.current;
      acknowledged.current = owner;
      uncertain.current = false;
      if (live.current) setSaved(owner);
      if (sameOwner(latest.current, owner)) {
        failed.current = null;
        if (live.current) setError("");
      } else if (sameOwner(latest.current, draftAtStart)) {
        failed.current = draftAtStart;
        pending.current = true;
        if (live.current) setError("Settings changed. Retry.");
      }
    } catch {
      if (acknowledgedWriteId.current === newerId && sameOwner(latest.current, draftAtStart)) {
        failed.current = draftAtStart;
        uncertain.current = true;
        pending.current = true;
        if (live.current) setError("Settings could not be checked. Retry.");
      }
    } finally {
      if (live.current) refreshStatus((n) => n + 1);
    }
  }, [adapter]);

  const send = useCallback(async () => {
    if (!loaded.current) return;
    window.clearTimeout(timer.current);
    if (inFlight.current) {
      again.current = true;
      return;
    }
    inFlight.current = true;
    try {
      for (let attempt = 0; attempt < 2; attempt += 1) {
        pending.current = false;
        const owner = latest.current;
        const writeRevision = revision.current;
        const id = beginWrite(owner, writeRevision);
        try {
          const result = await adapter.write(owner, writeRevision);
          if (!acknowledge(result.settings?.owner ?? owner, result.settings?._revision, id) && !writeRevision) {
            void reconcileUnguardedWrite(acknowledgedWriteId.current);
          }
          break;
        } catch (caught) {
          // Another write moved the settings (a Settings field, or the leave
          // send below): take its revision and send the newest value again.
          const payload = caught instanceof ApiError ? (caught.payload as { revision?: string } | null) : null;
          if (id < acknowledgedWriteId.current) break;
          if (caught instanceof ApiError && caught.status === 409 && payload?.revision) {
            revision.current = payload.revision;
            if (attempt === 0) continue;
          }
          if (!sameOwner(latest.current, acknowledged.current)) {
            if (sameOwner(latest.current, owner)) {
              failed.current = owner;
              if (live.current) setError(readableError(caught));
            }
            pending.current = true;
          }
          break;
        } finally {
          endWrite(id);
        }
      }
    } finally {
      inFlight.current = false;
      if (again.current) {
        again.current = false;
        void send();
      }
    }
  }, [acknowledge, adapter, beginWrite, endWrite, reconcileUnguardedWrite]);

  const setAliasDraft = useCallback((raw: string) => {
    latestAliasDraft.current = raw;
    setAliasDraftState(raw);
  }, []);

  const commitAliasDraft = useCallback(() => {
    const raw = latestAliasDraft.current;
    if (!raw.trim()) return;
    const added = splitAliases(raw, latest.current.aliases, latest.current.name);
    latestAliasDraft.current = "";
    if (live.current) setAliasDraftState("");
    if (!added.length) return;
    const next = [...latest.current.aliases, ...added];
    latest.current = { ...latest.current, aliases: next };
    touched.current = true;
    pending.current = true;
    if (live.current) setAliases(next);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => void send(), SAVE_AFTER_MS);
  }, [send]);

  /** The page hides or the editor unmounts: send the newest unsent value NOW
   *  with keepalive, without queueing behind an ordinary save. The revisionless
   *  response is reconciled if an older revisionless write can apply last. */
  const sendNow = useCallback(() => {
    if (!loaded.current) return;
    commitAliasDraft();
    if (!pending.current && !again.current) return;
    window.clearTimeout(timer.current);
    pending.current = false;
    again.current = false;
    revision.current = undefined;
    const owner = latest.current;
    const id = beginWrite(owner);
    void adapter.write(owner, undefined, { keepalive: true }).then((result) => {
      if (!acknowledge(result.settings?.owner ?? owner, result.settings?._revision, id)) {
        void reconcileUnguardedWrite(acknowledgedWriteId.current);
      }
    }).catch((caught) => {
      if (id < acknowledgedWriteId.current) return;
      if (sameOwner(latest.current, owner) && !sameOwner(acknowledged.current, owner)) {
        failed.current = owner;
        pending.current = true;
        if (live.current) setError(readableError(caught));
      }
    }).finally(() => endWrite(id));
  }, [acknowledge, adapter, beginWrite, commitAliasDraft, endWrite, reconcileUnguardedWrite]);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
        const settings = await adapter.read();
        if (!live.current) return;
        if (!revision.current && settings._revision) revision.current = settings._revision;
        loaded.current = true;
        setReadError("");
        if (touched.current) return;
        const owner = {
          name: String(settings.owner?.name ?? ""),
          aliases: Array.isArray(settings.owner?.aliases) ? settings.owner!.aliases.map(String) : [],
        };
        latest.current = owner;
        setNameState(owner.name);
        setAliases(owner.aliases);
        acknowledged.current = owner;
        setSaved(owner);
    } catch {
      if (live.current) setReadError("Your name could not be read");
    } finally { if (live.current) setLoading(false); }
  }, [adapter]);

  useEffect(() => {
    live.current = true;
    void reload();
    return () => {
      live.current = false;
      // Astra r2: leaving the editor (« Settings) inside the delay sent nothing.
      sendNow();
    };
  }, [reload, sendNow]);

  const save = send;

  // PHILO-17 words: a reload inside the delay lost the edit. Send it now.
  useFlushOnLeave(sendNow);

  const schedule = useCallback(
    (owner: OwnerSetting) => {
      if (!loaded.current) return;
      touched.current = true;
      latest.current = owner;
      pending.current = true;
      if (failed.current && !sameOwner(owner, failed.current)) setError("");
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => void save(), SAVE_AFTER_MS);
    },
    [save],
  );

  const setName = useCallback(
    (next: string) => {
      if (!loaded.current) return;
      setNameState(next);
      schedule({ name: next, aliases: latest.current.aliases });
    },
    [schedule],
  );

  const addAliases = useCallback(
    (raw: string) => {
      if (!loaded.current) return;
      const added = splitAliases(raw, latest.current.aliases, latest.current.name);
      if (!added.length) return;
      const next = [...latest.current.aliases, ...added];
      setAliases(next);
      schedule({ name: latest.current.name, aliases: next });
    },
    [schedule],
  );

  const removeLastAlias = useCallback(() => {
    if (!loaded.current) return;
    if (!latest.current.aliases.length) return;
    const next = latest.current.aliases.slice(0, -1);
    setAliases(next);
    schedule({ name: latest.current.name, aliases: next });
  }, [schedule]);

  const fieldStatus = (field: OwnerField): OwnerFieldStatus => {
    const current = latest.current;
    if (failed.current && sameField(field, current, failed.current)
      && (uncertain.current || !sameField(field, current, acknowledged.current))) return "Not saved";
    if (writes.current.some((write) => write.id < acknowledgedWriteId.current && !write.guarded
      && !sameField(field, current, write.owner))) return "Not saved";
    if (sameField(field, current, acknowledged.current)) return "Saved";
    if (writes.current.some((write) => sameField(field, current, write.owner))) return "Saving";
    return "Edited";
  };

  return {
    name,
    aliases,
    aliasDraft,
    isSet: Boolean(saved.name.trim()),
    error,
    loading,
    readError,
    fieldStatus,
    reload,
    setName,
    addAliases,
    setAliasDraft,
    commitAliasDraft,
    removeLastAlias,
    flush: () => save(),
  };
}
