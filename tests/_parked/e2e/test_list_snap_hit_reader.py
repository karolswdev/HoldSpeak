# Parked: #2332 replaces this CSS snap policy with the shared wholeRows row-anchor fitter.


def test_hit_probe_reaches_snapped_rows_and_still_rejects_hidden_clips():
    """Every row keeps its hit area after reveal; clipping is never waived."""
    from playwright.sync_api import sync_playwright
    from tests.e2e.test_desk_sweep import TARGET_JS

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 393, "height": 852}, reduced_motion="reduce")
        page.set_content('''<style>
          #face{padding:20px;font:14px sans-serif}
          .well{width:300px;height:240px;overflow:auto;scroll-snap-type:y proximity;scroll-padding-top:24px}
          .head{position:sticky;top:0;height:24px;background:white}
          button{display:block;width:280px;height:85px;scroll-snap-align:start}
          .tail{height:80px}
          </style><div id="face"><div class="well"><div class="head">Working</div>'''
                         + ''.join(f'<button>Program step {i}, Done</button>' for i in range(5))
                         + '<div class="tail"></div></div></div>')
        well = page.locator('.well')
        well.evaluate('el=>{el.scrollTop=85}')
        assert page.evaluate(TARGET_JS, '#face') == []
        assert well.evaluate('el=>el.scrollTop') == 85, "The probe restores the owner's scroll"
        well.evaluate("el=>{el.style.overflow='hidden';el.scrollTop=0}")
        assert page.evaluate(TARGET_JS, '#face'), "A hidden clip still loses hit points"
        browser.close()
