"""A minimal, valid example user plugin pack (HS-35-02 fixture).

Demonstrates the user-pack contract documented in
`docs/PLUGIN_AUTHORING.md`: export a `MANIFEST` (a `PluginManifest`) and a
zero-arg `create_plugin()` factory returning a `HostPlugin` instance whose
`.id` matches the manifest.

This pack is deliberately LLM-free (no `required_capabilities`) so the
loader/registration tests can exercise the full load → register → dispatch
path without an LLM endpoint.
"""

from __future__ import annotations

from typing import Any

from holdspeak.plugin_sdk import validate_manifest

MANIFEST = validate_manifest(
    {
        "id": "example_user_plugin",
        "label": "Example User Plugin",
        "version": "0.1.0",
        "kind": "synthesizer",
        "description": "Counts transcript words; a wiring demonstration.",
        "execution_mode": "inline",
        "intents": ["incident"],
        "profiles": ["balanced"],
    }
)


class ExampleUserPlugin:
    """Trivial deterministic plugin — summarizes transcript length."""

    id: str = "example_user_plugin"
    version: str = "0.1.0"
    kind: str = "synthesizer"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        transcript = str(context.get("transcript") or "").strip()
        word_count = len(transcript.split()) if transcript else 0
        return {
            "summary": f"example_user_plugin saw {word_count} word(s).",
            "word_count": word_count,
            "confidence_hint": 1.0 if word_count else 0.0,
        }


def create_plugin() -> ExampleUserPlugin:
    return ExampleUserPlugin()
