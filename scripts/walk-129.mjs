/*
 * HS-129-11 live desk walk. Run through dw evidence capture; it writes screenshots
 * into the phase asset directory and fails on a geometry or console violation.
 */
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const base = "http://127.0.0.1:61308/?token=uMcN-J7wwRrQRTWcac5Ucc_2Wf9kv6wf";
const out = "/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-129-one-grammar/assets/hs-129-11";
mkdirSync(out, { recursive: true });

const desktop = { width: 1440, height: 900 };
const mobile = { width: 393, height: 852 };

// Every walked surface must declare its frame contract. `none` is also an
// assertion: egress/Info cards deliberately have no footer, and desk-floor
// documents deliberately have no native shell to exercise.
const WINDOW = { head: "required", body: "required", foot: "required", sheet: "required" };
const ANATOMY = {
  Intelligence: WINDOW,
  Speak: WINDOW,
  Meetings: WINDOW,
  Agents: WINDOW,
  Settings: WINDOW,
  "Desk memory": WINDOW,
  Delivery: WINDOW,
  Panes: WINDOW,
  "Intelligence Brief": WINDOW,
  "Intelligence Follow-through": WINDOW,
  "Intelligence Receipts": WINDOW,
  "Meetings detail": WINDOW,
  "Settings Transcription": WINDOW,
  "Settings Guide": WINDOW,
  "Go *": WINDOW,
  "Object *": WINDOW,
  "New Note editor": WINDOW,
  "Desk memory": { head: "none", body: "none", foot: "none", sheet: "none", reason: "dock command with no native surface" },
  Panes: { head: "none", body: "none", foot: "none", sheet: "none", reason: "dock command with no native surface" },
  "Mobile Desk memory": { head: "none", body: "none", foot: "none", sheet: "none", reason: "dock command with no native surface" },
  "Mobile Panes": { head: "none", body: "none", foot: "none", sheet: "none", reason: "dock command with no native surface" },
  "Mobile *": WINDOW,
  "Trust egress": { head: "required", body: "required", foot: "none", sheet: "none", reason: "fixed egress card, not a sheet" },
  "Info *": { head: "required", body: "required", foot: "none", sheet: "none", reason: "inspection card, not a sheet" },
  "Design components": WINDOW,
};

function anatomyFor(surface) {
  const exact = ANATOMY[surface];
  if (exact) return exact;
  const wildcard = Object.entries(ANATOMY).find(([name]) => name.endsWith("*") && surface.startsWith(name.slice(0, -1)));
  if (wildcard) return wildcard[1];
  throw new Error(`Missing anatomy declaration for ${surface}`);
}

const results = [];
const violations = [];
const consoleErrors = [];
const warnings = new Set();

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const slug = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function fail(surface, message) {
  const finding = `${surface}: ${message}`;
  violations.push(finding);
  console.log(`FAIL ${finding}`);
}

async function reset(page, viewport = desktop, clearPanels = true) {
  // The dedicated mobile context is born at its viewport; changing it after
  // desktop walks can transiently hide the menu bar in Chromium.
  if (clearPanels) await page.setViewportSize(viewport);
  await page.goto(base, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".desk-world-canvas");
  if (clearPanels) {
    // Windows are persisted separately from the token: clear only their placement/open state.
    await page.evaluate(() => {
      localStorage.removeItem("hs.desk.panels");
      localStorage.removeItem("hs.desk.open-windows");
    });
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".desk-world-canvas");
  }
  await sleep(1200);
}

const shellSelector = ".desk-window-shell, .desk-pullout, .desk-surface-window, .desk-trust-window";

async function frontShell(page) {
  return page.locator(shellSelector).last();
}

async function snapshot(page, surface, state) {
  await page.screenshot({ path: `${out}/${slug(surface)}-${state}.png` });
}

