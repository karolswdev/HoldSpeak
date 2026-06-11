"""HS-44-02: the dictation cockpit premium pass (behavior-preserving)."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web" / "src" / "pages" / "dictation.astro").read_text()


def _app_js() -> str:
    """The dictation page behavior source: the entry module plus the carved
    behavior modules under scripts/dictation/ (the page bundles them into
    one chunk). Assertions target this combined source."""
    scripts = _REPO / "web" / "src" / "scripts"
    parts = [(scripts / "dictation-app.js").read_text()]
    for module in sorted((scripts / "dictation").glob("*.js")):
        parts.append(module.read_text())
    return "\n".join(parts)


def test_dictation_has_cockpit_hero() -> None:
    """A wizard-bar hero (eyebrow + display title + lede) heads the surface."""
    page = _page()
    assert "cockpit-hero" in page
    assert "cockpit-eyebrow" in page
    assert "cockpit-h" in page
    assert "cockpit-lede" in page
    assert "Dictation cockpit" in page


def test_dictation_cockpit_is_elevated_to_the_wizard_bar() -> None:
    """Ambient glow + a premium contained nav + reduced-motion-safe motion."""
    page = _page()
    # the same ambient accent glow as the dashboard home + the wizard.
    assert ".dictation::before" in page
    assert "radial-gradient" in page
    # the section nav is a premium contained pill bar.
    assert "cockpit-tabs" in page
    # depth + motion that respects reduced-motion.
    assert "prefers-reduced-motion" in page


def test_dictation_cockpit_preserves_behavior_hooks() -> None:
    """The Alpine-free app's DOM contract is untouched — ids + section tabs."""
    page = _page()
    # the section tablist the JS binds via `[data-section]` is intact.
    assert 'role="tablist" aria-label="Dictation sections"' in page
    for section in ("readiness", "blocks", "kb", "hs", "hooks", "runtime", "memory", "dry-run"):
        assert f'data-section="{section}"' in page
    # the block-scope row + key control ids the JS reads by id.
    assert 'data-scope="global"' in page
    assert 'id="project-root-apply"' in page
    assert 'id="dry-btn-run"' in page


def test_dictation_surfaces_carry_the_knowledge_explainer() -> None:
    """HS-47-02: each surface has a what/why/worked-example explainer that names
    the HS-47-01 model (project knowledge = Facts + Context)."""
    page = _page()
    # both explainer cards exist, under the one umbrella.
    assert page.count("kn-explainer") >= 2
    assert "Project knowledge · Facts" in page
    assert "Project knowledge · Context" in page
    # the what-line for each, accurate per the Phase-46 facts.
    assert "Exact values, stamped in word for word." in page
    assert "Background the rewrite model reads." in page
    # a worked example demonstrating the verbatim substitution (literal braces).
    assert "kn-example" in page
    assert "{project.kb.stack}" in page
    # each names its companion so the two read as one capability.
    assert "<strong>Project Context</strong>" in page
    assert "<strong>Project Facts</strong>" in page


def test_dictation_surfaces_have_teaching_empty_states() -> None:
    """HS-47-02: a detected-but-empty project meets a teaching empty state with a
    one-click starter, not a bare grid/textarea. Markup is static (toggled by JS)
    so its scoped CSS applies."""
    page = _page()
    assert 'id="kb-empty"' in page
    assert 'id="hs-empty"' in page
    assert "No facts yet" in page
    assert "No project context yet" in page
    # one-click starter actions on each surface.
    assert 'id="kb-empty-starter"' in page
    assert 'id="hs-empty-example"' in page
    assert "Use starter facts" in page
    assert "Start with an example" in page
    # the scoped CSS for the toggled DOM is present in this page (the trap guard).
    assert ".kn-empty" in page


def test_dictation_context_has_guided_setup_and_agent_prompt() -> None:
    """HS-47-03: the Context surface offers a guided setup with both a template
    starter and a copiable, repo-aware coding-agent prompt."""
    page = _page()
    assert 'id="hs-setup"' in page
    assert "Set up project knowledge" in page
    assert 'id="hs-empty-setup"' in page  # launches the flow from the empty state
    # the template-starter path.
    assert 'id="hs-setup-starter"' in page
    assert "Use a starter set" in page
    # the coding-agent prompt path.
    assert 'id="hs-setup-copy-prompt"' in page
    assert 'id="hs-agent-prompt"' in page
    assert "Draft with your coding agent" in page
    # the guided panel's scoped CSS ships with the page (the trap guard).
    assert ".kn-setup" in page
    assert ".kn-agent-prompt" in page


