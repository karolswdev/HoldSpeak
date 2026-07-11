"""Protocol-v2 execution identity: implementation target x form factor.

Device shape is not implementation identity.  In particular, a React page at
an iPad-sized viewport is not the Swift flagship app.  Every executable UAT
slot is therefore a canonical tuple and verdicts persist its full identity.
"""

from __future__ import annotations

from dataclasses import dataclass


PROTOCOL_SCHEMA_VERSION = 2

TARGETS: dict[str, dict] = {
    "cli_python": {
        "label": "HoldSpeak Python CLI",
        "native": False,
        "form_factors": ("local_shell",),
    },
    "web_react": {
        "label": "React Web Desk",
        "native": False,
        "form_factors": ("desktop", "ipad_browser", "iphone_browser", "tablet_viewport"),
    },
    "ios_flagship_swift": {
        "label": "Flagship Swift app",
        "native": True,
        "form_factors": ("ipad", "iphone"),
    },
    "ios_companion_swift": {
        "label": "Companion Swift app",
        "native": True,
        "form_factors": ("ipad", "iphone"),
    },
    "ios_classic_swift": {
        "label": "Classic/demo Swift app",
        "native": True,
        "form_factors": ("ipad", "iphone"),
    },
    # Quarantine target: useful for preserving diagnostic protocols whose
    # shipped root is unresolved, but forbidden in owner campaigns and never
    # accepted as release evidence.
    "ios_unclassified_swift": {
        "label": "Unclassified Swift build (diagnostic only)",
        "native": True,
        "form_factors": ("ipad", "iphone"),
        "quarantined": True,
    },
    "legacy_unqualified": {
        "label": "Legacy unqualified evidence (invalid)",
        "native": False,
        "form_factors": ("web", "ipad", "iphone"),
        "quarantined": True,
    },
}

FORM_FACTOR_LABELS = {
    "desktop": "desktop browser",
    "local_shell": "local terminal",
    "ipad_browser": "physical iPad browser (web, not native)",
    "iphone_browser": "physical iPhone browser (web, not native)",
    "tablet_viewport": "desktop tablet viewport (web simulation, not native)",
    "ipad": "iPad",
    "iphone": "iPhone",
    "web": "legacy web label",
}


def slot_id(target: str, form_factor: str) -> str:
    return f"{target}:{form_factor}"


@dataclass(frozen=True)
class ExecutionSlot:
    target: str
    form_factor: str

    @property
    def id(self) -> str:
        return slot_id(self.target, self.form_factor)

    @property
    def native(self) -> bool:
        return bool(TARGETS.get(self.target, {}).get("native"))

    @property
    def quarantined(self) -> bool:
        return bool(TARGETS.get(self.target, {}).get("quarantined"))

    @property
    def label(self) -> str:
        target = TARGETS.get(self.target, {}).get("label", self.target)
        form = FORM_FACTOR_LABELS.get(self.form_factor, self.form_factor)
        return f"{target} · {form}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "target": self.target,
            "form_factor": self.form_factor,
            "label": self.label,
            "native": self.native,
            "quarantined": self.quarantined,
        }


def validate_target_form(target: str, form_factor: str) -> str | None:
    spec = TARGETS.get(target)
    if spec is None:
        return f"unknown execution_target {target!r}"
    if form_factor not in spec["form_factors"]:
        allowed = ", ".join(spec["form_factors"])
        return (
            f"form factor {form_factor!r} is invalid for {target!r}; "
            f"allowed: {allowed}"
        )
    return None


def legacy_surface_for(slot: ExecutionSlot) -> str:
    """Temporary ledger bridge; never used as verdict identity."""
    if slot.target == "web_react":
        return "web"
    return slot.form_factor if slot.form_factor in {"ipad", "iphone"} else "web"
