# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_evidence_archive.py to restore.

# ruff: noqa


# --- test_the_manifest_hash_is_the_one_the_archive_doc_names: P8: repo-hygiene check of pm/ARCHIVE.md against a git tag; no user outcome
def test_the_manifest_hash_is_the_one_the_archive_doc_names() -> None:
    doc = (REPO / "pm" / "ARCHIVE.md").read_text(encoding="utf-8")
    named = re.search(r"Manifest SHA-256: `([0-9a-f]{64})`", doc)
    assert named, "pm/ARCHIVE.md must name the manifest SHA-256"
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == named.group(1)


# --- test_no_manifest_entry_is_in_the_tree: P8: repo-hygiene check of pm/ARCHIVE.md against a git tag; no user outcome
def test_no_manifest_entry_is_in_the_tree() -> None:
    entries = _entries()
    assert len(entries) == len(set(entries))
    present = [name for name in entries if (REPO / name).exists()]
    assert present == [], "a file in the tree is not archived; take it out of the manifest"


# --- test_every_manifest_entry_is_on_the_archive_tag: P8: repo-hygiene check of pm/ARCHIVE.md against a git tag; no user outcome
def test_every_manifest_entry_is_on_the_archive_tag() -> None:
    listed = subprocess.run(
        ["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", "-z", TAG],
        capture_output=True, timeout=120,
    )
    if listed.returncode != 0:
        pytest.skip(f"tag {TAG} is not in this clone (git fetch origin tag {TAG})")
    on_tag = set(listed.stdout.decode("utf-8").split("\0"))
    missing = [name for name in _entries() if name not in on_tag]
    assert missing == []