async function geometry(page) {
  return page.evaluate(() => {
    const candidates = [...document.querySelectorAll(".desk-window-shell, .desk-pullout, .desk-surface-window, .desk-trust-window")]
      .filter((node) => {
        const box = node.getBoundingClientRect();
        return box.width > 0 && box.height > 0;
      });
    const shell = candidates.at(-1);
    if (!shell) return null;
    const s = shell.getBoundingClientRect();
    const shellStyle = getComputedStyle(shell);
    const foot = shell.querySelector(".surface-footer");
    const head = shell.querySelector(".desk-pullout-head");
    const body = shell.querySelector(".desk-surface-body, .desk-pullout-body, .desk-zone-body");
    const f = foot?.getBoundingClientRect();
    const h = head?.getBoundingClientRect();
    const b = body?.getBoundingClientRect();
    const doc = document.documentElement;
    return {
      shell: { top: s.top, bottom: s.bottom, height: s.height },
      foot: f && { top: f.top, bottom: f.bottom, height: f.height },
      head: h && { top: h.top, bottom: h.bottom },
      body: b && { top: b.top, bottom: b.bottom, scrollHeight: body.scrollHeight, clientHeight: body.clientHeight, scrollTop: body.scrollTop },
      bodyScrollable: Boolean(body && body.scrollHeight > body.clientHeight + 1),
      bodyOverflowX: Boolean(body && body.scrollWidth > body.clientWidth),
      overflowSources: body
        ? [...body.querySelectorAll("*")]
            .filter((node) => node.scrollWidth > node.clientWidth + 1)
            .slice(0, 4)
            .map((node) => `${node.tagName.toLowerCase()}.${[...node.classList].join(".") || "(no-class)"} ${node.clientWidth}/${node.scrollWidth}`)
        : [],
      pageOverflowX: Math.max(document.body.scrollWidth, doc.scrollWidth) > doc.clientWidth,
      viewportHeight: window.innerHeight,
      viewportWidth: window.innerWidth,
      isSheet: shell.classList.contains("is-sheet"),
      sheetMaxHeight: parseFloat(shellStyle.maxHeight) || 0,
      workBand: {
        top: parseFloat(getComputedStyle(doc).getPropertyValue("--desk-work-top")) || 0,
        bottom: parseFloat(getComputedStyle(doc).getPropertyValue("--desk-work-bottom")) || 0,
      },
    };
  });
}

function assertGeometry(surface, state, before, after = before, { headStable = false } = {}) {
  const anatomy = anatomyFor(surface);
  if (!after) return fail(surface, `${state}: no visible window shell`);
  for (const part of ["head", "body", "foot"]) {
    if (anatomy[part] === "required" && !after[part]) fail(surface, `${state}: missing required ${part}`);
    if (anatomy[part] === "none" && after[part]) fail(surface, `${state}: unexpected ${part}`);
  }
  if (anatomy.foot === "required" && after.foot && Math.abs(after.shell.bottom - after.foot.bottom) > 3)
    fail(surface, `${state}: footer gap ${Math.abs(after.shell.bottom - after.foot.bottom).toFixed(1)}px`);
  if (headStable && anatomy.head === "required" && after.head && before?.head && Math.abs(before.head.top - after.head.top) > 3)
    fail(surface, `${state}: title bar moved ${Math.abs(before.head.top - after.head.top).toFixed(1)}px while body scrolled`);
  if (after.pageOverflowX || after.bodyOverflowX)
    fail(surface, `${state}: horizontal overflow${after.overflowSources.length ? ` (${after.overflowSources.join("; ")})` : ""}`);
  if (after.viewportWidth <= 720 && anatomy.sheet === "required" && !after.isSheet)
    fail(surface, `${state}: expected the small-width sheet form`);
  if (after.isSheet) {
    if (anatomy.sheet !== "required") fail(surface, `${state}: rendered a sheet although anatomy says sheet:none`);
    const designedTop = after.viewportHeight - after.sheetMaxHeight;
    if (after.sheetMaxHeight <= 0 || after.shell.top < designedTop - 1)
      fail(surface, `${state}: sheet top ${after.shell.top.toFixed(1)} above CSS max-height offset ${designedTop.toFixed(1)}`);
    if (Math.abs(after.shell.bottom - after.viewportHeight) > 3)
      fail(surface, `${state}: sheet bottom ${after.shell.bottom.toFixed(1)} is not viewport-flush ${after.viewportHeight.toFixed(1)}`);
    if (anatomy.head === "required" && after.head && Math.abs(after.head.top - after.shell.top) > 3)
      fail(surface, `${state}: sheet head is not pinned at sheet top`);
  } else {
    const bandTop = after.workBand.top;
    const bandBottom = after.viewportHeight - after.workBand.bottom;
    if (after.shell.height > bandBottom - bandTop + 1 || after.shell.top < bandTop - 1 || after.shell.bottom > bandBottom + 1)
      fail(surface, `${state}: shell ${after.shell.top.toFixed(1)}–${after.shell.bottom.toFixed(1)} outside working band ${bandTop.toFixed(1)}–${bandBottom.toFixed(1)}`);
  }
}

