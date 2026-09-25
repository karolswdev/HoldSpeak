"""Verify retained actual-atlas transport and readonly observer evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for width, red_http in [(1440, "red-http-1440-import-corrected"), (393, "red-http-393-atlas-width")]:
    results = {}
    for label in [red_http, f"red-op-{width}", f"green-http-{width}", f"green-op-{width}"]:
        sidecar = json.loads((ROOT / label / "observer-rows.json").read_text())
        observations = list((ROOT / label).glob("*/observation.json"))
        assert len(observations) == 1, label
        observation = json.loads(observations[0].read_text())
        assert observation["verdict"] == sidecar["rig_verdict"] == "pass", label
        assert Path(sidecar["db_path"]).is_relative_to(Path(sidecar["home"])), label
        assert sidecar["count"] == len(sidecar["rows"]), label
        assert all(row["error_code"] == "not_found" for row in sidecar["rows"]), label
        assert all("philo504-deliberately-absent" in row["args_summary"] for row in sidecar["rows"]), label
        results[label] = sidecar["count"]
        print(label, "rows:", [(row["id"], row["service"], row["method"], row["error_code"]) for row in sidecar["rows"]])
    assert results[red_http] == 2
    assert results[f"red-op-{width}"] == 1
    assert results[f"green-http-{width}"] == results[f"green-op-{width}"] == 1
    print(f"{width}: missing-decision parity FAIL 2:1 -> PASS 1:1")
print("PASS: both real atlas transports at both widths; no missing-id observation retry")
