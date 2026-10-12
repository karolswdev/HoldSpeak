"""PHILO-10-05 (Muad'Dib's ruling on #698): no raw code on the Send face, closed as a class.

Every code the channel services can emit -- derived from their source and their
declared refusals (``tests/unit/_philo10_codes.py``), never typed by hand -- has a
plain word in the face's tables (``web/src/features/channels/channels.ts``:
REFUSED / FAILED / UNKNOWN and their prefix tables, then the library's
REFUSAL_WORDS). A new code with no word, or a new place that passes a code
through a variable the derivation does not follow, fails here.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _philo10_codes as codes  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def test_every_emitted_code_has_a_face_word() -> None:
    assert codes.missing() == []


def test_no_code_expression_is_unsupported() -> None:
    """Codex Astra r1 on #698 (finding 1): an f-string outside ALLOWED_TEMPLATES, a
    ``.format()``, a concatenation, a call -- any code expression the derivation
    cannot read, in a producer or behind a declared flow -- fails here, by name."""
    assert codes.emitted()["__unsupported__"]["where"] == []


def test_every_variable_code_site_is_followed() -> None:
    """A code passed through a variable is followed by FLOWS; a new such site fails until it is."""
    seen = set(codes.emitted()["__variables__"]["where"])
    assert seen == set(codes.FLOWS), (sorted(seen - set(codes.FLOWS)), sorted(set(codes.FLOWS) - seen))


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


@pytest.mark.parametrize("code, kind", [
    ("slack_webhook_invalid", "refused"),
    ("invalid_payload", "failed"),
    ("rollup_error", "unknown"),
])
def test_slack_codes_are_derived_from_the_backend_source(code: str, kind: str) -> None:
    entry = codes.emitted().get(code, {})
    assert kind in entry.get("kinds", set()), (code, entry)
    assert any(where.startswith("holdspeak/services/channel_slack.py:") for where in entry.get("where", [])), entry


def test_the_face_reads_its_tables_through_the_word_functions() -> None:
    """The tables are the ones refusedWord / failedWord / unknownWord read (no second table)."""
    ts = (REPO / "web/src/features/channels/channels.ts").read_text()
    assert "export const refusedWord = (c: string) => REFUSED[c] ?? byPrefix(REFUSED_PREFIX, c) ?? refusalWord(c);" in ts
    assert "export const failedWord = (c: string) => word(FAILED, FAILED_PREFIX, c);" in ts
    assert "export const unknownWord = (c: string) => word(UNKNOWN, UNKNOWN_PREFIX, c);" in ts


def test_every_face_word_is_plain() -> None:
    """ASD-STE100 on the face: capital words, no code, no underscore."""
    ts = (REPO / "web/src/features/channels/channels.ts").read_text()
    lib = (REPO / "web/src/desk/surface/egress.ts").read_text()
    blocks = [re.search(rf"const {n}[^=]*=\s*\{{(.*?)\n\}};", ts, re.S).group(1) for n in ("REFUSED", "FAILED", "UNKNOWN")]
    blocks += [re.search(r"const REFUSAL_WORDS[^=]*=\s*\{(.*?)\n\};", lib, re.S).group(1)]
    blocks += [re.search(rf"const {n}[^=]*=\s*\[(.*?)\n\];", ts, re.S).group(1)
               for n in ("REFUSED_PREFIX", "FAILED_PREFIX", "UNKNOWN_PREFIX")]
    words = [w for b in blocks for w in re.findall(r':\s*"([^"]+)",|, "([^"]+)"\]', b) for w in w if w]
    assert len(words) > 100
    for word in words:
        assert re.fullmatch(r"[A-Z0-9 ]+", word), word


@pytest.mark.parametrize("code, word", [
    ("github_target_not_found", "ISSUE NOT FOUND"),
    ("github_permission_denied", "NO PERMISSION"),
    ("jira_cannot_be_edited", "CANNOT COMMENT"),
    ("atlassian_unauthorized", "NOT SIGNED IN"),
])
def test_the_census_codes_have_their_words(code, word) -> None:
    ts = (REPO / "web/src/features/channels/channels.ts").read_text()
    table = re.search(r"const FAILED[^=]*=\s*\{(.*?)\n\};", ts, re.S).group(1)
    assert f'  {code}: "{word}",' in table
