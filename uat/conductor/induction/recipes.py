"""State recipes — named, idempotent, self-verifying worlds.

A recipe (``uat/recipes/<name>.yaml``) names a world state and composes:

- a **deck** (the boot posture; default ``golden-local``),
- ``includes:`` other recipes (their seeds/actions/probes fold in; cycles
  refuse at load),
- **seeds** (manifests applied through public routes),
- **actions** (spawn/kill a local mesh node, wait),

and closes with a **probe** — assertions read back through product routes.

**Idempotency is the contract.** Applying a recipe first evaluates its
probe; if the world already holds, it is a verified no-op. Otherwise it
stages (seeds carry deterministic ids so re-seeding upserts, never
duplicates) and then re-verifies — a recipe that cannot verify itself
raises loudly, naming the failed assertion.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .probes import ProbeEvaluator
from .seeds import Seeder, SeedRegistry


def recipes_dir() -> Path:
    override = os.environ.get("UAT_RECIPES_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "recipes"


class RecipeError(ValueError):
    pass


class RecipeVerifyError(RuntimeError):
    def __init__(self, message: str, result: "ApplyResult"):
        super().__init__(message)
        self.result = result


@dataclass
class Recipe:
    name: str
    title: str = ""
    description: str = ""
    deck: str = "golden-local"
    requires: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    link_caches: bool = True
    seeds: list[str] = field(default_factory=list)
    actions: list[Any] = field(default_factory=list)
    probe: list[Any] = field(default_factory=list)

    @property
    def requires_intel(self) -> bool:
        return "intel" in self.requires


@dataclass
class ApplyResult:
    recipe: str
    deck: str
    already_satisfied: bool
    probe: dict
    seeds: list[dict] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    restarted: bool = False

    def to_dict(self) -> dict:
        return {
            "recipe": self.recipe,
            "deck": self.deck,
            "already_satisfied": self.already_satisfied,
            "restarted": self.restarted,
            "probe": self.probe,
            "seeds": self.seeds,
            "actions": self.actions,
            "ok": self.probe.get("ok", False),
        }


class RecipeRegistry:
    """Loads recipes and resolves their include graph (cycle-safe)."""

    def __init__(self, directory: Path | None = None):
        self.directory = Path(directory) if directory else recipes_dir()
        self._cache: dict[str, Recipe] = {}

    def names(self) -> list[str]:
        if not self.directory.exists():
            return []
        return sorted(p.stem for p in self.directory.glob("*.yaml"))

    def load(self, name: str) -> Recipe:
        if name in self._cache:
            return self._cache[name]
        path = self.directory / f"{name}.yaml"
        if not path.exists():
            raise RecipeError(f"unknown recipe: {name!r} (looked in {self.directory})")
        doc = yaml.safe_load(path.read_text()) or {}
        if not isinstance(doc, dict):
            raise RecipeError(f"recipe {name!r} must be a mapping")
        boot = doc.get("boot") or {}
        recipe = Recipe(
            name=name,
            title=doc.get("title", name),
            description=doc.get("description", ""),
            deck=doc.get("deck", "golden-local"),
            requires=list(doc.get("requires") or []),
            includes=list(doc.get("includes") or []),
            link_caches=bool(boot.get("link_caches", True)),
            seeds=list(doc.get("seeds") or []),
            actions=list(doc.get("actions") or []),
            probe=list(doc.get("probe") or []),
        )
        self._cache[name] = recipe
        return recipe

    def resolve_order(self, name: str) -> list[str]:
        """The include chain in application order (deps first), cycle-refused."""
        order: list[str] = []
        visiting: set[str] = set()
        done: set[str] = set()

        def visit(n: str, stack: tuple[str, ...]) -> None:
            if n in done:
                return
            if n in visiting:
                cycle = " -> ".join(stack + (n,))
                raise RecipeError(f"recipe include cycle: {cycle}")
            visiting.add(n)
            recipe = self.load(n)
            for inc in recipe.includes:
                visit(inc, stack + (n,))
            visiting.discard(n)
            done.add(n)
            order.append(n)

        visit(name, ())
        return order

    def all(self) -> list[dict]:
        out = []
        for n in self.names():
            r = self.load(n)
            out.append(
                {
                    "name": r.name,
                    "title": r.title,
                    "description": r.description,
                    "deck": r.deck,
                    "requires": r.requires,
                    "includes": r.includes,
                    "seeds": r.seeds,
                    "probe_len": len(r.probe),
                }
            )
        return out


class RecipeEngine:
    """Applies recipes to a booted run through a RunManager-shaped host."""

    def __init__(
        self,
        registry: RecipeRegistry | None = None,
        seed_registry: SeedRegistry | None = None,
    ):
        self.registry = registry or RecipeRegistry()
        self.seed_registry = seed_registry or SeedRegistry()

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)

        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )

        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)

        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)

        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe

        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )

        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))

        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
            raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
        return result

    def _run_action(self, action: Any, run_id: str, host: "RecipeHost", client) -> dict:
        kind, arg = _split_action(action)
        if kind == "wait":
            time.sleep(float(arg))
            return {"action": "wait", "seconds": float(arg)}
        if kind == "spawn_node":
            name = arg["name"] if isinstance(arg, dict) else str(arg)
            node = host.spawn_node(run_id, name)
            return {"action": "spawn_node", "name": name, "pid": node.get("pid")}
        if kind == "kill_node":
            name = arg["name"] if isinstance(arg, dict) else str(arg)
            killed = host.kill_node(run_id, name)
            return {"action": "kill_node", "name": name, "killed": killed}
        if kind == "process_intel":
            # The web import enqueues intel (status 'queued'); headless, nothing
            # auto-drains it. Wait out the transcript parse, then drain the
            # deferred-intel queue synchronously — the same POST /api/intel/process
            # the web UI fires — so real intel runs on the configured endpoint.
            opts = arg if isinstance(arg, dict) else {}
            parse_timeout = float(opts.get("parse_timeout", 90))
            deadline = time.monotonic() + parse_timeout
            while time.monotonic() < deadline:
                meetings = client.get_json("/api/meetings", params={"limit": 50}).get(
                    "meetings", []
                )
                if meetings and not any(m.get("intel_status") == "importing" for m in meetings):
                    break
                time.sleep(2.0)
            from .product_client import ProductClient

            slow = ProductClient(client.base_url, token=client.token, timeout=600.0)
            total = 0
            for _ in range(int(opts.get("rounds", 4))):
                resp = slow.post_json("/api/intel/process", {"mode": "retry_now"})
                n = resp.json().get("processed", 0) if resp.status_code == 200 else 0
                total += n
                if n == 0:
                    break
            return {"action": "process_intel", "processed": total}
        if kind in ("spawn_pane", "arm_pane", "send_keys", "steer_pane"):
            from . import steering

            opts = arg if isinstance(arg, dict) else {"name": str(arg)}
            name = opts.get("name", "coder")
            session = steering.session_name(run_id, name)
            if kind == "spawn_pane":
                command = opts.get("command", "bash -c 'echo AWAITING-INPUT; sleep 1200'")
                res = host.spawn_pane(run_id, name, command)
                return {"action": "spawn_pane", "name": name, "session": session, "result": res}
            client_ = host.product_client(run_id)
            if kind == "arm_pane":
                res = steering.arm(client_, session, ttl_seconds=int(opts.get("ttl_seconds", 120)))
                return {"action": "arm_pane", "name": name, "result": res}
            if kind == "send_keys":
                keys = opts.get("keys") or []
                res = steering.send_keys(client_, session, list(keys))
                return {"action": "send_keys", "name": name, "keys": keys, "result": res}
            if kind == "steer_pane":
                res = steering.steer(client_, session, str(opts.get("text", "")))
                return {"action": "steer_pane", "name": name, "result": res}
        if kind == "create_profile":
            # Register a profile through the public route. Defaults to a meshNode
            # (so the hub surfaces its liveness); any field the route accepts —
            # including a bogus api_key to attack key-never-syncs — passes through.
            opts = arg if isinstance(arg, dict) else {"name": str(arg)}
            name = opts.get("name", "profile")
            body = {"id": opts.get("id", f"uat-profile-{name}"), "name": name, "kind": opts.get("kind", "meshNode")}
            for k in ("node", "api_key", "requires_key", "profile_id", "avatar", "role", "system_prompt"):
                if k in opts:
                    body[k] = opts[k]
            resp = client.post_json("/api/profiles", body)
            return {"action": "create_profile", "name": name, "status": resp.status_code}
        if kind == "dispatch_run":
            # The handoff arc's verb: drive a real ask ONTO the mesh worker via
            # the hub's own /api/ask (profile_id → meshNode → relay). A mesh run
            # WAITS on the relay queue while the worker claims + executes it, so
            # use a slow client. Capture the worker's CLAIM-count delta (its own
            # log) before→after — "the run moved" — and persist the response's
            # egress badge + output to a sidecar the probes read back.
            import json as _json

            from .product_client import ProductClient

            opts = arg if isinstance(arg, dict) else {}
            label = str(opts.get("run", "handoff"))
            node = str(opts.get("node", "uat-worker"))
            profile_id = str(opts.get("profile_id", "uat-seed-profile-mesh-edge"))
            prompt = str(
                opts.get(
                    "prompt",
                    "Summarize the pylon incident from the handoff note. Name the "
                    "canary token it carries, verbatim.",
                )
            )
            context = opts.get("context") or []
            timeout = float(opts.get("timeout", 600))

            marker = f"CLAIMED for node {node}"
            claims_before = host.node_log_text(run_id, node).count(marker)

            slow = ProductClient(client.base_url, token=client.token, timeout=timeout)
            body: dict[str, Any] = {"prompt": prompt, "profile_id": profile_id, "lens": "Ask"}
            if context:
                body["context"] = context
            resp = slow.post_json("/api/ask", body)
            data = resp.json() if resp.status_code == 200 else {}

            claims_after = host.node_log_text(run_id, node).count(marker)

            sidecar = {
                "run": label,
                "node": node,
                "profile_id": profile_id,
                "status": resp.status_code,
                "ok": resp.status_code == 200,
                "provider": data.get("provider"),
                "egress": data.get("egress"),
                "model": data.get("model"),
                "output": data.get("output", ""),
                "error": data.get("error"),
                "claims_before": claims_before,
                "claims_after": claims_after,
            }
            home = host.run_home(run_id)
            (home / f"uat-dispatch-{label}.json").write_text(_json.dumps(sidecar))
            return {
                "action": "dispatch_run",
                "run": label,
                "status": resp.status_code,
                "egress": sidecar["egress"],
                "claimed": claims_after > claims_before,
            }
        if kind == "sync_meeting":
            # Stage a deterministic meeting through the product's cross-device
            # sync ingress. This is the public route a paired iPad uses, and it
            # gives fully-local recipes a real meeting/action-item world without
            # manufacturing product DB rows or requiring an LLM to word an
            # action exactly. The fixed timestamp makes a repeated apply a
            # last-write-wins no-op.
            opts = arg if isinstance(arg, dict) else {"id": str(arg)}
            meeting_id = str(opts.get("id", "uat-synced-meeting"))
            action_id = str(opts.get("action_id", f"{meeting_id}-action"))
            stamp = str(opts.get("timestamp", "2035-01-15T10:00:00Z"))
            title = str(opts.get("title", "UAT synced meeting"))
            task = str(opts.get("task", "Verify the staged acceptance world"))
            owner = opts.get("owner", "UAT owner")
            raw_action_items = opts.get("action_items")
            if isinstance(raw_action_items, list) and raw_action_items:
                action_items = []
                for index, raw_item in enumerate(raw_action_items):
                    item = raw_item if isinstance(raw_item, dict) else {}
                    action_items.append(
                        {
                            "id": str(
                                item.get("id") or f"{meeting_id}-action-{index + 1}"
                            ),
                            "task": str(item.get("task") or task),
                            "owner": item.get("owner", owner),
                            "due": item.get("due"),
                            "status": str(item.get("status", "pending")),
                            "review_state": str(
                                item.get("review_state", "accepted")
                            ),
                            "source_timestamp": float(
                                item.get("source_timestamp", 0.0)
                            ),
                            "created_at": stamp,
                        }
                    )
            else:
                action_items = [
                    {
                        "id": action_id,
                        "task": task,
                        "owner": owner,
                        "due": None,
                        "status": "pending",
                        "review_state": str(
                            opts.get("review_state", "accepted")
                        ),
                        "source_timestamp": 0.0,
                        "created_at": stamp,
                    }
                ]
            record = {
                "meta": {
                    "id": meeting_id,
                    "kind": "meeting",
                    "last_modified": stamp,
                    "deleted": False,
                },
                "value": {
                    "id": meeting_id,
                    "started_at": stamp,
                    "ended_at": stamp,
                    "title": title,
                    "tags": ["uat-seed", "sync-staged"],
                    "segments": [
                        {
                            "text": task,
                            "speaker": "UAT owner",
                            "speaker_id": None,
                            "start_time": 0.0,
                            "end_time": 2.0,
                            "is_bookmarked": False,
                            "device_id": "uat-harness",
                        }
                    ],
                    "bookmarks": [],
                    "intel": {
                        "timestamp": 2.0,
                        "topics": ["UAT"],
                        "action_items": action_items,
                        "summary": str(
                            opts.get(
                                "summary",
                                "A deterministic meeting staged through the sync API.",
                            )
                        ),
                    },
                    "intel_status": {
                        "state": "complete",
                        "detail": "UAT sync-staged fixture",
                        "requested_at": stamp,
                        "completed_at": stamp,
                    },
                    "mic_label": "Me",
                    "remote_label": "Remote",
                    "web_url": None,
                },
            }
            resp = client.post_json("/api/sync/push", {"meetings": [record]})
            data = resp.json() if resp.status_code == 200 else {}
            return {
                "action": "sync_meeting",
                "meeting_id": meeting_id,
                "action_id": action_items[0]["id"],
                "action_ids": [item["id"] for item in action_items],
                "status": resp.status_code,
                "merged": (data.get("received") or {}).get("meetings"),
                **(
                    {"error": data.get("error") or resp.text[:200]}
                    if resp.status_code != 200
                    else {}
                ),
            }
        if kind == "propose_github_card":
            # Create, but deliberately do not approve, the aftercare proposal.
            # The product's proposal read route is the probe seam; no connector
            # executes and no network egress occurs during staging.
            opts = arg if isinstance(arg, dict) else {}
            meeting_id = str(opts.get("meeting_id", "uat-egress-meeting"))
            action_id = str(opts.get("action_item_id", "uat-egress-action"))
            repo = str(opts.get("repo", "acme/holdspeak-uat"))
            resp = client.post_json(
                f"/api/meetings/{meeting_id}/aftercare/file-issue",
                {"action_item_id": action_id, "repo": repo},
            )
            data = resp.json() if resp.status_code == 200 else {}
            proposal = data.get("proposal") or {}
            return {
                "action": "propose_github_card",
                "meeting_id": meeting_id,
                "proposal_id": proposal.get("id"),
                "target": proposal.get("target"),
                "proposal_status": proposal.get("status"),
                "status": resp.status_code,
                **(
                    {"error": data.get("error") or resp.text[:200]}
                    if resp.status_code != 200
                    else {}
                ),
            }
        if kind == "teach_correction":
            # Record a dictation correction so the learned-from-N digest has a
            # KNOWN count to check honestly against.
            opts = arg if isinstance(arg, dict) else {}
            resp = client.post_json(
                "/api/dictation/corrections",
                {"kind": opts.get("kind", "intent"), "text": opts.get("text", "teh"), "value": opts.get("value", "the")},
            )
            return {"action": "teach_correction", "status": resp.status_code}
        return {"action": kind, "error": f"unknown action {kind!r}"}


def _split_action(action: Any) -> tuple[str, Any]:
    if isinstance(action, str):
        return action, True
    if isinstance(action, dict) and len(action) == 1:
        (kind, arg), = action.items()
        return str(kind), arg
    raise RecipeError(f"a recipe action must be a single-key mapping or string: {action!r}")


# A structural type note: RunManager satisfies RecipeHost (duck-typed).
class RecipeHost:  # pragma: no cover - documentation of the required interface
    def ensure_deck(self, run_id: str, deck: str, *, link_caches: bool) -> bool: ...
    def product_client(self, run_id: str): ...
    def run_home(self, run_id: str) -> Path: ...
    def spawn_node(self, run_id: str, name: str) -> dict: ...
    def kill_node(self, run_id: str, name: str) -> bool: ...
    def node_log_text(self, run_id: str, node: str) -> str: ...
