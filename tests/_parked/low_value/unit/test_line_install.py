# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_line_install.py to restore.

# ruff: noqa


# --- test_the_build_script_pins_the_versions_and_builds_bsd_modules_only: P1/P4: regex-matches version and SHA literals written in a shell script's text
def test_the_build_script_pins_the_versions_and_builds_bsd_modules_only() -> None:
    text = SCRIPT.read_text()
    assert re.search(r'^BARESIP_VERSION="4\.12\.0"$', text, re.M)
    assert re.search(r'^LIBRE_VERSION="4\.12\.0"$', text, re.M)
    assert re.search(r'^BARESIP_SHA256="710d79d60c15c09f0aeb93e5d2f219e7f12ab93f62cab826e4280592a1ea155f"$', text, re.M)
    assert re.search(r'^LIBRE_SHA256="707b6194dd3b8d3fb1641ca08a0999aaac1d38d36b5c45514777a13ded311923"$', text, re.M)
    assert "sha256sum -c" in text
    modules = re.search(r'^MODULES="([^"]+)"$', text, re.M).group(1).split(";")
    assert tuple(modules) == MODULES  # the build list is the load list
    assert not set(modules) & set(FORBIDDEN)
    # No command runs sudo or apt (a message may name the owner's sudo press).
    code = [line for line in text.splitlines() if not line.lstrip().startswith(("#", "echo"))]
    assert not any(re.search(r"(^|[;&|(]\s*)(sudo|apt|apt-get)\b", line.strip()) for line in code)
    assert 'id -u)" = "0"' in text  # it refuses to run as root
    assert SCRIPT.stat().st_mode & 0o111