async function scrollAfterLayout(page, surface, state, baseline, states) {
  if (!baseline?.bodyScrollable) return;
  await page.evaluate(() => {
    const shells = [...document.querySelectorAll(".desk-window-shell, .desk-pullout, .desk-surface-window, .desk-trust-window")];
    const shell = shells.filter((node) => node.getBoundingClientRect().width > 0).at(-1);
    const body = shell?.querySelector(".desk-surface-body, .desk-pullout-body, .desk-zone-body");
    if (body) body.scrollTop = (body.scrollHeight - body.clientHeight) * 0.5;
  });
  await sleep(180);
  const measured = await geometry(page);
  assertGeometry(surface, `${state}-scroll-mid`, baseline, measured, { headStable: true });
  await snapshot(page, surface, `${state}-scroll-mid`);
  states.push(`${state}-scroll-mid`);
}

async function exerciseWindow(page, surface, { resize = true, maximize = true } = {}) {
  const states = [];
  const initial = await geometry(page);
  if (!initial) {
    const anatomy = anatomyFor(surface);
    if (anatomy.head !== "none" || anatomy.body !== "none" || anatomy.foot !== "none")
      fail(surface, "default: missing required native shell");
    const overflow = await page.evaluate(() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > document.documentElement.clientWidth);
    if (overflow) fail(surface, "default: horizontal overflow without a native shell");
    await snapshot(page, surface, "default");
    states.push(`default (non-window: ${anatomy.reason || "undeclared reason"})`);
    return states;
  }
  assertGeometry(surface, "default", initial);
  await snapshot(page, surface, "default");
  states.push("default");

  if (initial.bodyScrollable) {
    for (const [state, fraction] of [["scroll-top", 0], ["scroll-mid", 0.5], ["scroll-bottom", 1]]) {
      await page.evaluate((amount) => {
        const shells = [...document.querySelectorAll(".desk-window-shell, .desk-pullout, .desk-surface-window, .desk-trust-window")];
        const shell = shells.filter((node) => node.getBoundingClientRect().width > 0).at(-1);
        const body = shell?.querySelector(".desk-surface-body, .desk-pullout-body, .desk-zone-body");
        if (body) body.scrollTop = (body.scrollHeight - body.clientHeight) * amount;
      }, fraction);
      await sleep(180);
      const measured = await geometry(page);
      assertGeometry(surface, state, initial, measured, { headStable: true });
      await snapshot(page, surface, state);
      states.push(state);
    }
  }

  const shell = await frontShell(page);
  const grip = shell.locator(".desk-window-grip, .desk-window-resize-grip, .desk-pullout-resize-grip, [class*='resize-grip']").last();
  if (resize && await grip.count() && await grip.isVisible()) {
    const box = await grip.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x - 120, box.y - 247, { steps: 12 });
      await page.mouse.up();
      await sleep(250);
      const measured = await geometry(page);
      assertGeometry(surface, "resized-small", initial, measured);
      await snapshot(page, surface, "resized-small");
      states.push("resized-small");
      await scrollAfterLayout(page, surface, "resized-small", measured, states);
    }
  }

  const max = shell.locator("button[aria-label*='Maximize' i], button[title*='Maximize' i], .desk-window-maximize").last();
  if (maximize && await max.count() && await max.isVisible()) {
    await max.click();
    await sleep(250);
    const measured = await geometry(page);
    assertGeometry(surface, "maximized", initial, measured);
    await snapshot(page, surface, "maximized");
    states.push("maximized");
    await scrollAfterLayout(page, surface, "maximized", measured, states);
  }
  return states;
}

