# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_philo10_face_words.py to restore.

# ruff: noqa


# --- test_the_derivation_sees_the_known_codes_of_each_kind: P2/P4: checks the test's own code-derivation helper and pins exact face strings; the every-code-has-a-word fence stays
def test_the_derivation_sees_the_known_codes_of_each_kind() -> None:
    """Guard the derivation itself: codes from every source it reads are there, with their kinds."""
    got = codes.emitted()
    want = {
        "destination_parked": "refused",            # ChannelRefused literal
        "folder_missing": "refused",                # ValidationError code=
        "github_target_not_found": "failed",        # a PINNED table
        "github_not_authenticated": "failed",       # a pinned() override
        "permission_denied": "failed",              # FAILED_ON_CREATE
        "atlassian_not_logged_in": "failed",        # a reason = (a if .. else b)
        "read_back_mismatch": "unknown",            # Outcome("unknown", literal)
        "github_exit_": "unknown",                  # an f-string template
        "reaped": "unknown",                        # the kernel's row reason default
        "interrupted": "unknown",                   # the restart's row reason
        "tls_failed": "unknown",                    # _classify, through EmailTransportError
        "email_key_store_locked": "refused",        # EmailKeyError, through the flow
        "payload_changed": "failed",                # the CLI flow's declared source
        "resend_quota_exceeded": "failed",          # PHILO-10-07: Resend's pinned (status, name) table
        "resend_forbidden": "failed",               # PHILO-10-07: Resend's 403 fallback literal
    }
    for code, kind in want.items():
        assert kind in got.get(code, {}).get("kinds", set()), (code, kind, got.get(code))
    assert "owner_principal_required" in codes.declared_refusals()


# --- test_the_census_codes_have_their_words: P2/P4: checks the test's own code-derivation helper and pins exact face strings; the every-code-has-a-word fence stays
@pytest.mark.parametrize("code, word", [
    ("github_target_not_found", "Issue not found"),
    ("github_permission_denied", "No permission"),
    ("jira_cannot_be_edited", "Cannot comment"),
    ("atlassian_unauthorized", "Not signed in"),
])
def test_the_census_codes_have_their_words(code, word) -> None:
    ts = (REPO / "web/src/features/channels/channels.ts").read_text()
    table = re.search(r"const FAILED[^=]*=\s*\{(.*?)\n\};", ts, re.S).group(1)
    assert f'  {code}: "{word}",' in table
