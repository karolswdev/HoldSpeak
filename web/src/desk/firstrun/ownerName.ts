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

export function useOwnerName() {
  const [name, setNameState] = useState("");
  const [aliases, setAliases] = useState<string[]>([]);
  const [saved, setSaved] = useState<OwnerSetting>({ name: "", aliases: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [readError, setReadError] = useState("");
  const loaded = useRef(false);
  const timer = useRef(0);
  const latest = useRef<OwnerSetting>({ name: "", aliases: [] });
  const touched = useRef(false);
  /** An edit not yet sent. */
  const pending = useRef(false);
  /** The settings revision the next PUT echoes (HS-130-07 opt-in guard). */
  const revision = useRef<string | undefined>(undefined);
  /** Astra r2 on #1090: ONE save in flight; a later edit waits and coalesces
   *  to the newest value, so an older PUT never lands after a newer one. */
  const inFlight = useRef(false);
  const again = useRef(false);

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
        try {
          const result = await apiFetch<{ settings?: { owner?: OwnerSetting; _revision?: string } }>("/api/settings", {
            method: "PUT",
            json: revision.current ? { owner, _revision: revision.current } : { owner },
          });
          revision.current = result.settings?._revision ?? revision.current;
          setSaved(result.settings?.owner ?? owner);
          setError("");
          break;
        } catch (caught) {
          // Another write moved the settings (a Settings field, or the leave
          // send below): take its revision and send the newest value again.
          const payload = caught instanceof ApiError ? (caught.payload as { revision?: string } | null) : null;
          if (caught instanceof ApiError && caught.status === 409 && payload?.revision && attempt === 0) {
            revision.current = payload.revision;
            continue;
          }
          setError(readableError(caught));
          pending.current = true;
          break;
        }
      }
    } finally {
      inFlight.current = false;
      if (again.current) {
        again.current = false;
        void send();
      }
    }
  }, []);

  /** The page hides or the editor unmounts: send the newest unsent value NOW,
   *  with keepalive, never queued behind a save in flight. It carries no
   *  revision, so it applies; an older save in flight carries the old revision
   *  and the hub refuses it if it lands later (newest wins either way). */
  const sendNow = useCallback(() => {
    if (!loaded.current) return;
    if (!pending.current && !again.current) return;
    window.clearTimeout(timer.current);
    pending.current = false;
    again.current = false;
    revision.current = undefined;
    void apiFetch("/api/settings", {
      method: "PUT",
      json: { owner: latest.current },
      keepalive: true,
    }).catch(() => undefined);
  }, []);

  const live = useRef(true);
  const reload = useCallback(async () => {
    setLoading(true);
    try {
        const settings = await apiFetch<{ owner?: Partial<OwnerSetting>; _revision?: string }>("/api/settings");
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
        setSaved(owner);
    } catch {
      if (live.current) setReadError("Your name could not be read");
    } finally { if (live.current) setLoading(false); }
  }, []);

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

  return {
    name,
    aliases,
    isSet: Boolean(saved.name.trim()),
    error,
    loading,
    readError,
    reload,
    setName,
    addAliases,
    removeLastAlias,
    flush: () => save(),
  };
}
