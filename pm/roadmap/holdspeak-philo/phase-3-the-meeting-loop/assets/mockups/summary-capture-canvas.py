from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for path in sorted(root.glob('summary-*.dc.html')):
        phone = path.name.endswith('-phone.dc.html')
        width, height = (393, 852) if phone else (1440, 900)
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
        page.goto(path.as_uri(), wait_until='load')
        page.screenshot(path=str(root / (path.stem + '.png')), full_page=False)
        page.close()
    browser.close()
print('captured', len(list(root.glob('summary-*.dc.png'))), 'shots')
