// One clock format on the desk (owner decision 2026-11-13). The top bar said
// "12:04 PM" and each window's strip said "12:04" for the same minute. Both
// read `clockOf` now, and `clockOf` reads the system's hour cycle.
import { render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DeskClock } from "../../components/DeskChrome";
import { clockOf, rereadHourCycle, streamTime, wireClock, wireDayClock } from "../format";
import { StatusBar } from "../kit";
import { clock as todayClock } from "../../pullouts/views/today/time";
import { clock as callClock } from "../../calls/PhonePane";
import { keptReceipt } from "../../keptReceipt";

const RealFormat = Intl.DateTimeFormat;

/** The system locale for this test: a call that names no locale gets it. */
function systemLocale(locale: string): void {
  vi.spyOn(Intl, "DateTimeFormat").mockImplementation(
    function (asked?: string | string[], options?: Intl.DateTimeFormatOptions) {
      return new RealFormat(asked ?? locale, options);
    } as unknown as typeof Intl.DateTimeFormat,
  );
  rereadHourCycle();
}

function bothClocks(): { topBar: string; strip: string } {
  const top = render(<DeskClock />);
  const strip = render(<StatusBar inPlace parts={[]} />);
  return {
    topBar: top.container.querySelector(".desk-clock strong")?.textContent ?? "",
    strip: strip.container.querySelector(".kit-statusbar-clock")?.textContent ?? "",
  };
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  rereadHourCycle();
});

describe("the desk has one clock format", () => {
  const afternoon = new Date(2026, 10, 13, 21, 6, 9);
  const noon = new Date(2026, 10, 13, 12, 4, 0);
  const midnight = new Date(2026, 10, 13, 0, 5, 0);

  it("a 12-hour system: the top bar and a window's strip say the same words", () => {
    systemLocale("en-US");
    vi.useFakeTimers({ now: afternoon, toFake: ["Date"] });
    const { topBar, strip } = bothClocks();
    expect(strip).toBe("9:06 PM");
    expect(topBar).toBe(strip);
  });

  it("a 24-hour system: the top bar and a window's strip say the same words", () => {
    systemLocale("en-GB");
    vi.useFakeTimers({ now: afternoon, toFake: ["Date"] });
    const { topBar, strip } = bothClocks();
    expect(strip).toBe("21:06");
    expect(topBar).toBe(strip);
  });

  it("noon and midnight read as a 12-hour clock reads them", () => {
    systemLocale("en-US");
    expect([clockOf(noon), clockOf(midnight), clockOf(afternoon, true)]).toEqual(["12:04 PM", "12:05 AM", "9:06:09 PM"]);
    systemLocale("de-DE");
    expect([clockOf(noon), clockOf(midnight), clockOf(afternoon, true)]).toEqual(["12:04", "00:05", "21:06:09"]);
  });

  it.each([["en-US", "9:06 PM"], ["en-GB", "21:06"]])("time facts follow the system (%s)", (locale, words) => {
    systemLocale(locale);
    expect(wireClock(afternoon)).toBe(words);
    expect(wireDayClock(afternoon)).toBe(`Nov 13, ${words}`);
    expect(streamTime(afternoon)).toBe(words);
    expect(todayClock(afternoon)).toBe(words);
    expect(callClock(afternoon.toISOString())).toBe(words);
    expect(keptReceipt(afternoon.getTime())).toBe(`Kept · ${words}`);
  });
});
