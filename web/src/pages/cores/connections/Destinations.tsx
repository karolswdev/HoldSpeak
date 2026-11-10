/* PHILO-10-04: the Destinations group in Settings -> Connections, under
 * Tools (the accounts each destination uses live in Tools, right above).
 * Built to the owner's ratified canvas (assets/story-04-destinations-canvas/,
 * "Ratify as drawn", 2026-09-29: B1 here; B2 the Room's Add destination
 * arrives AT the group with the form open; B3 the name fills from the target
 * and stays editable). Library species only: GadgetGroup, GadgetRow,
 * CycleGadget, StringGadget, CheckGadget, SecretRow, FoldGadget,
 * SurfaceLedger, SurfaceLedgerRow, StateChip, EgressChip, Button,
 * ConfirmVerb.
 *
 * - A row never changes its target. Edit = Save makes a NEW row and PARKS
 *   the old one (`replaces`); Remove = park. Parked rows keep their history
 *   (the PARKED fold).
 * - The key is typed once into the OS keychain and never shown again (SET /
 *   NOT SET); the face knows only present or absent.
 * - A read that gets no answer says CANNOT READ DESTINATIONS + Retry, never
 *   the empty add form. A refused key save says KEY NOT SAVED + why.
 * - Email Check reports the sender's verification, never the key alone.
 * - PHILO-11-05 (canvas D1-D4, design section 5): Slack is the sixth channel.
 *   The webhook URL is the credential: a SecretRow saved through the HTTP-only
 *   `channel.save_slack_webhook` (the hub mints the key_ref), never shown
 *   again. The channel name is his label; the name fills from it. Check says
 *   what is known without a post (WEBHOOK SET · HOST OK); it never posts.
 * - No counter of zero: the group head counts only when there is a row.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { ConfirmVerb, EgressChip, FoldGadget, GadgetGroup, StateChip, SurfaceLedger, SurfaceLedgerRow } from "../../../desk/surface";
import type { ConnectionsResponse } from "./api";
import { ACCOUNTS_CHANGED, fetchConnections } from "./api";
import { accountChip } from "../../../features/channels/accountChip";
import { DestForm, EMPTY, emailKeyIdentity, type Draft } from "../../../features/channels/DestinationForm";
import {
  CHANNEL_WORD,
  DEFAULT_EMAIL_PROVIDER,
  DEST_FOCUS,
  SEND_WORDS,
  egressOf,
  emailProvider,
  refusedWord,
  stamp,
  takeDestinationsFocus,
  targetToken,
  wire,
  Refusal,
  type Channel,
  type Destination,
  type EmailProvider,
} from "../../../features/channels/channels";

import { ListView, PaneInspector, PaneActions, GadgetRow, type ListVerb } from "../../../desk/surface";
import { Token } from "../../../desk/surface/Token";

// HS-S53: the form has one owner, features/channels/DestinationForm.tsx.
// These names stay importable from here; they forward to that owner.
export { DestForm, EMPTY, autoName, keyRef, type DestFormProps, type Draft } from "../../../features/channels/DestinationForm";

/** A destination's channel in sentence case on its row (the Send faces keep
 *  their own CHANNEL_WORD). */
const CHANNEL_NAME: Record<string, string> = {
  file: "File",
  github: "GitHub",
  jira: "Jira",
  confluence: "Confluence",
  email: "Email",
  slack: "Slack",
};

function fromDestination(d: Destination): Draft {
  const t = d.target,
    a = d.account;
  return {
    ...EMPTY,
    channel: d.channel,
    name: d.name,
    nameTouched: true,
    folder: String(t.folder ?? ""),
    synced: d.synced,
    repo: String(t.repo ?? ""),
    kind: t.kind === "pr" ? "pr" : "issue",
    number: t.number != null ? String(t.number) : "",
    jiraAccount: d.channel === "jira" ? `${a.site}|${a.email}` : "",
    key: String(t.key ?? ""),
    confAccount: d.channel === "confluence" ? `${a.site}|${a.email}` : "",
    space: String(t.space_id ?? ""),
    provider: a.provider === "resend" ? "resend" : "sendgrid",
    fromEmail: String(a.from_email ?? ""),
    fromName: String(a.from_name ?? ""),
    emailRef: String(a.key_ref ?? ""),
    to: [t.to as unknown].flat().filter(Boolean).join("\n"),
    cc: [t.cc as unknown].flat().filter(Boolean).join("\n"),
    // A new webhook is a new destination: Edit keeps this key_ref until he types a new URL (design section 5).
    slackLabel: String(t.channel_label ?? ""),
    slackRef: d.channel === "slack" ? String(a.key_ref ?? "") : "",
  };
}

