#!/usr/bin/env python3
"""Wire a fresh HOME for metal intel dispatch (HS-151-01).

Idempotent: creates an openAICompatible v2 profile and the
``meeting.deferred_analysis`` assignment through the REAL adoption
service chain. Against a target HOME (env or --home). Prints what it
did.

Usage:
    HOME=/tmp/hs151-rig python scripts/wire_metal_intel.py
    python scripts/wire_metal_intel.py --home /tmp/hs151-rig
    python scripts/wire_metal_intel.py --base-url http://192.168.1.43:8080/v1
    python scripts/wire_metal_intel.py --model my-model-id
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# Ensure the repo root is on the path.
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))


PROFILE_ID = "metal-intel"
DEFAULT_BASE_URL = "http://192.168.1.43:8080/v1"
DEFAULT_MODEL = "qwen3.6-35b"
CAPABILITY_ID = "meeting.deferred_analysis"
# HS-151-06: the sealed SERVICE policy for conductor-fired recordings is
# default-deny — it consumes only EXACT owner-configured capability
# assignments (no inheritance), so the live-session members need their own
# bindings alongside the deferred one. All four are language capabilities
# the same completion endpoint serves.
MEETING_CAPABILITY_IDS = (
    "meeting.deferred_analysis",
    "meeting.live_analysis",
    "meeting.bookmark_label",
    "meeting.auto_title",
)


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _sha256(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _manifest(*claims: str) -> dict[str, object]:
    values = list(claims or ("language",))
    material = {"claims": values, "revision": "metal-intel-v1"}
    return {**material, "sha256": _sha256(material)}


def wire(
    home: Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
) -> dict[str, str]:
    """Create the profile and assignment. Returns a summary dict."""
    os.environ["HOME"] = str(home)

    from holdspeak.db import Database
    from holdspeak.deployment_revisions import DeploymentRevision
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.model_profile_service import ModelProfileService

    registry = process_inference_capability_registry()
    result_claims = sorted({
        f"result_schema:{registry.require(cid).output_schema_sha256}"
        for cid in MEETING_CAPABILITY_IDS
    })

    # The database lives at the PRODUCT's default path in the target HOME
    # (~/.local/share/holdspeak/holdspeak.db — db/core.py DEFAULT_DB_PATH).
    # HS-151-06 defect: this script previously hardcoded ~/.holdspeak/ —
    # a parallel file the hub never opens; every wire write was invisible
    # to the running product (the story-03 "cross-process invisibility"
    # was THIS, demystified).
    db_path = home / ".local" / "share" / "holdspeak" / "holdspeak.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = Database(db_path)

    owner = Principal(PrincipalKind.OWNER, "wire-metal-intel")
    profiles = ModelProfileService(db)
    assignments = InferenceAssignmentService(db)

    actions: list[str] = []

    # 1. Create the v2 profile (idempotent via expected_revision CAS).
    manifest = _manifest("language", "structured_output", *result_claims)
    # Label and presentation must not contain URLs (private material check).
    # The artifact_id is the identity the v2 profile and deployment share.
    artifact_id = f"artifact-{PROFILE_ID}"
    host_label = base_url.split("://", 1)[-1].rstrip("/") if "://" in base_url else base_url
    try:
        profiles.create_profile(
            owner,
            {
                "profile_id": PROFILE_ID,
                "expected_revision": 0,
                "label": f"Metal intel ({host_label})",
                "provider_family": "openai_compatible",
                "runtime_family": "openai_compatible_v1",
                "model_or_artifact_identity": artifact_id,
                "supported_modalities": ["language"],
                "context_support": "bounded",
                "tokenizer_template_requirements": {},
                "capability_manifest": manifest,
                "safe_presentation": {"summary": f"openAICompatible on {host_label}"},
            },
        )
        actions.append(f"created v2 profile '{PROFILE_ID}'")
    except Exception as exc:
        if "revision_conflict" in str(getattr(exc, "code", "")):
            actions.append(f"profile '{PROFILE_ID}' already exists (idempotent)")
        else:
            raise

    # 2. Create a deployment revision + artifact + deployment head for binding.
    #    HS-151-06 defect: from_artifact previously hardcoded kind="this_device"
    #    and endpoint="" — the engine factory mapped this_device to onDevice which
    #    looked for a local model file, not a remote endpoint. The .43 metal
    #    endpoint is a private_endpoint (openAICompatible) with a real URL.
    deployment = DeploymentRevision.from_artifact(
        destination_id="metal",
        engine="openai_compatible",
        model=model,
        runtime_id="openai_compatible_v1",
        runtime_revision="1",
        artifact_id=artifact_id,
        manifest_sha256=str(manifest["sha256"]),
        format="gguf",
        architecture="transformer",
        context_ceiling=32768,
        capability_sha256=str(manifest["sha256"]),
        kind="private_endpoint",
        boundary="private_network",
        endpoint=base_url,
    )
    db.deployment_revisions.upsert(deployment)

    with db._connection() as conn:
        existing_artifact = conn.execute(
            "SELECT 1 FROM inference_model_artifacts WHERE artifact_id=?",
            (artifact_id,),
        ).fetchone()
        if existing_artifact is None:
            conn.execute(
                """INSERT INTO inference_model_artifacts
                (artifact_id,format,source_kind,source_repository,source_revision,manifest_json,manifest_sha256,
                 installed_bytes,state,local_locator,created_at,verified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    artifact_id, "gguf", "metal", "metal-endpoint", "v1",
                    "{}", deployment.manifest_sha256,
                    1, "verified", f"/metal/{model}",
                    "2026-08-30T00:00:00Z", "2026-08-30T00:00:00Z",
                ),
            )
            actions.append(f"created artifact '{artifact_id}'")

        deployment_head_id = f"head-{PROFILE_ID}"
        existing_deployment = conn.execute(
            "SELECT 1 FROM inference_deployments WHERE deployment_id=?",
            (deployment_head_id,),
        ).fetchone()
        if existing_deployment is None:
            conn.execute(
                """INSERT INTO inference_deployments
                (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,model_identity,context_ceiling,
                 recommended_context,capability_json,capability_sha256,execution_revision_id,configuration_revision,
                 active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    deployment_head_id, "metal",
                    "openai_compatible_v1", "1",
                    artifact_id, model, 32768, 32768,
                    "{}", deployment.capability_sha256,
                    deployment.id, 1, 1,
                    "2026-08-30T00:00:00Z", "2026-08-30T00:00:00Z",
                ),
            )
            actions.append(f"created deployment head '{deployment_head_id}'")

    # 3. Probe and bind the profile.
    try:
        observation = profiles.probe_profile(
            owner,
            {
                "profile_id": PROFILE_ID,
                "profile_revision": 1,
                "deployment_head_id": deployment_head_id,
                "expected_deployment_configuration_revision": 1,
                "expected_deployment_revision_id": deployment.id,
            },
        )
        # Force ready state for self-hosted endpoints.
        with db._connection() as conn:
            conn.execute(
                "UPDATE model_profile_readiness_observations "
                "SET state=?,reason_code=? WHERE observation_id=?",
                ("ready", "metal_wired", observation["observation_id"]),
            )
        profiles.bind_profile(
            owner,
            {
                "binding_id": f"binding-{PROFILE_ID}",
                "profile_id": PROFILE_ID,
                "profile_revision": 1,
                "deployment_head_id": deployment_head_id,
                "expected_binding_revision": 0,
                "expected_deployment_configuration_revision": 1,
                "expected_deployment_revision_id": deployment.id,
                "enabled": True,
                "readiness_observation_id": observation["observation_id"],
            },
        )
        actions.append(f"bound profile '{PROFILE_ID}' (ready)")
    except Exception as exc:
        if "revision_conflict" in str(getattr(exc, "code", "")):
            actions.append(f"profile binding already exists (idempotent)")
        else:
            raise

    # 4. Set the capability assignments for every meeting capability the
    #    endpoint serves (exact bindings — the SERVICE policy inherits nothing).
    for cid in MEETING_CAPABILITY_IDS:
        try:
            assignments.set_assignment(
                owner,
                {
                    "command_id": f"wire-metal-{cid}",
                    "expected_revision": 0,
                    "scope": {"kind": "capability", "capability_id": cid},
                    "entries": [{"profile_id": PROFILE_ID, "profile_revision": 1}],
                },
            )
            actions.append(f"assigned '{PROFILE_ID}' to '{cid}'")
        except Exception as exc:
            if "revision_conflict" in str(getattr(exc, "code", "")):
                actions.append(f"assignment for '{cid}' already exists (idempotent)")
            else:
                raise

    # 5. Also set up the legacy v1 profile for the effective_intel_cloud path.
    db.profiles.upsert(
        profile_id=PROFILE_ID,
        name=f"Metal intel ({model})",
        kind="openAICompatible",
        base_url=base_url,
        model=model,
    )
    actions.append(f"created v1 profile '{PROFILE_ID}' (legacy bridge)")

    return {
        "profile_id": PROFILE_ID,
        "base_url": base_url,
        "model": model,
        "capability": CAPABILITY_ID,
        "db_path": str(db_path),
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Wire a fresh HOME for metal intel dispatch.")
    parser.add_argument("--home", type=Path, default=None, help="Target HOME directory (default: $HOME)")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"OpenAI-compatible base URL (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model identity (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    home = args.home or Path(os.environ.get("HOME", "/tmp/hs151-rig"))
    result = wire(home, base_url=args.base_url, model=args.model)

    print(f"Wired metal intel dispatch in {home}")
    for action in result["actions"]:
        print(f"  - {action}")
    print(f"  profile_id: {result['profile_id']}")
    print(f"  base_url:   {result['base_url']}")
    print(f"  model:      {result['model']}")
    print(f"  capability: {result['capability']}")
    print(f"  db_path:    {result['db_path']}")


if __name__ == "__main__":
    main()