async function openGo(page) {
  const button = page.locator(".desk-verbbar-title").filter({ hasText: "Go" }).last();
  await button.waitFor({ state: "visible", timeout: 10000 });
  try {
    await button.click({ timeout: 2500 });
  } catch {
    await button.focus();
    await page.keyboard.press("Enter");
  }
}

async function openDock(page, name) {
  const button = name === "Intelligence"
    ? page.locator(".desk-dock button[aria-label^='Intelligence']").first()
    : page.getByRole("button", { name: new RegExp(`^${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`) }).last();
  await button.waitFor({ state: "visible", timeout: 10000 });
  try {
    await button.click({ timeout: 2500 });
  } catch {
    // An ambient sprite can overlap the dock; its semantic button remains keyboard-operable.
    await button.focus();
    await page.keyboard.press("Enter");
  }
  await sleep(1800);
}

async function createNoteAndAwaitEditor(page, menuItem) {
  const beforeRefs = await page.evaluate(() => (window.__hsWorldProbe?.() ?? []).map((item) => item.ref));
  await menuItem.click();
  const ref = await page.waitForFunction((knownRefs) => {
    const created = (window.__hsWorldProbe?.() ?? []).find((item) => item.title === "New note" && !knownRefs.includes(item.ref));
    return created?.ref || null;
  }, beforeRefs, { timeout: 10000 });
  await page.waitForFunction((createdRef) => {
    const candidate = (window.__hsWorldProbe?.() ?? []).find((item) => item.ref === createdRef);
    return Boolean(candidate && document.querySelector(".desk-window-shell, .desk-pullout, .desk-surface-window"));
  }, await ref.jsonValue(), { timeout: 10000 });
}

async function openDeskObject(page, title) {
  const target = await page.evaluate((wantedTitle) => {
    const object = (window.__hsWorldProbe?.() ?? []).find((candidate) => candidate.title === wantedTitle);
    if (!object) return null;
    for (const dy of [0, -28, -48]) {
      const x = object.x, y = object.y + dy;
      const element = document.elementFromPoint(x, y);
      const hit = window.__hsWorldHitProbe?.(x, y);
      if ((element?.classList.contains("desk-world-canvas") || element?.classList.contains("desk-vignette")) && hit?.type === "object" && hit.ref === object.ref)
        return { x, y, title: object.title, ref: object.ref };
    }
    return null;
  }, title);
  if (!target) throw new Error(`No reachable desk object titled ${JSON.stringify(title)}`);
  await page.mouse.dblclick(target.x, target.y);
  await sleep(450);
  return target;
}

async function openZone(page) {
  const target = await page.evaluate(() => {
    for (const zone of window.__hsWorldZoneProbe?.() ?? []) {
      const x = zone.x, y = zone.y + 6;
      if (window.__hsWorldHitProbe?.(x, y)?.type === "zone") return { x, y, id: zone.id };
    }
    return null;
  });
  if (!target) throw new Error("No reachable zone body");
  await page.mouse.dblclick(target.x, target.y);
  await sleep(450);
  return target;
}

async function record(surface, states) {
  const anatomy = anatomyFor(surface);
  const verdict = violations.some((item) => item.startsWith(`${surface}:`)) ? "FAIL" : "PASS";
  results.push({ surface, anatomy, states: states.join(", ") || "default", verdict });
  console.log(`WALK ${surface} | ${anatomy.head}/${anatomy.body}/${anatomy.foot} | ${states.join(", ") || "default"} | ${verdict}`);
}

const dockSurfaces = ["Intelligence", "Speak", "Meetings", "Agents", "Settings", "Desk memory", "Delivery", "Panes"];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: desktop });
page.on("console", (message) => {
  if (message.type() !== "error") return;
  const text = message.text();
  if (/pixi|webgl|gpu stall|loadParser|deprecated/i.test(text)) warnings.add(text);
  else consoleErrors.push(text);
});
page.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));

