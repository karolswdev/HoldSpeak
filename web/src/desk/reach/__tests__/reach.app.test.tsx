/* Settings ▸ Reach (T2; PG-DIRECTION DIR6, DIRECTION-2026-10-31.md §9).
 *
 * The answers are the hub's own, recorded by
 * tests/integration/test_desk_reach_settings.py (web/src/desk/reach/__fixtures__/).
 * Each case drives a press to the rendered outcome: each row draws its
 * state; Pair Telegram shows the one-time code in place and its dot breathes
 * until the chat pairs; Unpair; the bot token in the keystore; Telegram's
 * rung and Later means save; the Reach you rows (moved from Calls ▸ Phone)
 * write his own word over the level. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import paired from "../__fixtures__/reach.paired.json";
import pairing from "../__fixtures__/reach.pairing.json";
import pairingOpen from "../__fixtures__/reach.pairing_open.json";
import saved from "../__fixtures__/reach.saved.json";
import unpaired from "../__fixtures__/reach.unpaired.json";
import phoneOff from "../__fixtures__/reach.phone_off.json";
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
import { ReachSettingsPane, TELEGRAM_EGRESS } from "../ReachSettings";
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
const pane = () => render(<ReachSettingsPane quiet={<div data-testid="quiet-rows" />} cadence={<div data-testid="cadence-rows">Notice choices</div>} />);

beforeEach(() => {
  calls = [];
  mocks.apiFetch.mockReset();
  mocks.openSurfaceOr.mockReset();
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

  it("unpaired, no token: each row draws its state; the egress fact is on the Telegram row", async () => {
    hub({ "GET /api/reach": unpaired });
    pane();
    expect((await screen.findByTestId("reach-telegram-state")).textContent).toBe("Not paired");
    expect(screen.getByTestId("reach-egress").textContent).toBe(TELEGRAM_EGRESS);
    expect(screen.getAllByTestId("reach-egress")).toHaveLength(1);
    expect(screen.getByLabelText("Bot token")).toHaveAttribute("type", "password");
    expect(screen.getByTestId("reach-pair")).toBeDisabled();
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
    fireEvent.click(screen.getByRole("tab", { name: "Channels" }));
    fireEvent.click(screen.getByTestId("reach-phone-open"));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "calls");
  });

  it("shows the selected brief form at once and Return or double-click focuses its first control", async () => {
    hub({"GET /api/reach": paired});
    pane();
    await screen.findByTestId("reach-token");
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
    fireEvent.click(screen.getByRole("tab", {name: "Channels"}));
    expect(screen.getByTestId("reach-unpair")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", {name: "Brief"}));
    expect(screen.getByRole("row", {name: "Digest and Later"})).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("combobox", {name: "Digest"})).toBeInTheDocument();
    expect(calls.some((call) => call.startsWith("PUT ") || call.startsWith("DELETE "))).toBe(false);
  });

  it("the bot token goes to the keystore; the row then says so with Replace", async () => {
    let stored = false;
    hub({
      "GET /api/reach": () => (stored ? pairingOpen : unpaired),
      "PUT /api/reach/telegram/token": () => {
        stored = true;
        return { token: "keystore" };
      },
    });
    pane();
    await screen.findByTestId("reach-token");
    fireEvent.change(within(screen.getByTestId("reach-token")).getByLabelText("Bot token"), { target: { value: "6000:abc" } });
    fireEvent.click(screen.getByTestId("reach-token-save"));
    await waitFor(() => expect(calls).toContain('PUT /api/reach/telegram/token {"token":"6000:abc"}'));
    await waitFor(() => expect(screen.queryByLabelText("Bot token")).toBeNull());
    expect(screen.getByTestId("reach-token-replace")).toBeInTheDocument();
    expect(screen.getByTestId("reach-pair")).not.toBeDisabled();
  });

  it("keeps a refused bot token across tab changes and clears it only after the keystore accepts it", async () => {
    let stored = false; let attempts = 0;
    hub({
      "GET /api/reach": () => stored ? pairingOpen : unpaired,
      "PUT /api/reach/telegram/token": () => { if (++attempts === 1) throw new ApiError(503, "Keystore locked", { error: "Keystore locked" }); stored = true; return { saved: true }; },
    });
    pane();
    const field = await screen.findByLabelText("Bot token");
    fireEvent.change(field, { target: { value: "fixture-bot-token" } });
    fireEvent.click(screen.getByTestId("reach-token-save"));
    await screen.findByTestId("reach-refusal");
    expect(field).toHaveValue("fixture-bot-token");
    fireEvent.click(screen.getByRole("tab", { name: "Channels" }));
    expect(screen.getByLabelText("Bot token")).toHaveValue("fixture-bot-token");
    fireEvent.click(screen.getByTestId("reach-token-save"));
    await screen.findByTestId("reach-token-replace");
    expect(screen.queryByLabelText("Bot token")).toBeNull();
  });

  it("Pair Telegram shows the code in place; its dot breathes until the chat pairs; then Unpair", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let state: unknown = pairingOpen;
    hub({
      "GET /api/reach": () => state,
      "POST /api/reach/telegram/pair": pairing,
      "DELETE /api/reach/telegram/pair": () => {
        state = unpaired;
        return { paired: null };
      },
    });
    pane();
    fireEvent.click(await screen.findByTestId("reach-pair"));
    const sheet = await screen.findByTestId("reach-pair-sheet");
    expect(within(sheet).getByTestId("reach-pair-code")).toHaveAttribute("data-feedback-redact", "true");
    expect(within(sheet).getByTestId("reach-pair-code").textContent).toBe("/pair 482 913");
    expect(sheet.textContent).toContain("Send /pair 482 913 to your bot");
    expect(within(sheet).getByTestId("reach-pair-left").querySelector("[data-live]")).toBeTruthy();
    expect(screen.getByTestId("reach-telegram-state").textContent).toBe("Waiting for your bot");
    expect(calls).toContain("POST /api/reach/telegram/pair {}");
    state = paired;
    await act(async () => {
      vi.advanceTimersByTime(3_100);
    });
    // Under a loaded machine the poll's read can take more than the default
    // second (it flaked in quick checks 2026-11-01): wait up to five.
    await waitFor(() => expect(screen.queryByTestId("reach-pair-sheet")).toBeNull(), { timeout: 5_000 });
    expect(screen.queryByTestId("reach-telegram-state")).toBeNull();
    expect(screen.getByTestId("reach-unpair")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Brief" }));
    fireEvent.doubleClick(screen.getByRole("row", {name: "Digest and Later"}));
    expect(screen.getByTestId("reach-digest-now")).not.toBeDisabled();
    fireEvent.click(screen.getByRole("tab", { name: "Channels" }));
    fireEvent.click(screen.getByTestId("reach-unpair"));
    await waitFor(() => expect(calls).toContain("DELETE /api/reach/telegram/pair"));
    await waitFor(() => expect(screen.getByTestId("reach-telegram-state").textContent).toBe("Not paired"), { timeout: 5_000 });
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
