"""The shared material grammar, read from computed styles.

Owner 2026-10-22: Workbench meets Pop!_OS; flat controls and continuous
paper supersede mandatory heavy bevels. Token presence, state naming and
the existing contrast/hit/geometry guards remain binding.

The material reader of PHILO-14 B2, kept as a rig: the desk sweep's
`material` fence (tests/e2e/test_desk_sweep.py) reads every window with it,
and tests/e2e/test_settings_glass.py reads a pressed Button with it. The B2
browser file is parked (tests/e2e/_parked/test_philo14_b2_material_glass.py).
"""
from __future__ import annotations

from typing import Any

LAMP_WORDS = {"success": "OK", "working": "WORKING", "warning": "WARN", "failure": "FAILED", "active": "ASKS"}

# The material of one face, read from the computed styles.
MATERIAL_JS = r"""(root) => {
  const scope = root ? document.querySelector(root) : document;
  if (!scope) return null;
  // Each token resolved on a fresh probe (an unknown token would read "none").
  const resolve = (value) => {
    const probe = document.createElement('div');
    probe.style.boxShadow = value;
    document.body.appendChild(probe);
    const v = getComputedStyle(probe).boxShadow;
    probe.remove();
    return v;
  };
  const raised = resolve('var(--bevel-raised)');
  const sunken = resolve('var(--bevel-sunken)');
  const soft = resolve('var(--bevel-raised-soft)');
  const softSunken = resolve('var(--bevel-sunken-soft)');
  // On the Steel plate (the title bar: Raw) the grammar rides --wb-raised.
  const wbRaised = resolve('var(--wb-raised)');
  const wbSunken = resolve('var(--wb-sunken)');
  const seen = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const TOKEN = '.surface-filter-token, .surface-project-button';
  const btns = [...scope.querySelectorAll('.btn:not(:disabled):not([aria-pressed="true"])')]
    .filter(seen).filter((b) => !b.matches(TOKEN));
  const tokens = [...scope.querySelectorAll('.surface-filter-token.btn:not(:disabled), .surface-project-button.btn:not(:disabled)')].filter(seen);
  const chips = [...scope.querySelectorAll('.surface-state-chip')].filter(seen);
  const facts = [...scope.querySelectorAll('.surface-token[data-chip]')].filter(seen);
  const BODY = '.desk-pullout-body, .desk-surface-body, .chair-window-body';
  const bodies = [...scope.querySelectorAll(BODY)].filter(seen)
    .filter((b) => !b.parentElement || !b.parentElement.closest(BODY));
  return {
    raised, sunken, soft, softSunken, wbRaised, wbSunken,
    tokenPresence: ['--bevel-raised','--bevel-sunken','--bevel-raised-soft',
      '--bevel-sunken-soft','--wb-raised','--wb-sunken'].every(name =>
        getComputedStyle(document.documentElement).getPropertyValue(name).trim()),
    tokens: tokens.map((t) => ({ name: (t.textContent || '').trim().slice(0, 40),
      active: t.hasAttribute('data-filter-active'), shadow: getComputedStyle(t).boxShadow })),
    buttons: btns.map((b) => ({ name: (b.textContent || '').trim().slice(0, 40), shadow: getComputedStyle(b).boxShadow })),
    chips: chips.map((c) => {
      const lamp = c.querySelector('.surface-state-chip-icon');
      const s = getComputedStyle(c);
      const l = lamp ? getComputedStyle(lamp) : null;
      const glyph = lamp ? lamp.textContent : '';
      return { name: c.getAttribute('aria-label'), state: c.dataset.state,
               word: (c.textContent || '').slice(glyph.length).trim(),
               border: s.borderTopWidth, bg: s.backgroundColor,
               lampW: l ? l.width : null, lampShadow: l ? l.boxShadow : null,
               lampRadius: l ? l.borderTopLeftRadius : null };
    }),
    facts: facts.map((f) => { const s = getComputedStyle(f); const b = getComputedStyle(f, '::before');
      return { text: (f.textContent || '').slice(0, 30), tone: f.dataset.tone || null,
               border: s.borderTopColor, shadow: s.boxShadow, bg: s.backgroundColor,
               lampW: b.content === 'none' ? null : b.width, lampShadow: b.boxShadow }; }),
    bodies: bodies.map((b) => getComputedStyle(b).boxShadow),
  };
}"""


def _assert_material(page: Any, face: str, root: str | None = None) -> dict[str, Any]:
    m = page.evaluate(MATERIAL_JS, root)
    assert m is not None, face
    raised, sunken = m["raised"], m["sunken"]
    # Explicit none is a valid modern material; an absent token is not.
    assert m["tokenPresence"], m
    for b in m["buttons"]:
        assert b["shadow"] == "none" or b["shadow"].startswith((raised, m["wbRaised"])), (face, b, raised)
    for t in m["tokens"]:
        assert t["shadow"] == "none" or t["shadow"].startswith(m["softSunken"] if t["active"] else m["soft"]), (face, t)
    for c in m["chips"]:
        # PHILO-17 ALIVE (owner 2026-10-11, "way too static … monotone"):
        # a state is a soft tinted PILL with a round lamp dot; no border.
        assert c["border"] == "0px", (face, c)
        assert c["lampW"] == "8px" and c["lampRadius"] == "50%", (face, c)
        # Never colour alone: every lamp is named; a shown word IS its name;
        # a lit lamp with no word of its own is named by its state word.
        assert (c["name"] or "").strip(), (face, c)
        if c["word"]:
            assert c["name"] == c["word"], (face, c)
        elif c["state"] in LAMP_WORDS:
            assert c["name"] == LAMP_WORDS[c["state"]], (face, c)
    for f in m["facts"]:
        # The 1 px border stays, transparent, so no row moves.
        assert f["border"] == "rgba(0, 0, 0, 0)" and f["shadow"] == "none", (face, f)
        # PHILO-17 ALIVE: a fact is a tinted pill; a toned one leads with
        # a round lamp dot.
        if f["tone"] in ("warn", "danger", "ok"):
            assert f["lampW"] == "8px", (face, f)
    for shadow in m["bodies"]:
        assert shadow == "none" or shadow.startswith(sunken), (face, shadow, sunken)
    return m