try {
  for (const dock of dockSurfaces) {
    await reset(page);
    await openDock(page, dock);
    const states = await exerciseWindow(page, dock);
    await record(dock, states);
  }

  // Intelligence's three named faces are independent evidence states.
  for (const view of ["Brief", "Follow-through", "Receipts"]) {
    const surface = `Intelligence ${view}`;
    await reset(page); await openDock(page, "Intelligence");
    await page.locator(`.intelligence-segment:has-text("${view}")`).click(); await sleep(300);
    await record(surface, await exerciseWindow(page, surface));
  }

  // A detail is required in addition to the dock's Meeting list.
  await reset(page); await openDock(page, "Meetings");
  const row = page.locator(".surface-ledger-line").first();
  if (await row.count()) { await row.click(); await sleep(1800); await record("Meetings detail", await exerciseWindow(page, "Meetings detail")); }
  else { fail("Meetings detail", "no scriptable meeting ledger row"); await record("Meetings detail", ["unreachable"]); }

  // Settings's named faces.
  for (const face of ["Transcription", "Guide"]) {
    const surface = `Settings ${face}`;
    await reset(page); await openDock(page, "Settings");
    const target = page.getByText(new RegExp(`^${face}$`, "i")).last();
    if (await target.count()) { await target.click(); await sleep(1800); await record(surface, await exerciseWindow(page, surface)); }
    else fail(surface, "face not present");
  }

  // Enumerate and walk precisely what this live Go menu renders.
  await reset(page);
  await openGo(page);
  const goEntries = await page.locator("[role=menuitem]").evaluateAll((items) => items.map((item) => item.innerText.split("\n")[0].trim()));
  console.log(`GO ENTRIES: ${goEntries.join(" | ")}`);
  for (const name of goEntries) {
    const surface = `Go ${name}`;
    await reset(page); await page.getByRole("button", { name: "Go", exact: true }).click();
    await page.getByRole("menuitem", { name: new RegExp(`^${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`) }).click();
    await sleep(400);
    await record(surface, await exerciseWindow(page, surface));
  }

  // One fresh canvas context mirrors the inherited engine-hit helper exactly.
  const objectContext = await browser.newContext({ viewport: desktop });
  const objectPage = await objectContext.newPage();
  objectPage.on("console", (message) => {
    if (message.type() !== "error") return;
    const text = message.text();
    if (/pixi|webgl|gpu stall|loadParser|deprecated/i.test(text)) warnings.add(text);
    else consoleErrors.push(text);
  });
  objectPage.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));
  await objectPage.goto(base, { waitUntil: "networkidle" });
  await objectPage.waitForSelector(".desk-world-canvas");
  await sleep(1200);
  for (const kind of ["zone", "meeting:", "artifact:", "workbench:"]) {
    const surface = `Object ${kind.replace(/:$/, "")}`;
    try {
      if (kind === "zone") await openZone(objectPage);
      else {
        const title = await objectPage.evaluate((prefix) => (window.__hsWorldProbe?.() ?? []).find((item) => item.ref.startsWith(prefix))?.title, kind);
        if (!title) throw new Error(`${kind} absent from this live desk`);
        await openDeskObject(objectPage, title);
      }
      await record(surface, await exerciseWindow(objectPage, surface));
      await objectPage.keyboard.press("Escape");
      await sleep(250);
    } catch (error) {
      fail(surface, error.message);
      await record(surface, ["unreachable"]);
    }
  }
  await objectContext.close();

  await reset(page);
  await page.getByRole("button", { name: /Privacy and trust/ }).click(); await sleep(300);
  await record("Trust egress", await exerciseWindow(page, "Trust egress"));

  await reset(page);
  await page.goto("http://127.0.0.1:61308/design/components?token=uMcN-J7wwRrQRTWcac5Ucc_2Wf9kv6wf", { waitUntil: "domcontentloaded" }); await sleep(500);
  await record("Design components", await exerciseWindow(page, "Design components"));

  // The small-width pass gets a fresh browser context, independent of the
  // desktop app's route and persisted room state.
  const mobileBrowser = await chromium.launch({ headless: true });
  const mobileContext = await mobileBrowser.newContext({ viewport: mobile });
  const mobilePage = await mobileContext.newPage();
  mobilePage.on("console", (message) => {
    if (message.type() !== "error") return;
    const text = message.text();
    if (/pixi|webgl|gpu stall|loadParser|deprecated/i.test(text)) warnings.add(text);
    else consoleErrors.push(text);
  });
  mobilePage.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));

  // The small-width pass walks every sheet-capable family, not just four cores.
  // Go comes first: Panes may launch an external utility and is intentionally
  // a no-surface dock command, so it cannot be allowed to hide the menu walk.
  for (const name of goEntries) {
    const surface = `Mobile Go ${name}`;
    await reset(mobilePage, mobile, false); await openGo(mobilePage);
    await mobilePage.getByRole("menuitem", { name: new RegExp(`^${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`) }).click();
    await sleep(400);
    await record(surface, await exerciseWindow(mobilePage, surface, { resize: false, maximize: false }));
  }
  for (const dock of dockSurfaces) {
    const surface = `Mobile ${dock}`;
    await reset(mobilePage, mobile, false); await openDock(mobilePage, dock);
    await record(surface, await exerciseWindow(mobilePage, surface, { resize: false, maximize: false }));
  }
  await reset(mobilePage, mobile, false);
  try {
    await openZone(mobilePage);
    await record("Mobile Object zone", await exerciseWindow(mobilePage, "Mobile Object zone", { resize: false, maximize: false }));
  } catch (error) {
    fail("Mobile Object zone", error.message);
    await record("Mobile Object zone", ["unreachable"]);
  }
  await reset(mobilePage, mobile, false);
  await mobilePage.getByRole("button", { name: "Desk", exact: true }).click();
  const mobileNewNote = mobilePage.getByRole("menuitem", { name: /New note/i });
  if (await mobileNewNote.count()) {
    await createNoteAndAwaitEditor(mobilePage, mobileNewNote);
    await record("Mobile New Note editor", await exerciseWindow(mobilePage, "Mobile New Note editor", { resize: false, maximize: false }));
  } else {
    fail("Mobile New Note editor", "NEW menu did not offer New note");
    await record("Mobile New Note editor", ["unreachable"]);
  }
  console.log("MOBILE EXCLUSIONS: Trust egress (fixed egress card, not a sheet); Info cards (inspection cards, not sheets); Design components (desk-floor document, no native shell).");
  await mobileContext.close();
  await mobileBrowser.close();

  // HS-129-08: create a Note through the real NEW menu, then inspect its in-world editor.
  // Run after the mobile menu census: creation refreshes the desk projection.
  await reset(page);
  await page.getByRole("button", { name: "Desk", exact: true }).click();
  const newNote = page.getByRole("menuitem", { name: /New note/i });
  if (await newNote.count()) {
    await createNoteAndAwaitEditor(page, newNote);
    await record("New Note editor", await exerciseWindow(page, "New Note editor"));
  } else fail("New Note editor", "NEW menu did not offer New note");
} catch (error) {
  fail("HARNESS", error.stack || String(error));
} finally {
  await browser.close();
}

for (const error of consoleErrors) fail("Console", error);
console.log("\n=== HS-129-11 WALK REPORT ===");
console.log("| Surface | Anatomy | States walked | Assertions | Verdict |");
console.log("|---|---|---|---|---|");
for (const result of results) {
  const { head, body, foot, sheet, reason } = result.anatomy;
  console.log(`| ${result.surface} | head:${head}, body:${body}, foot:${foot}; sheet:${sheet}${reason ? ` (${reason})` : ""} | ${result.states} | anatomy/footer/head/overflow/working-band | ${result.verdict} |`);
}
console.log(`PIXl/WEBGL WARNINGS (non-failing): ${warnings.size}`);
for (const warning of warnings) console.log(`WARN ${warning}`);
console.log(`SUMMARY: ${results.length} surfaces; ${violations.length} violations; ${consoleErrors.length} console errors.`);
if (violations.length) process.exitCode = 1;
