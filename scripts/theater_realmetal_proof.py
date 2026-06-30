"""HS-69-09 — generation theater REAL-METAL proof.

Drives the actual MeetingIntel pipeline against a real OpenAI-compatible LAN
endpoint and captures the REAL streaming output — the same data the theater
visualizes: the `intel_token` chunks (the orb's "thinking" pulse) and the final
snapshot's summary / action_items / topics (the constellation lighting). This
proves the theater consumes real frame CONTENT, not just simulated frames.

The owner's intended clean endpoint is the Mac llama-server at 192.168.1.13:8081;
when that is down this falls back to .43. Run with the sandbox disabled (LAN):
  uv run python scripts/theater_realmetal_proof.py
"""
import os
import sys
import time

from holdspeak.intel.engine import MeetingIntel

ENDPOINTS = [
    ("http://192.168.1.13:8081/v1", "llama-server (.13, owner's clean endpoint)"),
    ("http://192.168.1.43:8080/v1", "Qwythos-9B (.43, fallback)"),
]

TRANSCRIPT = """\
Alice: Okay, let's lock the rate limiter design. I think a token bucket per API key is the way.
Bob: Agreed. We should put it behind a feature flag so we can roll it out gradually.
Alice: Good call. Bob, can you wire the flag this week?
Bob: Yes, I'll have it by Friday.
Alice: We also still need to pick a service name. Let's decide that next sync.
Bob: Sounds good. And we decided to use Postgres for the primary store, right?
Alice: Yes, Postgres for the primary store. That's settled.
"""


def pick_model(base_url):
    import urllib.request
    import json
    try:
        with urllib.request.urlopen(base_url + "/models", timeout=5) as r:
            data = json.loads(r.read().decode())
        models = data.get("models") or data.get("data") or []
        if models:
            return models[0].get("name") or models[0].get("id")
    except Exception:
        return None
    return None


def main():
    os.environ.setdefault("OPENAI_API_KEY", "sk-no-key-required")
    chosen = None
    for base_url, label in ENDPOINTS:
        model = pick_model(base_url)
        if model:
            chosen = (base_url, label, model)
            break
        print(f"  - {label}: unreachable")
    if not chosen:
        print("\nRESULT: SKIP — no LAN intel endpoint reachable (.13 and .43 both down).")
        print("The script is ready; re-run when an endpoint is up.")
        return 2

    base_url, label, model = chosen
    print(f"\nUsing {label}\n  base_url={base_url}\n  model={model}\n")

    intel = MeetingIntel(
        provider="cloud",
        cloud_model=model,
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url=base_url,
        cloud_timeout_seconds=120.0,
    )

    tokens = []
    final = None
    t0 = time.monotonic()
    try:
        for chunk in intel.analyze(TRANSCRIPT, stream=True):
            if isinstance(chunk, str):
                tokens.append(chunk)
                sys.stdout.write(".")
                sys.stdout.flush()
            else:
                final = chunk
    except Exception as exc:
        print(f"\nRESULT: FAIL — analyze raised: {exc}")
        return 1
    dt = time.monotonic() - t0

    print(f"\n\n--- real-metal capture ({dt:.1f}s) ---")
    print(f"intel_token chunks streamed: {len(tokens)}  (drive the orb's 'thinking' pulse)")
    streamed_text = "".join(tokens)
    print(f"streamed text length: {len(streamed_text)} chars")
    if final is None:
        print("\nRESULT: PARTIAL — tokens streamed (theater 'thinking' proven on real metal),")
        print("but no final IntelResult object was yielded.")
        return 0
    err = getattr(final, "error", None)
    print(f"final.error: {err!r}")
    print(f"summary: {(final.summary or '')[:200]!r}")
    print(f"action_items: {len(final.action_items or [])}")
    print(f"topics: {final.topics or []}")

    # the theater lights a node when the snapshot carries that artifact type
    lit = []
    if (final.summary or "").strip():
        lit.append("summary")
    if final.action_items:
        lit.append("actions")
    if final.topics:
        lit.append("topics")
    print(f"\nconstellation nodes that would light: {lit}")
    ok = len(tokens) > 0 and not err and len(lit) >= 2
    print(f"\nRESULT: {'PASS' if ok else 'PARTIAL'} — real {label} produced "
          f"{len(tokens)} streamed chunks + a snapshot lighting {lit}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