function detailFields(d: Destination, keyKnown?: boolean): [string, string][] {
  const t = d.target,
    a = d.account;
  const base: [string, string][] = [["Channel", CHANNEL_WORD[d.channel] ?? d.channel]];
  switch (d.channel) {
    case "file":
      return [...base, ["Folder", String(t.folder)], ["Synced", d.synced ? "YES" : "NO"]];
    case "github":
      return [...base, ["Account", `@${a.login} · ${a.host}`], ["Repository", String(t.repo)], [t.kind === "pr" ? "Pull request" : "Issue", `#${t.number}`]];
    case "jira":
      return [...base, ["Account", `${a.email} · ${a.site}`], ["Work item", String(t.key)]];
    case "confluence":
      return [...base, ["Account", `${a.email} · ${a.site}`], ["Space id", String(t.space_id)]];
    case "email":
      return [
        ...base,
        ["Provider", emailProvider(a).label],
        ["From", a.from_name ? `${a.from_name} <${a.from_email}>` : String(a.from_email)],
        ["To", [t.to as unknown].flat().join(", ")],
        ["Cc", [t.cc as unknown].flat().join(", ") || "—"],
      ];
    // The face knows the webhook only as present or absent, and only when known: never the URL.
    case "slack":
      return [...base, ["Channel name", String(t.channel_label ?? "")], ["Webhook", keyKnown === true ? "SET · hooks.slack.com" : keyKnown === false ? "NOT SET" : "hooks.slack.com"]];
    default:
      return base;
  }
}

