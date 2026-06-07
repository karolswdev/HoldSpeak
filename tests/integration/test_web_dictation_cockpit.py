"""HS-44-02: the dictation cockpit premium pass (behavior-preserving)."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web" / "src" / "pages" / "dictation.astro").read_text()


def _app_js() -> str:
    return (_REPO / "web" / "src" / "scripts" / "dictation-app.js").read_text()


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
