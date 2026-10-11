/* First run C1 — the You card: his name and the other names for him.
 *
 * Stored in `config.owner` through the settings API (`GET/PUT
 * /api/settings`, section `owner: { name, aliases }`). The needs-you rule
 * reads them as "me" (holdspeak/services/needs_you_membership.py). */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
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
  const timer = useRef(0);
  const latest = useRef<OwnerSetting>({ name: "", aliases: [] });
  const touched = useRef(false);
  const pending = useRef(false);

  useEffect(() => {
    let live = true;
    void apiFetch<{ owner?: Partial<OwnerSetting> }>("/api/settings")
      .then((settings) => {
        if (!live || touched.current) return;
        const owner = {
          name: String(settings.owner?.name ?? ""),
          aliases: Array.isArray(settings.owner?.aliases) ? settings.owner!.aliases.map(String) : [],
        };
        latest.current = owner;
        setNameState(owner.name);
        setAliases(owner.aliases);
        setSaved(owner);
      })
      .catch(() => undefined);
    return () => {
      live = false;
      window.clearTimeout(timer.current);
    };
  }, []);

  const save = useCallback(async (keepalive = false) => {
    window.clearTimeout(timer.current);
    pending.current = false;
    const owner = latest.current;
    try {
      const result = await apiFetch<{ settings?: { owner?: OwnerSetting } }>("/api/settings", {
        method: "PUT",
        json: { owner },
        // On page leave the request must outlive the page.
        ...(keepalive ? { keepalive: true } : {}),
      });
      setSaved(result.settings?.owner ?? owner);
      setError("");
    } catch (caught) {
      setError(readableError(caught));
    }
  }, []);

  const schedule = useCallback(
    (owner: OwnerSetting) => {
      touched.current = true;
      latest.current = owner;
      pending.current = true;
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => void save(), SAVE_AFTER_MS);
    },
    [save],
  );

  // PHILO-17 words: a reload inside the delay lost the edit. Send it now.
  useFlushOnLeave(() => {
    if (pending.current) void save(true);
  });

  const setName = useCallback(
    (next: string) => {
      setNameState(next);
      schedule({ name: next, aliases: latest.current.aliases });
    },
    [schedule],
  );

  const addAliases = useCallback(
    (raw: string) => {
      const added = splitAliases(raw, latest.current.aliases, latest.current.name);
      if (!added.length) return;
      const next = [...latest.current.aliases, ...added];
      setAliases(next);
      schedule({ name: latest.current.name, aliases: next });
    },
    [schedule],
  );

  const removeLastAlias = useCallback(() => {
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
    setName,
    addAliases,
    removeLastAlias,
    flush: () => save(),
  };
}