export function Destinations({ onCount }: { onCount?: (count: number) => void } = {}) {
  const [rows, setRows] = useState<Destination[] | null>(null);
  const [readFailed, setReadFailed] = useState(false);
  const [arrive, setArrive] = useState(false);
  const groupRef = useRef<HTMLDivElement>(null);
  const [conns, setConns] = useState<ConnectionsResponse | null>(null);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [accountsReadError, setAccountsReadError] = useState(false);
  const onAccountsRetry = () => window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
  // Settings: Accounts and Destinations share this module. Open the existing
  // account control above the form, so the destination draft stays mounted.
  const setUpAccount = (channel: Channel) => {
    const module = groupRef.current?.closest(".prefs-module") ?? document;
    const row = module.querySelector<HTMLElement>(`[data-testid="connections-${channel}"]`) ?? module.querySelector<HTMLElement>(`[data-testid^="connections-${channel}-conn-"]`);
    const add = module.querySelector<HTMLButtonElement>(`[data-testid="connections-add-open-${channel}"]`);
    const show = module.querySelector<HTMLButtonElement>(`[data-testid="connections-${channel}-show"]`);
    if (add && add.getAttribute("aria-expanded") !== "true") add.click();
    if (show && show.getAttribute("aria-expanded") !== "true") show.click();
    (row ?? add)?.scrollIntoView?.({ block: "center" });
    const target = module.querySelector<HTMLInputElement>(`[data-testid="connections-add-${channel}"] input`) ?? show ?? row?.querySelector<HTMLButtonElement>("button:not([disabled])") ?? add;
    target?.focus({ preventScroll: true });
  };
  useEffect(() => {
    let live = true;
    const read = () => {
      setAccountsLoading(true);
      void fetchConnections()
        .then((answer) => {
          if (live) {
            setConns(answer);
            setAccountsReadError(false);
          }
        })
        .catch(() => {
          if (live) {
            setConns(null);
            setAccountsReadError(true);
          }
        })
        .finally(() => {
          if (live) setAccountsLoading(false);
        });
    };
    read();
    window.addEventListener("focus", read);
    window.addEventListener(ACCOUNTS_CHANGED, read);
    return () => {
      live = false;
      window.removeEventListener("focus", read);
      window.removeEventListener(ACCOUNTS_CHANGED, read);
    };
  }, []);
  const [open, setOpen] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [keys, setKeys] = useState<Record<string, boolean>>({});
  const [checks, setChecks] = useState<Record<string, { busy: boolean; state?: string; at?: string; answeredAt?: string | null }>>({});
  const [removeBusy, setRemoveBusy] = useState<string | null>(null);
  // A Remove the hub did not confirm: the row stays open, named, with Retry
  // (Codex Astra r1 F2 on #697). Never closed as if it were parked.
  const [removeFailed, setRemoveFailed] = useState<Record<string, string>>({});
  const remove = (id: string) => {
    setRemoveBusy(id);
    setRemoveFailed((m) => {
      const n = { ...m };
      delete n[id];
      return n;
    });
    void wire
      .park(id)
      .then(() => {
        setOpen(null);
        reload();
      })
      .catch((e) =>
        setRemoveFailed((m) => ({
          ...m,
          [id]: e instanceof Refusal ? e.code : "no_answer",
        })),
      )
      .finally(() => setRemoveBusy(null));
  };
  const reload = useCallback(
    () =>
      void wire
        .destinations(true)
        .then((r) => {
          setRows(r);
          setReadFailed(false);
          setKeys((k) => ({
            ...k,
            ...Object.fromEntries(
              r
                .filter((d) => d.channel === "email" && typeof d.account.key_present === "boolean")
                .map((d) => [emailKeyIdentity(String(d.account.provider ?? DEFAULT_EMAIL_PROVIDER), String(d.account.key_ref)), !!d.account.key_present]),
            ),
          }));
        })
        .catch(() => setReadFailed(true)),
    [],
  );
  useEffect(() => {
    reload();
    const want = () => {
      if (takeDestinationsFocus()) setArrive(true);
    };
    want();
    window.addEventListener(DEST_FOCUS, want);
    return () => window.removeEventListener(DEST_FOCUS, want);
  }, [reload]);
  // B2, the arrival: once the group has drawn, bring it into view with the add form open.
  useEffect(() => {
    if (!arrive || (rows === null && !readFailed)) return;
    setArrive(false);
    setOpen(null);
    setEditing(null);
    setAdding(true);
    requestAnimationFrame(() => groupRef.current?.scrollIntoView({ block: "start" }));
  }, [arrive, rows, readFailed]);
  const onKey = (ref: string, v: string, provider: EmailProvider): Promise<string | null> =>
    wire
      .saveKey(ref, v, provider)
      .then(() => {
        setKeys((k) => ({ ...k, [emailKeyIdentity(provider, ref)]: true }));
        return null;
      })
      .catch((e) => (e instanceof Refusal ? e.code : "no_answer"));
  const onSlackKey = (url: string): Promise<{ keyRef: string } | { code: string }> =>
    wire
      .saveSlackWebhook(url)
      .then((r) => {
        setKeys((k) => ({ ...k, [r.key_ref]: true }));
        return { keyRef: r.key_ref };
      })
      .catch((e) => ({ code: e instanceof Refusal ? e.code : "no_answer" }));
  const onKeyKnown = useCallback((ref: string, present: boolean) => setKeys((k) => ({ ...k, [ref]: present })), []);
  /** A Slack row's webhook, as far as this face knows it (a save or a Check): true, false or unknown. */
  const slackKey = (d: Destination): boolean | undefined => (d.channel === "slack" ? keys[String(d.account.key_ref ?? "")] : undefined);
  const activeCount = rows?.filter((row) => row.state === "active").length;
  useEffect(() => {
    if (activeCount !== undefined) onCount?.(activeCount);
  }, [activeCount, onCount]);
  if (readFailed) {
    return (
      <div className="connections-destinations" data-send="destinations" data-testid="destinations" ref={groupRef}>
        <GadgetGroup label="Destinations">
          <div className="send-verbs" data-testid="dest-unreadable">
            <StateChip state="failure" label={`${SEND_WORDS.cannotRead} DESTINATIONS`} />
            <Button dense variant="ghost" data-testid="dest-unreadable-retry" onClick={reload}>
              {SEND_WORDS.retry}
            </Button>
          </div>
        </GadgetGroup>
      </div>
    );
  }
  // The first read is out: nothing drawn yet, but still reading (aria-busy), so
  // the group's late arrival is not read as a settled window moving.
  if (rows === null) return <span hidden aria-busy="true" data-testid="dest-reading" />;
  const active = rows.filter((d) => d.state === "active");
  const parked = rows.filter((d) => d.state === "parked");
  const form = (
    <DestForm
      conns={conns}
      accountsLoading={accountsLoading}
      accountsReadError={accountsReadError}
      onAccountsRetry={onAccountsRetry}
      initial={EMPTY}
      keys={keys}
      onKey={onKey}
      onSlackKey={onSlackKey}
      onKeyKnown={onKeyKnown}
      onSetUpAccount={setUpAccount}
      onDone={(saved) => {
        // PHILO-10-07: after Save the form closes; the saved row stays in view (at 393 the closed form
        // otherwise leaves the list above the window).
        setAdding(false);
        reload();
        // Betterment send S1: a saved GitHub row opens, so its Account line shows the login gh named.
        if (saved?.channel === "github") setOpen(saved.id);
        requestAnimationFrame(() => groupRef.current?.scrollIntoView({ block: "start" }));
      }}
      onCancel={active.length ? () => setAdding(false) : undefined}
    />
  );
  const verbs: ListVerb[] = [
    {
      id: "add",
      label: "Add destination",
      symbol: "+",
      run: () => {
        setEditing(null);
        setAdding(true);
      },
    },
    {
      id: "remove",
      label: "Remove destination",
      symbol: "−",
      key: "Delete",
      enabled: (row) => Boolean(row) && !active.find((d) => d.id === row?.id)?.builtin && !removeBusy,
      run: (row) => {
        if (row) remove(row.id);
      },
    },
    {
      id: "open",
      label: "Open",
      key: "Enter",
      enabled: (row) => Boolean(row),
      run: (row) => {
        setAdding(false);
        setEditing(row?.id ?? null);
      },
    },
  ];
  const selected = active.find((d) => d.id === editing);
  return (
    <div className="surface-tab-panel" data-testid="destinations" ref={groupRef}>
      {Object.values(removeFailed).length ? (
        <PaneActions>
          <span role="alert">Destination not removed</span>
          <Button
            dense
            onClick={() => {
              if (open) remove(open);
            }}
          >
            Retry
          </Button>
        </PaneActions>
      ) : null}
      {adding ? (
        <PaneInspector label="Add destination" onClose={() => setAdding(false)}>
          {form}
        </PaneInspector>
      ) : selected ? (
        <PaneInspector label={selected.name} onClose={() => setEditing(null)}>
          {selected.builtin ? (
            <GadgetGroup>
              <GadgetRow label="Destination">
                <EgressChip {...egressOf(selected)} />
              </GadgetRow>
              {detailFields(selected).map(([label, value]) => (
                <GadgetRow key={label} label={label}>
                  {value}
                </GadgetRow>
              ))}
            </GadgetGroup>
          ) : (
            <DestForm
              conns={conns}
              accountsLoading={accountsLoading}
              accountsReadError={accountsReadError}
              onAccountsRetry={onAccountsRetry}
              initial={fromDestination(selected)}
              replaces={selected.id}
              keys={keys}
              onKey={onKey}
              onSlackKey={onSlackKey}
              onKeyKnown={onKeyKnown}
              onSetUpAccount={setUpAccount}
              onDone={() => {
                setEditing(null);
                reload();
              }}
              onCancel={() => setEditing(null)}
            />
          )}
        </PaneInspector>
      ) : (
        <ListView
          label="Send to"
          ordered
          rows={active.map((destination) => ({
            id: destination.id,
            kind: "destination",
            name: destination.name,
            cells: {
              channel: CHANNEL_NAME[destination.channel],
              target: targetToken(destination.channel, destination.target),
            },
          }))}
          columns={[
            { key: "name", word: "Destination", track: "minmax(0, 1.2fr)" },
            { key: "channel", word: "Channel", track: "100px" },
            { key: "target", word: "To", track: "minmax(0, 1fr)" },
          ]}
          selectedId={open}
          onSelect={setOpen}
          verbs={verbs}
          defaultVerb="open"
        />
      )}
    </div>
  );
}
