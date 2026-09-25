"""Check the retained actual-atlas S4 transition traces, not a calibration."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for width in (393, 1440):
    for colour, expected in (("red", "fail"), ("green", "pass")):
        folder = ROOT / f"{colour}-s4-{width}{'-continuous' if colour == 'red' else ''}"
        paths = list(folder.glob("*/observation.json"))
        assert len(paths) == 1, paths
        record = json.loads(paths[0].read_text())
        assert record["case_id"] == "case.closure.chain.s4_saved_content"
        assert record["verdict"] == expected, record["notes"]
        probe = record["after"]["transition_probe"]
        assert probe["armedAt"] <= probe["clickedAt"]
        assert probe["firstReadFrame"]["readable"]
        frames = [frame for frame in probe["frames"] if not frame["editing"]]
        assert frames
        bad = probe["firstUnreadableReadFrame"]
        if colour == "red":
            assert bad and bad["text"] == "DECISION"
            assert any(not frame["readable"] for frame in frames)
        else:
            assert bad is None and all(frame["readable"] for frame in frames)
        print(f"{width} {colour}: {record['verdict'].upper()}; first read "
              f"{probe['firstReadFrame']['atMs']:.1f} ms readable; "
              f"first blank {str(round(bad['atMs'], 1)) + ' ms' if bad else 'none'}; "
              f"{len(frames)} read-mode frames")
