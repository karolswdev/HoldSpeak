"""Print one line per test from a JUnit XML: PASS, or FAIL with the first assertion line."""
import sys
import xml.etree.ElementTree as ET

for case in ET.parse(sys.argv[1]).getroot().iter("testcase"):
    name = case.get("name")
    bad = case.find("failure") if case.find("failure") is not None else case.find("error")
    if bad is None:
        print(f"PASS  {name}")
        continue
    lines = [ln.strip() for ln in (bad.get("message") or "").splitlines() if ln.strip()]
    body = [ln.strip() for ln in (bad.text or "").splitlines()]
    waiting = [ln for ln in lines + body if "waiting for locator" in ln]
    detail = (" | " + waiting[0][-160:]) if waiting else ""
    print(f"FAIL  {name} :: {(lines[0] if lines else '')[:220]}{detail}")
