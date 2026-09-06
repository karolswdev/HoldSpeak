// Invoked by check-environments-floor.mjs --settle, with isolated HTTP fixtures.
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { resolve } from "node:path";

export async function checkSettleFlow(page, output, origin) {
  const still = (ms = 300) => new Promise((done) => setTimeout(done, ms));
  const shot = async (name) => {
    await still();
    await page.screenshot({ path: resolve(output, `${name}.png`) });
  };
  const settled = async () => {
    await page.click("[data-settle-toggle]");
    await page.waitForSelector('[data-settled="true"]');
    assert.equal(
      await page.$eval(
        ".desk-verbbar",
        (node) => getComputedStyle(node).display,
      ),
      "none",
    );
    assert(
      await page.$eval(".desk-settle-capture", (node) =>
        node.textContent.includes("Recording elsewhere"),
      ),
    );
    assert(
      await page.$eval(
        ".desk-orb",
        (node) =>
          node.getBoundingClientRect().width > 0 &&
          node.getAttribute("aria-label") === "Stop recording",
      ),
    );
  };
  const openPlaces = async () => {
    await page.click('.desk-room-actions [aria-label="Change places"]');
    await page.waitForSelector('#surface-places [role="radio"]');
    await still();
    for (const selector of [".desk-orb", "[data-settle-toggle]"]) {
      assert(
        await page.$eval(selector, (node) => {
          const box = node.getBoundingClientRect();
          const hit = document.elementFromPoint(
            box.x + box.width / 2,
            box.y + box.height / 2,
          );
          return hit === node || node.contains(hit);
        }),
        `${selector} was covered by the places window`,
      );
    }
  };
  const shortcut = async (letter) => {
    await page.keyboard.down("Control");
    await page.keyboard.down("Shift");
    await page.keyboard.press(letter);
    await page.keyboard.up("Shift");
    await page.keyboard.up("Control");
  };
  await page.waitForSelector(".desk-orb.is-recording");
  await page.evaluate(() => {
    window.__originalOrb = document.querySelector(".desk-orb");
  });
  await settled();
  await shot("settle-desktop");
  await openPlaces();
  await page.click('[aria-label="Favorite Night Train"]');
  assert.equal(
    await page.evaluate(() => localStorage.getItem("hs.desk.atmosphere")),
    "radio-station",
    "Favoriting changed the room",
  );
  await page.click('[data-atmosphere-choice="night-train"]');
  await page.waitForSelector(
    '[data-atmosphere="night-train"] canvas[data-ready="true"]',
  );
  await page.waitForFunction(
    () =>
      document.querySelector('[data-atmosphere-choice="night-train"] img')
        ?.naturalWidth > 0,
  );
  await shot("places-desktop");
  // The same window instance and record control survive settling and Escape.
  await page.evaluate(() => {
    window.__originalPlaces = document.querySelector("#surface-places");
  });
  await shortcut("P");
  assert.equal(
    await page.$$eval("#surface-places", (nodes) => nodes.length),
    1,
  );
  await page.keyboard.press("Escape");
  await page.waitForFunction(
    () => !document.querySelector('[data-settled="true"]'),
  );
  assert(
    await page.evaluate(
      () =>
        document.querySelector("#surface-places") === window.__originalPlaces,
    ),
  );
  assert(
    await page.evaluate(
      () => document.querySelector(".desk-orb") === window.__originalOrb,
    ),
  );
  await page.keyboard.press("Escape");
  await page.waitForSelector("#surface-places", { hidden: true });
  await page.click('[data-menu-id="go"] > button');
  await page.waitForSelector(".desk-verbbar-menu");
  await shortcut("F");
  await page.waitForSelector('[data-settled="true"]');
  await page.waitForSelector(".desk-verbbar-menu", { hidden: true });
  await page.keyboard.press("Escape");
  assert.equal(
    await page.evaluate(() => window.__micRequests),
    0,
    "The desktop flow requested a microphone",
  );
  // Reload proves favorites persist but quiet mode intentionally does not.
  await page.setViewport({ width: 393, height: 852, deviceScaleFactor: 1 });
  await page.goto(`${origin}/_built/`, { waitUntil: "networkidle0" });
  assert(!(await page.$('[data-settled="true"]')));
  assert.deepEqual(
    JSON.parse(
      await page.evaluate(() =>
        localStorage.getItem("hs.desk.atmosphere.favorites"),
      ),
    ),
    ["night-train"],
  );
  await page.click('button[aria-label="Floor"]');
  await page.waitForSelector(
    '[data-atmosphere="night-train"] canvas[data-ready="true"]',
  );
  await settled();
  await shot("settle-phone");
  await openPlaces();
  await page.click("#surface-places ::-p-text(Favorites)");
  assert.equal(
    await page.$$eval(
      '#surface-places [role="radio"]',
      (nodes) => nodes.length,
    ),
    1,
  );
  await page.waitForFunction(
    () =>
      document.querySelector('#surface-places [role="radio"] img')
        ?.naturalWidth > 0,
  );
  await shot("places-phone");
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    "Phone horizontal overflow",
  );
  await page.keyboard.press("Escape");
  assert(!(await page.$('[data-settled="true"]')));
  assert(
    await page.$("#surface-places"),
    "Restoring the Desk closed the work window",
  );
  const report = {
    bundle: "production",
    backend: "isolated HTTP fixtures",
    preservedWindow: true,
    preservedCaptureControl: true,
    captureReachableOverPhoneSheet: true,
    favoritesPersist: true,
    nativeShortcuts: true,
    escapeRestores: true,
    phoneOverflow: false,
  };
  await writeFile(
    resolve(output, "settle-checks.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  console.log(JSON.stringify(report, null, 2));
}
