"""Build the two light review pages (index.html in each canvas folder).

Shots are referenced by relative path (no base64). Colours are the product's
token values (web/src/styles/tokens.css: the field, surface, text, accent).
"""
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
ITEMS = HERE.parent
DELIVERY = ITEMS.parent / "story-03-delivery-canvas"

PAGES = {
    ITEMS: ("Room items canvas", "PHILO-9-03 · the ITEMS section", [
        ("0-today", "0 · Today", "No items section; ON TRACK; the milestone 7 days late is not shown."),
        ("1a-late-first-view", "1a · Late, first view", "AT RISK + 1 MILESTONE LATE; NEEDS YOU row; ITEMS 3 after NEEDS YOU."),
        ("1b-late-items", "1b · Late, the section", "Late first; the open risk; planned; MISSED (failure ✗); DROPPED (idle —). No Add, no row verb."),
        ("1c-sources-in-view", "1c · SOURCES in view", "At 393 the Ask well is in the flow: it covers no verb and no head (F10)."),
        ("2a-reached-first-view", "2a · Reached, first view", "A real transition to reached: ON TRACK again."),
        ("2b-reached-items", "2b · Reached, the section", "The reached milestone last, with REACHED."),
        ("3-empty-omitted", "3 · Empty", "Zero items: the section is omitted; no counter of zero."),
        ("4-items-unavailable", "4 · Items read failed", "ITEMS UNAVAILABLE with Retry: never drawn as empty."),
    ]),
    DELIVERY: ("Copy and confirm canvas", "PHILO-9-03 · copy and confirm delivery", [
        ("0a-today-list", "0a · Today, the list", "DRAFTS 1; the fixed E; the words run together (F11)."),
        ("0b-today-published", "0b · Today, published", "Regenerate and Copy; nothing records a delivery."),
        ("1-after-copy", "1 · After Copy", "Copied (2 s); DELIVERY: the To field and Mark delivered."),
        ("2-returned", "2 · He left and returned", "A reload, the Room reopened: Mark delivered still offered."),
        ("3-to-typed", "3 · To typed", "Priya in the field."),
        ("4-pending", "4 · Pending", "The press held: the loading face, the field disabled."),
        ("5-delivered-once", "5 · Delivered once", "One row after a double-click: one call, one row."),
        ("6-mistake-kept", "6 · The mistake kept", "Priya was wrong; Tomas added; both rows stay; DELIVERED 2."),
        ("6b-refused", "6b · Refused", "A named refusal: REFUSED · NOT PUBLISHED (data-code update_not_published). The field unlocks."),
        ("6c-result-unknown", "6c · Result unknown", "The answer was lost: NO ANSWER · RESULT UNKNOWN; the field locked to Lena; the verb is Retry."),
        ("6d-retried-one-row", "6d · Retried", "Retry sent the same key and To: one Lena row (the hub replayed it)."),
        ("7a-list-chip-count", "7a · List chip, ×N (after Back)", "Back returned to the list at both widths; DELIVERED ×3 counts every mark."),
        ("7b-list-chip-latest", "7b · List chip, latest", "DELIVERED <time> · LENA."),
        ("8-draft-no-mark", "8 · A draft", "No DELIVERY, no Mark delivered."),
    ]),
}

CSS = """
:root { --field: #0e0f13; --surface: #15171d; --border: #2a2e37; --text: #f2f3f5; --muted: #9aa0a6; --accent: #a86e4a; }
body { margin: 0; background: var(--field); color: var(--text); font: 14px/1.5 "Inter", system-ui, sans-serif; }
main { max-width: 1480px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font: 600 20px/1.3 "JetBrains Mono", ui-monospace, monospace; margin: 0 0 4px; }
.lede { color: var(--muted); margin: 0 0 24px; }
section { border-top: 1px solid var(--border); padding: 20px 0; }
h2 { font: 600 14px/1.4 "JetBrains Mono", ui-monospace, monospace; letter-spacing: .06em; text-transform: uppercase; margin: 0 0 4px; color: var(--accent); }
.note { color: var(--muted); margin: 0 0 12px; }
.pair { display: grid; grid-template-columns: minmax(0, 1440fr) minmax(0, 393fr); gap: 16px; align-items: start; }
figure { margin: 0; background: var(--surface); border: 1px solid var(--border); padding: 6px; }
figure img { display: block; width: 100%; height: auto; }
figcaption { color: var(--muted); font: 12px ui-monospace, monospace; padding-top: 4px; }
@media (max-width: 720px) { .pair { grid-template-columns: 1fr; } }
"""

for folder, (title, head, boards) in PAGES.items():
    parts = []
    for key, name, note in boards:
        parts.append(
            f'<section><h2>{html.escape(name)}</h2><p class="note">{html.escape(note)}</p><div class="pair">'
            f'<figure><img src="shots/{key}-1440.png" alt="{html.escape(name)} at 1440" loading="lazy"><figcaption>1440 × 900</figcaption></figure>'
            f'<figure><img src="shots/{key}-393.png" alt="{html.escape(name)} at 393" loading="lazy"><figcaption>393 × 852</figcaption></figure>'
            "</div></section>"
        )
    page = (
        f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>"
        f"<h1>{html.escape(head)}</h1><p class=\"lede\">DRAFT for the owner's ratification. The questions and the measurements: README.md.</p>"
        + "".join(parts) + "</main></body></html>\n"
    )
    (folder / "index.html").write_text(page)
    print("wrote", folder / "index.html")
