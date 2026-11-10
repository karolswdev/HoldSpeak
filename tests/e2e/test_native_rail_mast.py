"""A native rail must leave the object's name readable beside its verbs."""
from tests.e2e import test_desk_sweep as sweep
from tests.e2e.test_desk_sweep import desk, pw_browser  # noqa: F401


def test_decision_mast_keeps_words_whole_beside_a_rail(desk, pw_browser):
    base = desk["base"]
    wid = "surface-decisions"
    sweep.clear_hub_windows_http(base, sweep.TOKEN)
    sweep._hub_open(base, wid, None)
    ctx, page, errors, requests = sweep._page(pw_browser, 1440, base)
    try:
        page.goto(f"{base}/?token={sweep.TOKEN}", wait_until="load")
        sweep._normal_chair(page)
        sweep._Case(page, base, wid, errors, requests).settle()
        title = page.locator(f'[id="{wid}"] [data-testid="decision-reader-title"]')
        title.wait_for(state="visible")
        broken = title.evaluate(r"""el => {
          const node = el.firstChild;
          const text = node.textContent;
          return [...text.matchAll(/\S+/g)].flatMap(match => {
            const range = document.createRange();
            range.setStart(node, match.index);
            range.setEnd(node, match.index + match[0].length);
            const lines = new Set([...range.getClientRects()].map(rect => Math.round(rect.top)));
            return lines.size > 1 ? [match[0]] : [];
          });
        }""")
        assert not broken, f"The mast breaks words to fit its verbs: {broken}"
    finally:
        ctx.close()
