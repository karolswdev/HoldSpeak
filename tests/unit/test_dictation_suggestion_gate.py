"""HS-39-04: project-doc suggestion quality gate (dedup / recurrence / consolidate)."""

from __future__ import annotations

from holdspeak.project_doc_suggestions import (
    ProjectDocSuggestion,
    consolidate_suggestions,
    suggestion_already_covered,
    suggestion_signature,
)
from holdspeak.web.routes.dictation._helpers import _store_project_doc_suggestion


# --- signature -------------------------------------------------------------


def test_signature_is_stable_and_near_dupe_matches():
    a = suggestion_signature(".hs/memory/x.md", "append only ledger never delete rows")
    b = suggestion_signature(".hs/memory/x.md", "Never delete rows; append-only ledger.")
    assert a == b  # token-set + path → near-dupes collide
    c = suggestion_signature(".hs/memory/y.md", "append only ledger never delete rows")
    assert a != c  # different target → different signature


# --- dedup vs existing doc -------------------------------------------------


def test_already_covered_true_when_doc_has_the_tokens():
    doc = "The ledger is append-only: never UPDATE or DELETE a posted row."
    assert suggestion_already_covered("append-only ledger; never delete a row", doc) is True


def test_already_covered_false_for_novel_content():
    doc = "The ledger is append-only."
    novel = "Charges must validate the Idempotency-Key header against the idempotency_keys table."
    assert suggestion_already_covered(novel, doc) is False


def test_already_covered_edge_cases():
    assert suggestion_already_covered("", "anything") is True   # nothing to add
    assert suggestion_already_covered("a brand new fact", "") is False  # empty doc


# --- consolidation ---------------------------------------------------------


def _sug(path: str, rat: str, content: str) -> ProjectDocSuggestion:
    return ProjectDocSuggestion(target_path=path, rationale=rat, content=content)


def test_consolidate_empty_and_single():
    assert consolidate_suggestions([]) is None
    assert consolidate_suggestions([None]) is None
    lone = _sug(".hs/memory/x.md", "r", "c")
    assert consolidate_suggestions([lone]) is lone


def test_consolidate_merges_several():
    s1 = _sug(".hs/memory/x.md", "rule one", "Fact one.")
    s2 = _sug(".hs/memory/x.md", "rule two", "Fact two.")
    s3 = _sug(".hs/memory/x.md", "rule two", "Fact two.")  # duplicate content
    merged = consolidate_suggestions([s1, s2, s3])
    assert merged is not None
    assert merged.target_path == ".hs/memory/x.md"
    assert "Fact one." in merged.content and "Fact two." in merged.content
    assert merged.content.count("Fact two.") == 1  # de-duplicated
    assert "Consolidated from 3" in merged.rationale


# --- recurrence suppression (store level) ----------------------------------


def _stages_with_suggestion() -> list[dict]:
    return [
        {
            "stage_id": "project-rewriter",
            "metadata": {
                "project_doc_suggestion": {
                    "target_path": ".hs/memory/foo.md",
                    "rationale": "Preserves a convention.",
                    "content": "Some genuinely new project fact worth keeping.",
                }
            },
        }
    ]


def test_store_keeps_then_suppresses_dismissed(tmp_path):
    project = {"root": str(tmp_path)}
    stages = _stages_with_suggestion()

    store: dict[str, dict[str, str]] = {}
    assert _store_project_doc_suggestion(project, stages, store, dismissed_signatures=set()) == "stored"
    assert store  # it's there

    sig = suggestion_signature(".hs/memory/foo.md", "Some genuinely new project fact worth keeping.")
    store2: dict[str, dict[str, str]] = {}
    status = _store_project_doc_suggestion(
        project, stages, store2, dismissed_signatures={sig}
    )
    assert status == "dismissed"
    assert not store2  # suppressed, did not recur


def test_store_no_suggestion_is_reported(tmp_path):
    project = {"root": str(tmp_path)}
    assert _store_project_doc_suggestion(project, [], {}, dismissed_signatures=set()) == "no_suggestion"