def test_dictation_has_focus_safe_discovery_nudge() -> None:
    """HS-47-04: an ambient, dismissible, focus-safe discovery nudge with a
    per-project + global off switch, routing into the guided flow."""
    page = _page()
    js = _app_js()
    # ambient bar above the tabs, a note (not a modal), with its scoped CSS.
    assert 'id="kn-nudge"' in page
    assert 'role="note"' in page
    assert ".kn-nudge" in page
    assert 'id="kn-nudge-setup"' in page    # routes into the guided flow
    assert 'id="kn-nudge-dismiss"' in page  # per-project dismiss
    assert 'id="kn-nudge-off"' in page      # global off switch
    # show/suppress logic + durable dismissal live in the bundle.
    assert "maybeShowKnNudge" in js
    assert "project_context" in js          # suppress when context exists
    assert "knNudgeDismiss" in js           # durable per-project dismissal
    assert "holdspeak.knNudgeDisabled" in js  # global off key
    # focus-safe: the dictation bundle still calls no .focus().
    astro = (
        Path(__file__).resolve().parents[2]
        / "holdspeak" / "static" / "_built" / "_astro"
    )
    dict_js = list(astro.glob("dictation.astro_astro_type_script*.js"))
    if dict_js:
        bundle = "\n".join(p.read_text() for p in dict_js)
        assert ".focus()" not in bundle


def test_agent_prompt_is_repo_aware_and_lists_the_hs_files() -> None:
    """HS-47-03: the copiable prompt names this repo and the .hs/ files to write,
    and the starter set + prompt builder live in the client bundle."""
    js = _app_js()
    assert "function buildAgentPrompt" in js
    assert "STARTER_HS_FILES" in js
    # repo-aware: the prompt interpolates the detected project name/root.
    assert "project.name" in js and "project.root" in js
    # it tells the agent which .hs/ files to author.
    for name in ("instructions.md", "context.md", "terms.md", "workflows.md", "targets.md"):
        assert name in js


def test_dictation_has_focus_safe_activity_nudges() -> None:
    """HS-53-04: the activity pre-briefing nudges — a focus-safe region with a
    JS-injected list, a citation-rich card pattern, and a selection pin.

    The shell is static markup; the list items are runtime-rendered, so their
    CSS lives in `<style is:global>` (Astro scoped CSS dies on JS-injected DOM)
    and a `role="region"` / `role="note"` keeps focus put.
    """
    page = _page()
    js = _app_js()
    # Static hero shell — region wrapper + the list mount + the selection pin.
    assert 'id="activity-nudges"' in page
    assert 'role="region"' in page
    assert 'id="activity-nudges-list"' in page
    assert 'id="activity-nudges-pin"' in page
    assert 'id="activity-nudges-pin-clear"' in page
    # Signal hero: eyebrow + display title + trust strip + activity-nudge card.
    assert "an-eyebrow" in page
    assert "an-title" in page
    assert "an-trust" in page
    assert ".activity-nudge {" in page
    # Chip-style citations and a real primary CTA (no flat ghost buttons).
    assert ".an-chip-entity" in page
    assert ".an-btn-primary" in page
    # JS: the loader, the chip + glyph builders, the pin store, and the API verbs.
    assert "maybeShowActivityNudges" in js
    assert "/api/activity/nudges" in js
    assert "/dismiss" in js
    assert "anSavePin" in js
    assert "anRenderCards" in js
    assert "anChip" in js
    assert "AN_SVG" in js
    # The card is a focus-safe note, not a modal.
    assert 'card.setAttribute("role", "note")' in js
    # The dictation bundle still calls no .focus().
    astro = (
        Path(__file__).resolve().parents[2]
        / "holdspeak" / "static" / "_built" / "_astro"
    )
    dict_js = list(astro.glob("dictation.astro_astro_type_script*.js"))
    if dict_js:
        bundle = "\n".join(p.read_text() for p in dict_js)
        assert ".focus()" not in bundle
