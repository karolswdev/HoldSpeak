/* Settings ▸ Reach (T2; PG-DIRECTION DIR6, DIRECTION-2026-10-31.md §9).
 *
 * The answers are the hub's own, recorded by
 * tests/integration/test_desk_reach_settings.py (web/src/desk/reach/__fixtures__/).
 * Each case drives a press to the rendered outcome. The Telegram tab: the
 * three steps; a token the hub checks with Telegram (named, refused, not
 * checked yet); the link that connects the chat with one press; the test and
 * its answer; each problem with its one verb; Disconnect and Remove asked in
 * the window. Then Telegram's rung and Later means save, and the Reach you
 * rows (moved from Calls ▸ Phone) write his own word over the level. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import paired from "../__fixtures__/reach.paired.json";
import pairing from "../__fixtures__/reach.pairing.json";
import pairingOpen from "../__fixtures__/reach.pairing_open.json";
import saved from "../__fixtures__/reach.saved.json";
import unpaired from "../__fixtures__/reach.unpaired.json";
import phoneOff from "../__fixtures__/reach.phone_off.json";
import anotherDesk from "../__fixtures__/reach.another_desk.json";
import botBlocked from "../__fixtures__/reach.bot_blocked.json";
import keystoreLocked from "../__fixtures__/reach.keystore_locked.json";
import testSent from "../__fixtures__/reach.test_sent.json";
import tested from "../__fixtures__/reach.tested.json";
import tokenChecked from "../__fixtures__/reach.token_checked.json";
import tokenRefused from "../__fixtures__/reach.token_refused.json";
import tokenRevoked from "../__fixtures__/reach.token_revoked.json";
import tokenUnchecked from "../__fixtures__/reach.token_unchecked.json";
import unreachable from "../__fixtures__/reach.unreachable.json";
import useHere from "../__fixtures__/reach.use_here.json";
import needsLater from "../__fixtures__/needs_you.later.json";
import needsSent from "../__fixtures__/needs_you.sent.json";

type Answer = unknown | ((init?: { method?: string; json?: unknown }) => unknown);

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), openSurfaceOr: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../shell")>()),
  openSurfaceOr: mocks.openSurfaceOr,
}));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));

import { ApiError } from "../../../lib/api";
import { SETTINGS_SECTIONS } from "../../../pages/cores/settings/prefs";
import { ReachSettingsPane } from "../ReachSettings";
import { TELEGRAM_LEAVES } from "../TelegramSetup";
import { laterWords, pageWords, type LaterMark, type OpenPage } from "../../reach";

let calls: string[];
const clone = <T,>(value: T): T => structuredClone(value);
function hub(table: Record<string, Answer>) {
  mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
    calls.push(init?.json !== undefined ? `${key} ${JSON.stringify(init.json)}` : key);
    if (!(key in table)) throw new ApiError(404, "Not Found", { detail: "Not Found" });
    const answer = table[key];
    return clone(typeof answer === "function" ? (answer as (i?: typeof init) => unknown)(init) : answer);
  });
}
const strip = vi.fn();
const pane = () => render(<ReachSettingsPane onStatus={strip} quiet={<div data-testid="quiet-rows" />} cadence={<div data-testid="cadence-rows">Notice choices</div>} />);
const telegramState = () => screen.getByTestId("reach-telegram").getAttribute("data-state");

beforeEach(() => {
  calls = [];
  mocks.apiFetch.mockReset();
  mocks.openSurfaceOr.mockReset();
  strip.mockReset();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("Settings ▸ Reach", () => {
  it("Notices reads Reach on the rail (the anchor id stays)", () => {
    expect(SETTINGS_SECTIONS.find((section) => section.id === "notices")?.label).toBe("Reach");
    expect(SETTINGS_SECTIONS.map((section) => section.label)).not.toContain("Notices");
  });

  it("not set up: three numbered steps, one labelled token field, and the egress line one time", async () => {
    hub({ "GET /api/reach": unpaired });
    pane();
    await screen.findByTestId("reach-telegram");
    expect(telegramState()).toBe("not_set_up");
    for (const step of ["1 · Make a bot in Telegram", "2 · Paste its token", "3 · Connect your chat"]) expect(screen.getByText(step)).toBeInTheDocument();
    expect(screen.getByTestId("reach-egress").textContent).toBe(TELEGRAM_LEAVES);
    expect(screen.getAllByTestId("reach-egress")).toHaveLength(1);
    const field = screen.getByLabelText("Bot token");
    expect(field).toHaveAttribute("type", "password");
    expect(field).toHaveAttribute("data-feedback-redact", "true");
    // The token field is live for a person who has a bot; step 3 waits for the token.
    expect(field).not.toBeDisabled();
    expect(screen.getByTestId("reach-pair")).toBeDisabled();
    const opened = vi.spyOn(window, "open").mockImplementation(() => null);
    fireEvent.click(screen.getByTestId("reach-open-botfather"));
    expect(opened).toHaveBeenCalledWith("https://t.me/BotFather", "_blank", "noopener,noreferrer");
    opened.mockRestore();
    await waitFor(() => expect(strip).toHaveBeenLastCalledWith("Telegram is not set up"));
    fireEvent.click(screen.getByRole("tab", { name: "Calls" }));
    expect(screen.getByTestId("reach-phone-state").textContent).toBe(unpaired.channels.phone_app.words);
    expect(screen.getByTestId("reach-calls-state").textContent).toBe(unpaired.channels.calls.words);
    fireEvent.click(screen.getByRole("tab", {name:"When"}));
    expect(screen.getByRole("combobox", { name: "Telegram" })).toHaveValue("at_once");
    fireEvent.click(screen.getByRole("tab", { name: "Brief" }));
    fireEvent.doubleClick(screen.getByRole("row", {name: "Digest and Later"}));
    expect(screen.getByRole("combobox", { name: "Later means" })).toHaveValue("in_2h");
    expect(screen.getByRole("combobox", { name: "Digest" })).toHaveValue("end_of_quiet");
    expect(screen.getByTestId("reach-digest-now")).toBeDisabled();
    // The Reach you rows moved here: one per kind, by the level.
    fireEvent.click(screen.getByRole("tab", { name: "Calls" }));
    const rows = screen.getAllByTestId("phone-reach-row");
    expect(new Set(rows.map((r) => r.getAttribute("data-kind")))).toEqual(new Set(Object.keys(unpaired.ladder.kinds).filter((kind) => kind !== "level")));
    fireEvent.click(screen.getByRole("tab", { name: "When" }));
    expect(screen.getByTestId("quiet-rows")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Calls" }));
    fireEvent.click(screen.getByTestId("reach-phone-open"));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "calls");
  });

  it("shows the selected brief form at once and Return or double-click focuses its first control", async () => {
    hub({"GET /api/reach": paired});
    pane();
    await screen.findByTestId("reach-telegram");
    expect(screen.getAllByRole("tab").length).toBeLessThanOrEqual(4);
    fireEvent.click(screen.getByRole("tab", {name: "Brief"}));
    const row = screen.getByRole("row", {name: "Digest and Later"});
    expect(row.closest('[role="row"]')).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("combobox", {name: "Digest"})).toBeInTheDocument();
    expect(within(screen.getByRole("grid", {name: "Brief choices"})).queryByRole("columnheader")).toBeNull();
    expect(screen.queryByRole("button", {name: "Open choice"})).toBeNull();
    fireEvent.click(screen.getByText("Notices", {exact: true}));
    expect(screen.getByTestId("cadence-rows")).toBeInTheDocument();
    expect(screen.queryByRole("combobox", {name: "Digest"})).toBeNull();
    fireEvent.click(row);
    fireEvent.keyDown(row.closest('[role="row"]')!, {key: "Enter"});
    expect(screen.getByRole("region", {name: "Digest and Later"})).toBeInTheDocument();
    expect(screen.getByRole("combobox", {name: "Digest"})).toHaveFocus();
    fireEvent.doubleClick(row);
    expect(screen.getByRole("combobox", {name: "Digest"})).toHaveFocus();
    expect(screen.queryByRole("button", {name: "Done"})).toBeNull();
    expect(screen.getByRole("combobox", {name: "Digest"})).toBeInTheDocument();
    fireEvent.click(screen.getByText("Notices", {exact: true}));
    fireEvent.click(screen.getByRole("tab", {name: "Telegram"}));
    expect(screen.getByTestId("reach-unpair")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", {name: "Brief"}));
    expect(screen.getByRole("row", {name: "Digest and Later"})).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("combobox", {name: "Digest"})).toBeInTheDocument();
    expect(calls.some((call) => call.startsWith("PUT ") || call.startsWith("DELETE "))).toBe(false);
  });

  it("a token that Telegram knows: the hub names the bot, the token leaves the face, step 3 is live", async () => {
    let stored = false;
    hub({
      "GET /api/reach": () => (stored ? tokenChecked : unpaired),
      "PUT /api/reach/telegram/token": () => {
        stored = true;
        return { token: "keystore", bot: tokenChecked.channels.telegram.bot };
      },
    });
    pane();
    fireEvent.change(await screen.findByLabelText("Bot token"), { target: { value: "6000:abc" } });
    fireEvent.click(screen.getByTestId("reach-token-save"));
    await waitFor(() => expect(calls).toContain('PUT /api/reach/telegram/token {"token":"6000:abc"}'));
    expect((await screen.findByTestId("reach-bot-name")).textContent).toBe("HoldSpeak · @holdspeak_karol_bot");
    expect(telegramState()).toBe("token_checked");
    // The token is not on the face after the save: no field, no value.
    expect(screen.queryByLabelText("Bot token")).toBeNull();
    expect(document.body.innerHTML).not.toContain("6000:abc");
    expect(screen.getByTestId("reach-pair")).not.toBeDisabled();
    await waitFor(() => expect(strip).toHaveBeenLastCalledWith("Telegram waits for your chat"));
  });

  it("a token that Telegram does not know: the hub's sentence, the field kept across a tab change, nothing saved", async () => {
    let stored = false; let attempts = 0;
    hub({
      "GET /api/reach": () => stored ? tokenChecked : unpaired,
      "PUT /api/reach/telegram/token": () => { if (++attempts === 1) throw new ApiError(400, "token_unknown", tokenRefused); stored = true; return { token: "keystore" }; },
    });
    pane();
    const field = await screen.findByLabelText("Bot token");
    fireEvent.change(field, { target: { value: "fixture-bot-token" } });
    fireEvent.click(screen.getByTestId("reach-token-save"));
    expect((await screen.findByTestId("reach-token-refused")).textContent).toBe(tokenRefused.detail);
    expect(field).toHaveValue("fixture-bot-token");
    expect(telegramState()).toBe("not_set_up");
    fireEvent.click(screen.getByRole("tab", { name: "When" }));
    fireEvent.click(screen.getByRole("tab", { name: "Telegram" }));
    expect(screen.getByLabelText("Bot token")).toHaveValue("fixture-bot-token");
    fireEvent.click(screen.getByTestId("reach-token-save"));
    await screen.findByTestId("reach-bot-name");
    expect(screen.queryByLabelText("Bot token")).toBeNull();
    expect(screen.queryByTestId("reach-token-refused")).toBeNull();
  });

  it("a token Telegram has not checked yet says so and can still connect a chat", async () => {
    hub({ "GET /api/reach": tokenUnchecked });
    pane();
    expect((await screen.findByTestId("reach-telegram-health")).textContent).toBe(tokenUnchecked.channels.telegram.health.words);
    expect(telegramState()).toBe("token_unchecked");
    expect(screen.getByTestId("reach-bot-name").textContent).toBe("Token saved");
    expect(screen.getByTestId("reach-pair")).not.toBeDisabled();
  });

  it("Get the link: one press in Telegram connects the chat; the code is a fallback row; then the chat shows", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date(Date.parse(pairing.expires_at) - 9.5 * 60_000));
    let state: unknown = tokenChecked;
    hub({
      "GET /api/reach": () => state,
      "POST /api/reach/telegram/pair": () => { state = pairingOpen; return pairing; },
    });
    pane();
    fireEvent.click(await screen.findByTestId("reach-pair"));
    const open = await screen.findByTestId("reach-open-bot");
    expect(calls).toContain("POST /api/reach/telegram/pair {}");
    expect(telegramState()).toBe("code_live");
    expect(open).toHaveAttribute("data-feedback-redact", "true");
    const opened = vi.spyOn(window, "open").mockImplementation(() => null);
    fireEvent.click(open);
    expect(opened).toHaveBeenCalledWith(pairing.link, "_blank", "noopener,noreferrer");
    opened.mockRestore();
    expect(screen.getByTestId("reach-pair-code")).toHaveAttribute("data-feedback-redact", "true");
    expect(screen.getByTestId("reach-pair-code").textContent).toBe("/pair 482 913");
    expect(screen.getByTestId("reach-pair-left").textContent).toBe("10 min");
    expect(screen.getByTestId("reach-new-code")).toBeInTheDocument();
    state = paired;
    await act(async () => {
      vi.advanceTimersByTime(3_100);
    });
    await waitFor(() => expect(telegramState()).toBe("connected"), { timeout: 5_000 });
    expect(screen.queryByTestId("reach-pair-code")).toBeNull();
    const facts = screen.getByTestId("reach-telegram-facts");
    expect(within(facts).getByText("Karol")).toBeInTheDocument();
    expect(within(facts).getByText("At once")).toBeInTheDocument();
    expect(within(facts).getByText(`${String(paired.quiet_hours.start).padStart(2, "0")}:00 to ${String(paired.quiet_hours.end).padStart(2, "0")}:00`)).toBeInTheDocument();
    await waitFor(() => expect(strip).toHaveBeenLastCalledWith("Telegram connected"));
    fireEvent.click(screen.getByRole("tab", { name: "Brief" }));
    fireEvent.doubleClick(screen.getByRole("row", {name: "Digest and Later"}));
    expect(screen.getByTestId("reach-digest-now")).not.toBeDisabled();
  });

  it("Send a test: the strip says it was sent; the answer from Telegram shows as a fact", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date(Date.parse(testSent.channels.telegram.last_test.sent_at) + 2_000));
    let state: unknown = paired;
    hub({
      "GET /api/reach": () => state,
      "POST /api/reach/telegram/test": () => { state = testSent; return { last_test: testSent.channels.telegram.last_test }; },
    });
    pane();
    fireEvent.click(await screen.findByTestId("reach-test"));
    await waitFor(() => expect(calls).toContain("POST /api/reach/telegram/test {}"));
    expect((await screen.findByTestId("reach-test-state")).textContent).toMatch(/^Sent \d\d:\d\d\. Press "It works" in Telegram\.$/);
    await waitFor(() => expect(strip.mock.calls.at(-1)?.[0]).toMatch(/^Test sent \d\d:\d\d$/));
    state = tested;
    await act(async () => {
      vi.advanceTimersByTime(3_100);
    });
    await waitFor(() => expect(screen.getByTestId("reach-test-state").textContent).toMatch(/^Answered from Telegram \d\d:\d\d$/), { timeout: 5_000 });
  });

  it("each problem is one notice with the hub's sentence and its one verb", async () => {
    const opened = vi.spyOn(window, "open").mockImplementation(() => null);
    // The token was refused: the verb is the token field.
    hub({ "GET /api/reach": tokenRevoked });
    let view = pane();
    expect((await screen.findByTestId("reach-telegram-health")).textContent).toBe(tokenRevoked.channels.telegram.health.words);
    expect(screen.getByLabelText("Bot token")).toBeInTheDocument();
    expect(screen.getByTestId("reach-test")).toBeDisabled();
    expect(screen.queryByTestId("reach-use-here")).toBeNull();
    expect(screen.queryByTestId("reach-open-bot")).toBeNull();
    view.unmount();
    // The chat stopped the bot: the verb opens the bot in Telegram.
    hub({ "GET /api/reach": botBlocked });
    view = pane();
    expect((await screen.findByTestId("reach-telegram-health")).textContent).toBe(botBlocked.channels.telegram.health.words);
    fireEvent.click(screen.getByTestId("reach-open-bot"));
    expect(opened).toHaveBeenCalledWith("https://t.me/holdspeak_karol_bot", "_blank", "noopener,noreferrer");
    expect(screen.queryByLabelText("Bot token")).toBeNull();
    view.unmount();
    // Another desk reads the bot: Use this desk, and how to stop the other one.
    let state: unknown = anotherDesk;
    hub({ "GET /api/reach": () => state, "POST /api/reach/telegram/use-here": () => { state = paired; return useHere; } });
    view = pane();
    expect((await screen.findByTestId("reach-telegram-health")).textContent).toBe(anotherDesk.channels.telegram.health.words);
    expect(screen.getByText("This desk reads the bot again.")).toBeInTheDocument();
    expect(screen.getByText("/revoke")).toBeInTheDocument();
    expect(screen.getByTestId("reach-test")).toBeDisabled();
    fireEvent.click(screen.getByTestId("reach-use-here"));
    await waitFor(() => expect(calls).toContain("POST /api/reach/telegram/use-here {}"));
    await waitFor(() => expect(telegramState()).toBe("connected"));
    view.unmount();
    // Telegram does not answer: the sentence and the time, no verb in the notice.
    hub({ "GET /api/reach": unreachable });
    view = pane();
    const said = await screen.findByTestId("reach-telegram-health");
    expect(said.textContent).toMatch(new RegExp(`^${unreachable.channels.telegram.health.words.replace(/\./g, "\\.")} Since \\d\\d:\\d\\d\\.$`));
    expect(said.closest(".surface-pane-notice")?.querySelector("button")).toBeNull();
    view.unmount();
    // The keystore is not open: the hub's sentence and no field.
    hub({ "GET /api/reach": keystoreLocked });
    pane();
    expect((await screen.findByTestId("reach-telegram-health")).textContent).toBe(keystoreLocked.channels.telegram.keystore_words);
    expect(screen.queryByLabelText("Bot token")).toBeNull();
    expect(screen.queryByTestId("reach-pair")).toBeNull();
    opened.mockRestore();
  });

  it("Remove the bot asks in the window, names the bot, focuses Cancel and sends the bound user name", async () => {
    let state: unknown = paired;
    hub({
      "GET /api/reach": () => state,
      "POST /api/reach/telegram/remove": () => { state = unpaired; return { token: "missing", paired: null, bot: null }; },
    });
    pane();
    fireEvent.click(await screen.findByTestId("reach-remove"));
    const question = await screen.findByTestId("reach-remove-question");
    expect(within(question).getByText("Remove HoldSpeak · @holdspeak_karol_bot?")).toBeInTheDocument();
    expect(within(question).getByRole("button", { name: "Cancel" })).toHaveFocus();
    expect(calls.some((call) => call.startsWith("POST /api/reach/telegram/remove"))).toBe(false);
    fireEvent.click(within(question).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByTestId("reach-remove-question")).toBeNull();
    fireEvent.click(screen.getByTestId("reach-remove"));
    fireEvent.click(await screen.findByTestId("reach-remove-confirm"));
    await waitFor(() => expect(calls).toContain('POST /api/reach/telegram/remove {"username":"holdspeak_karol_bot"}'));
    await waitFor(() => expect(telegramState()).toBe("not_set_up"));
    expect(screen.queryByTestId("reach-remove-question")).toBeNull();
  });

  it("Disconnect asks in the window and keeps the bot; a refusal says the hub's sentence", async () => {
    let state: unknown = paired; let attempts = 0;
    hub({
      "GET /api/reach": () => state,
      "DELETE /api/reach/telegram/pair": () => {
        if (++attempts === 1) throw new ApiError(503, "keystore_unavailable", { code: "keystore_unavailable", detail: "The keystore is not open. Unlock it and try again." });
        state = tokenChecked;
        return { paired: null };
      },
    });
    pane();
    fireEvent.click(await screen.findByTestId("reach-unpair"));
    const question = await screen.findByTestId("reach-disconnect-question");
    expect(within(question).getByText("Disconnect Karol?")).toBeInTheDocument();
    expect(within(question).getByRole("button", { name: "Cancel" })).toHaveFocus();
    fireEvent.click(screen.getByTestId("reach-disconnect-confirm"));
    expect((await screen.findByTestId("reach-refusal")).textContent).toBe("The keystore is not open. Unlock it and try again.");
    expect(telegramState()).toBe("connected");
    fireEvent.click(screen.getByTestId("reach-disconnect-confirm"));
    await waitFor(() => expect(telegramState()).toBe("token_checked"));
    expect(screen.getByTestId("reach-bot-name").textContent).toBe("HoldSpeak · @holdspeak_karol_bot");
  });

  it("DIR7: the ladder's rungs in the hub's order, each with its wait; Phone saves through PUT /api/reach", async () => {
    hub({ "GET /api/reach": paired, "PUT /api/reach": phoneOff });
    pane();
    fireEvent.click(screen.getByRole("tab", {name:"When"}));
    const ladder = await screen.findByTestId("reach-ladder");
    await waitFor(() => expect(within(ladder).getAllByRole("combobox").length).toBe(2));
    const labels = [...ladder.querySelectorAll(".gadget-row-label")].map((node) => node.childNodes[0]?.textContent?.trim());
    expect(labels).toEqual(["Desk", "Phone", "Telegram", "Call"]);
    expect(within(ladder).getByTestId("reach-rung-desk").textContent).toBe("At once");
    expect(within(ladder).getByRole("combobox", { name: "Phone" })).toHaveValue("on");
    fireEvent.change(within(ladder).getByRole("combobox", { name: "Phone" }), {
      target: { value: "off" },
    });
    await waitFor(() => expect(calls).toContain('PUT /api/reach {"phone_app":"off"}'));
    await waitFor(() =>
      expect(
        within(screen.getByTestId("reach-ladder")).getByRole("combobox", {
          name: "Phone",
        }),
      ).toHaveValue("off"),
    );
  });

  it("Telegram's rung, the digest and Later means save through PUT /api/reach", async () => {
    hub({ "GET /api/reach": paired, "PUT /api/reach": saved });
    pane();
    fireEvent.click(screen.getByRole("tab", {name:"When"}));
    const rung = await screen.findByRole("combobox", { name: "Telegram" });
    fireEvent.change(rung, { target: { value: "after_10" } });
    await waitFor(() => expect(calls).toContain('PUT /api/reach {"telegram":"after_10"}'));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Telegram" })).toHaveValue("after_10"));
    fireEvent.click(screen.getByRole("tab", { name: "Brief" }));
    fireEvent.doubleClick(screen.getByRole("row", {name: "Digest and Later"}));
    expect(screen.getByRole("combobox", { name: "Digest" })).toHaveValue("7");
    fireEvent.change(screen.getByRole("combobox", { name: "Digest" }), {
      target: { value: "end_of_quiet" },
    });
    await waitFor(() => expect(calls).toContain('PUT /api/reach {"digest":"end_of_quiet"}'));
    fireEvent.change(screen.getByRole("combobox", { name: "Later means" }), {
      target: { value: "tomorrow" },
    });
    await waitFor(() => expect(calls).toContain('PUT /api/reach {"later_means":"tomorrow"}'));
  });

  it("a refused Reach you choice keeps the last value and can be tried again; Use the set clears it", async () => {
    let own: Record<string, string> = {};
    const withOwn = () => {
      const answer = clone(paired) as typeof paired & {
        ladder: { kinds: Record<string, unknown> };
      };
      for (const [kind, word] of Object.entries(own)) {
        answer.ladder.kinds[kind] = {
          ...(answer.ladder.kinds[kind] as object),
          word,
          own: true,
        };
      }
      return answer;
    };
    let refuse = true;
    hub({
      "GET /api/reach": withOwn,
      "PUT /api/settings": (init?: { json?: unknown }) => {
        if (refuse) { refuse = false; throw new ApiError(503, "Unavailable", {error: "Settings unavailable"}); }
        own = (init?.json as { calls: { phone_reach: Record<string, string> } }).calls.phone_reach;
        return {};
      },
    });
    pane();
    fireEvent.click(screen.getByRole("tab", { name: "Calls" }));
    const row = (await screen.findAllByTestId("phone-reach-row")).find((r) => r.getAttribute("data-kind") === "program_done")!;
    const choice = within(row).getByRole("combobox");
    const before = (choice as HTMLSelectElement).value;
    fireEvent.change(choice, {target: {value: "nothing"}});
    await screen.findByTestId("phone-settings-refusal");
    expect(choice).toHaveValue(before);
    fireEvent.change(choice, {target: {value: "nothing"}});
    await waitFor(() => expect(calls).toContain('PUT /api/settings {"calls":{"phone_reach":{"program_done":"nothing"}}}'));
    await waitFor(() => expect(row.getAttribute("data-channel")).toBe("nothing"));
    expect(screen.getByTestId("phone-reach-level").textContent).toMatch(/^Your choices over Control: /);
    fireEvent.click(screen.getByTestId("phone-reach-reset"));
    await waitFor(() => expect(calls).toContain('PUT /api/settings {"calls":{"phone_reach":{}}}'));
    await waitFor(() => expect(row.getAttribute("data-channel")).toBe("message"));
  });
});

describe("the line of a sent or deferred item (the Needs you row and the Program window's Your turn row)", () => {
  const clock = (stamp: string) => {
    const at = new Date(stamp);
    return `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
  };
  it("says Sent to Telegram with its time and the page's end, never a chip", () => {
    const page = needsSent.items[0].program.page as OpenPage;
    expect(pageWords(page)).toBe(`Sent to Telegram ${clock(String(page.sent?.at))} · page open until ${clock(page.expires_at)}`);
  });
  it("says Later · back at HH:MM and the channel it was said on", () => {
    const later = needsLater.items[0].later as LaterMark;
    expect(laterWords(later)).toBe(`Later · back at ${clock(later.until)}`);
    expect(laterWords({ ...later, via: "telegram" })).toBe(`Later · back at ${clock(later.until)} · from Telegram`);
    expect(laterWords(null)).toBe("");
  });
});
