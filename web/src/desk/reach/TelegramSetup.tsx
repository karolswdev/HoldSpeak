/* Settings ▸ Reach ▸ Telegram: the setup pane (owner, 2026-11-13: "so
 * unfriendly to configure"; canvas .tmp/orch-canvas/telegram/telegram.html,
 * Part 1, states A to F).
 *
 * Every state comes from the hub's answer (`GET /api/reach`, the owner view
 * of #2298 and #2299): no token, a token Telegram has not checked yet, a bot
 * with a name, a code that is open, a chat that is connected, and each
 * problem with its one verb. The desk calls nothing outside: `Open BotFather`
 * and `Open the bot in Telegram` are links that the owner's browser opens.
 * A token is never shown after it is saved; the field, the link and the code
 * carry `data-feedback-redact`. */
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError } from "../../lib/api";
import { GadgetGroup, GadgetRow, StringGadget } from "../surface/gadgets";
import { wireClock, wireDayClock } from "../surface/format";
import { InspectorFacts, InspectorQuestion, PaneActions, PaneNotice, StepHeading } from "../surface";

export type TelegramHealth = {
  state: "connected" | "not_checked" | "token_revoked" | "bot_blocked" | "another_desk" | "unreachable" | "no_token" | "keystore_locked" | "off" | string;
  since: string | null;
  words: string;
};

export type TelegramStatus = {
  on: boolean;
  token: "keystore" | "missing";
  destination?: string;
  paired: { name: string; at?: string | null } | null;
  pairing: { expires_at: string; link?: string } | null;
  bot?: { name: string; username: string; checked: boolean } | null;
  health?: TelegramHealth;
  last_test?: { sent_at: string | null; answered_at: string | null } | null;
  keystore?: "open" | "locked";
  keystore_words?: string | null;
};

/** What `POST /api/reach/telegram/pair` answers: the code is only here. */
export type TelegramPairing = { code: string; words: string; expires_at: string; say: string; link?: string };

export const TELEGRAM_LEAVES = "Questions, briefs and your answers. They go through Telegram's servers.";
export const BOTFATHER = "https://t.me/BotFather";
/** The short state word under the bot's name (the sentence is the hub's). */
const STATE_WORD: Record<string, string> = {
  connected: "Connected",
  not_checked: "Not checked yet",
  token_revoked: "Token refused",
  bot_blocked: "Stopped in the chat",
  another_desk: "Two desks, one bot",
  unreachable: "Not reachable",
};

/** The hub's own sentence for a refusal, when it sent one. */
export function hubWords(cause: unknown): string | null {
  const payload = cause instanceof ApiError ? cause.payload : null;
  const detail = payload && typeof payload === "object" ? (payload as { detail?: unknown }).detail : null;
  return typeof detail === "string" && detail.trim() ? detail : null;
}

function minutesLeft(expiresAt: string, now: number): number {
  const end = Date.parse(expiresAt);
  return Number.isFinite(end) ? Math.max(0, Math.ceil((end - now) / 60_000)) : 0;
}

function openOutside(url: string) {
  window.open(url, "_blank", "noopener,noreferrer");
}

/** One row: words at the left, its one verb at the right. */
function Said({ children, verb }: { children: ReactNode; verb?: ReactNode }) {
  return (
    <PaneActions>
      <span>{children}</span>
      {verb}
    </PaneActions>
  );
}

function TokenField({ draft, setDraft, busy, refused, onSave }: { draft: string; setDraft(value: string): void; busy: boolean; refused: string | null; onSave(value: string): Promise<boolean> }) {
  const save = async () => {
    const value = draft.trim();
    if (!value) return;
    // The draft leaves the face as soon as the hub keeps the token.
    if (await onSave(value)) setDraft("");
  };
  return (
    <>
      <GadgetRow label="Bot token" controlWidth="full">
        <PaneActions>
          <StringGadget
            label="Bot token"
            value={draft}
            onChange={setDraft}
            mic={false}
            type="password"
            placeholder="Paste the token from BotFather"
            onKeyDown={(event) => {
              if (event.key === "Enter") void save();
            }}
            inputProps={{ autoComplete: "off", spellCheck: false, "data-feedback-redact": "true" } as Record<string, unknown>}
          />
          <Button dense variant="primary" loading={busy} disabled={!draft.trim()} onClick={() => void save()} data-testid="reach-token-save">
            Check and save
          </Button>
        </PaneActions>
      </GadgetRow>
      {refused ? (
        <PaneNotice>
          <span role="alert" data-testid="reach-token-refused">
            {refused}
          </span>
        </PaneNotice>
      ) : null}
    </>
  );
}

