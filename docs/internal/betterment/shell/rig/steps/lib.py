def boxes(page):
    return page.evaluate("""() => [...document.querySelectorAll('header.desk-pullout-head')].map(h => {const w=h.parentElement; const r=w.getBoundingClientRect(); return [w.getAttribute('aria-label'), Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]})""")
def close_all(page, wait):
    for i in range(14):
        b = page.locator('header.desk-pullout-head button[aria-label^="Close "], header.desk-pullout-head button[aria-label^="Back from "]')
        if b.count() == 0: break
        try: b.first.click(timeout=3000, force=True)
        except Exception as e: print("close fail", e); break
        wait(0.6)