export type TelegramActs = {
  saveToken(value: string): Promise<boolean>;
  pair(): void;
  disconnect(): Promise<boolean>;
  remove(username: string): Promise<boolean>;
  useHere(): void;
  sendTest(): void;
  /** Read the hub's status again (the keystore was locked). */
  readAgain(): void;
};

export function TelegramSetup({
  telegram,
  pairing,
  now,
  busy,
  tokenDraft,
  onTokenDraft,
  tokenRefused,
  refusal,
  sends,
  quiet,
  acts,
}: {
  telegram: TelegramStatus | undefined;
  /** The answer of the last `pair` press in this window (it holds the code). */
  pairing: TelegramPairing | null;
  now: number;
  busy: string;
  /** The token while he types it: the host holds it, so a refused token stays
   *  in its field across a tab change; it is cleared when the hub keeps it. */
  tokenDraft: string;
  onTokenDraft(value: string): void;
  /** The hub's sentence for a token it did not keep. */
  tokenRefused: string | null;
  /** The hub's sentence for another act that failed. */
  refusal: string | null;
  /** `Sends`: the Telegram rung's words (the When tab sets it). */
  sends?: string;
  /** `Quiet`: the quiet hours' words. */
  quiet?: string;
  acts: TelegramActs;
}) {
  const [changing, setChanging] = useState(false);
  const [asking, setAsking] = useState<"disconnect" | "remove" | null>(null);
  const state = telegram?.health?.state ?? (telegram?.token === "keystore" ? "not_checked" : "no_token");
  const bot = telegram?.bot ?? null;
  const named = Boolean(bot?.username);
  const paired = telegram?.paired ?? null;
  const tokenSaved = telegram?.token === "keystore";
  // A new token closes the field; a removed bot closes a question.
  useEffect(() => {
    if (!tokenSaved) setAsking(null);
  }, [tokenSaved]);
  useEffect(() => {
    setChanging(false);
  }, [bot?.username, state]);

  if (!telegram) return null;

  if (telegram.keystore === "locked" || state === "keystore_locked" || state === "off") {
    return (
      <div data-testid="reach-telegram" data-state={state}>
        <PaneNotice>
          <Said
            verb={
              state === "off" ? undefined : (
                <Button dense variant="primary" onClick={acts.readAgain} data-testid="reach-read-again">
                  Read again
                </Button>
              )
            }
          >
            <span data-testid="reach-telegram-health">{telegram.keystore_words || telegram.health?.words}</span>
          </Said>
        </PaneNotice>
      </div>
    );
  }

  const leaves = (
    <GadgetRow label="Leaves this Mac" controlWidth="full">
      <span data-testid="reach-egress">{TELEGRAM_LEAVES}</span>
    </GadgetRow>
  );
  const saveToken = async (value: string) => {
    const kept = await acts.saveToken(value);
    if (kept) setChanging(false);
    return kept;
  };
  const tokenField = <TokenField draft={tokenDraft} setDraft={onTokenDraft} busy={busy === "token"} refused={tokenRefused} onSave={saveToken} />;
  const botName = bot ? [bot.name, named ? `@${bot.username}` : ""].filter(Boolean).join(" · ") : "";
  const link = pairing?.link ?? telegram.pairing?.link ?? null;
  const expiresAt = pairing?.expires_at ?? telegram.pairing?.expires_at ?? null;
  const codeOpen = Boolean(telegram.pairing) && Boolean(expiresAt) && minutesLeft(String(expiresAt), now) > 0;
  const left = expiresAt ? minutesLeft(expiresAt, now) : 0;

  /* ── A: not set up ─────────────────────────────────────────────── */
  if (!tokenSaved) {
    return (
      <div data-testid="reach-telegram" data-state="not_set_up">
        <StepHeading number={1} title="Make a bot in Telegram" testId="reach-step-1" />
        <GadgetGroup>
          <GadgetRow label="In Telegram" controlWidth="full">
            <Said
              verb={
                <Button dense variant="primary" onClick={() => openOutside(BOTFATHER)} data-testid="reach-open-botfather">
                  Open BotFather
                </Button>
              }
            >
              Open the chat with BotFather. BotFather makes bots.
            </Said>
          </GadgetRow>
          <GadgetRow label="Send it" controlWidth="full">
            <code>/newbot</code>
          </GadgetRow>
          <GadgetRow label="Then type" controlWidth="full">
            <span>
              A name for the bot, then a user name that ends in <code>bot</code>
            </span>
          </GadgetRow>
          <GadgetRow label="You get" controlWidth="full">
            <span>A token. Copy it.</span>
          </GadgetRow>
        </GadgetGroup>
        <StepHeading number={2} title="Paste its token" testId="reach-step-2" />
        <GadgetGroup>
          {tokenField}
          <GadgetRow label="Kept in" controlWidth="full">
            <span>The keystore of this Mac. Telegram checks the token before the desk keeps it.</span>
          </GadgetRow>
        </GadgetGroup>
        <StepHeading number={3} title="Connect your chat" state="later" after="After step 2" testId="reach-step-3" />
        <GadgetGroup>
          <GadgetRow label="In Telegram" controlWidth="full">
            <Said
              verb={
                <Button dense disabled title="Paste the token first" data-testid="reach-pair">
                  Get the link
                </Button>
              }
            >
              Press Start in the chat with your bot.
            </Said>
          </GadgetRow>
          {leaves}
        </GadgetGroup>
      </div>
    );
  }

  /* ── the bot's row, in every state that has a token ─────────────── */
  const botRows = (
    <GadgetGroup>
      <GadgetRow label="Bot" controlWidth="full">
        <Said
          verb={
            // A refused token has its field open below: no second verb for it.
            state === "token_revoked" ? undefined : changing ? (
              <Button dense variant="ghost" onClick={() => setChanging(false)}>
                Cancel
              </Button>
            ) : (
              <Button dense onClick={() => setChanging(true)} data-testid="reach-token-replace">
                Change the token
              </Button>
            )
          }
        >
          <span data-testid="reach-bot-name">{botName || "Token saved"}</span>
        </Said>
      </GadgetRow>
      {changing || state === "token_revoked" ? tokenField : null}
    </GadgetGroup>
  );

  /* ── F: a problem, with its one verb ────────────────────────────── */
  const since = telegram.health?.since ? wireClock(telegram.health.since) : "";
  const problem =
    state === "token_revoked" ? (
      <PaneNotice>
        <span role="alert" data-testid="reach-telegram-health">{telegram.health?.words}</span>
      </PaneNotice>
    ) : state === "bot_blocked" ? (
      <PaneNotice>
        <Said
          verb={
            named ? (
              <Button dense variant="primary" onClick={() => openOutside(`https://t.me/${bot?.username}`)} data-testid="reach-open-bot">
                Open the bot in Telegram
              </Button>
            ) : undefined
          }
        >
          <span role="alert" data-testid="reach-telegram-health">{telegram.health?.words}</span>
        </Said>
      </PaneNotice>
    ) : state === "another_desk" ? (
      <>
        <PaneNotice>
          <Said
            verb={
              <Button dense variant="primary" loading={busy === "use-here"} onClick={acts.useHere} data-testid="reach-use-here">
                Use this desk
              </Button>
            }
          >
            <span role="alert" data-testid="reach-telegram-health">{telegram.health?.words}</span>
          </Said>
        </PaneNotice>
        <GadgetGroup>
          <GadgetRow label="Use this desk" controlWidth="full">
            <span>This desk reads the bot again.</span>
          </GadgetRow>
          <GadgetRow label="Other desk" controlWidth="full">
            <span>
              To stop it, send <code>/revoke</code> to BotFather, then paste the new token here
            </span>
          </GadgetRow>
        </GadgetGroup>
      </>
    ) : state === "unreachable" || (state === "not_checked" && Boolean(paired)) ? (
      <PaneNotice>
        <span role="status" data-testid="reach-telegram-health">
          {telegram.health?.words}
          {state === "unreachable" && since ? ` Since ${since}.` : ""}
        </span>
      </PaneNotice>
    ) : null;

  /* ── B: a token, no chat yet ────────────────────────────────────── */
  if (!paired) {
    return (
      <div data-testid="reach-telegram" data-state={codeOpen ? "code_live" : bot?.checked ? "token_checked" : "token_unchecked"}>
        {problem}
        {!bot?.checked && state === "not_checked" ? (
          <PaneNotice>
            <span role="status" data-testid="reach-telegram-health">{telegram.health?.words}</span>
          </PaneNotice>
        ) : null}
        {refusal ? (
          <PaneNotice>
            <span role="alert" data-testid="reach-refusal">{refusal}</span>
          </PaneNotice>
        ) : null}
        {/* Steps 1 and 2 are done: each is its heading with a check; the
            token's step keeps one fact row, the bot and the way to change it. */}
        <StepHeading number={1} title="Make a bot in Telegram" state="done" testId="reach-step-1" />
        <StepHeading number={2} title="Paste its token" state="done" testId="reach-step-2" />
        {botRows}
        <StepHeading number={3} title="Connect your chat" testId="reach-step-3" />
        <GadgetGroup>
          <GadgetRow label="In Telegram" controlWidth="full">
            <Said
              verb={
                codeOpen && link ? (
                  <Button dense variant="primary" onClick={() => openOutside(link)} data-testid="reach-open-bot" data-feedback-redact="true">
                    Open the bot in Telegram
                  </Button>
                ) : (
                  <Button dense variant="primary" loading={busy === "pair"} disabled={state === "token_revoked"} onClick={acts.pair} data-testid="reach-pair">
                    Get the link
                  </Button>
                )
              }
            >
              Open your bot and press Start.
            </Said>
          </GadgetRow>
          {codeOpen && pairing ? (
            <GadgetRow label="Or send" controlWidth="full">
              <span>
                <code data-testid="reach-pair-code" data-feedback-redact="true">/pair {pairing.words}</code>
                {named ? ` to @${bot?.username}` : " to your bot"}
              </span>
            </GadgetRow>
          ) : null}
          {codeOpen ? (
            <GadgetRow label="Code ends in" controlWidth="full">
              <Said
                verb={
                  <Button dense loading={busy === "pair"} onClick={acts.pair} data-testid="reach-new-code">
                    New code
                  </Button>
                }
              >
                <span data-testid="reach-pair-left">{left} min</span>
              </Said>
            </GadgetRow>
          ) : null}
          {leaves}
        </GadgetGroup>
      </div>
    );
  }

  /* ── D and E: a chat is connected ───────────────────────────────── */
  const test = telegram.last_test ?? null;
  const testWords = test?.sent_at
    ? test.answered_at
      ? `Answered from Telegram ${wireClock(test.answered_at)}`
      : `Sent ${wireClock(test.sent_at)}. Press "It works" in Telegram.`
    : "";
  const halted = state === "token_revoked" || state === "another_desk";
  const question =
    asking === "disconnect" ? (
      <InspectorQuestion
        question={`Disconnect ${paired.name || "this chat"}?`}
        consequence="The bot stays on this desk. This chat gets no more messages."
        cancel={() => setAsking(null)}
        targetId={`chat:${paired.name}:${paired.at ?? ""}`}
        actionId="disconnect"
        testId="reach-disconnect-question"
        verb={{
          label: "Disconnect",
          busy: busy === "unpair",
          testId: "reach-disconnect-confirm",
          run: () => void acts.disconnect().then((done) => (done ? setAsking(null) : undefined)),
        }}
      />
    ) : asking === "remove" ? (
      <InspectorQuestion
        question={`Remove ${botName || "the bot"}?`}
        consequence="The token leaves this Mac and the chat is disconnected. The bot stays in Telegram."
        cancel={() => setAsking(null)}
        targetId={`bot:${bot?.username ?? ""}`}
        actionId="remove"
        testId="reach-remove-question"
        verb={{
          label: "Remove the bot",
          busy: busy === "remove",
          testId: "reach-remove-confirm",
          run: () => void acts.remove(bot?.username ?? "").then((done) => (done ? setAsking(null) : undefined)),
        }}
      />
    ) : null;

  return (
    <div data-testid="reach-telegram" data-state={state === "connected" ? "connected" : state}>
      <PaneActions>
        <Button dense variant={state === "bot_blocked" || halted ? "secondary" : "primary"} loading={busy === "test"} disabled={halted} onClick={acts.sendTest} data-testid="reach-test">
          Send a test
        </Button>
        <Button dense disabled={Boolean(asking)} onClick={() => setAsking("disconnect")} data-testid="reach-unpair">
          Disconnect
        </Button>
        <Button dense disabled={Boolean(asking) || !named} title={named ? undefined : "Telegram has not named this bot yet"} onClick={() => setAsking("remove")} data-testid="reach-remove">
          Remove the bot
        </Button>
      </PaneActions>
      {problem}
      {refusal ? (
        <PaneNotice>
          <span role="alert" data-testid="reach-refusal">{refusal}</span>
        </PaneNotice>
      ) : null}
      {question}
      <InspectorFacts
        name={bot?.name || "Telegram"}
        subtitle={STATE_WORD[state] ?? undefined}
        testId="reach-telegram-facts"
        rows={[
          { label: "Chat", value: paired.name || "Your chat" },
          { label: "Connected", value: paired.at ? wireDayClock(paired.at) : "" },
          { label: "Last answer", value: state === "connected" && telegram.health?.since ? wireDayClock(telegram.health.since) : "" },
          { label: "Test", value: testWords ? <span data-testid="reach-test-state">{testWords}</span> : "" },
          { label: "Sends", value: sends ?? "" },
          { label: "Quiet", value: quiet ?? "" },
        ]}
      />
      {botRows}
      <GadgetGroup>{leaves}</GadgetGroup>
    </div>
  );
}
