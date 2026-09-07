"""HS-200-08: the corpus, its split, and the deterministic invariant checks.

Five things are proved here:

1. The corpus satisfies its schema and the phase's acceptance shape: at least
   thirty episodes over the three categories, with at least a third held out.
2. The manifest is derived from the episode files and cannot drift from them.
3. A tuning step cannot read a held-out acceptance episode.
4. Every invariant check judges a good output and a bad one, and severity
   comes from the checker, not from the corpus file.
5. A critical factual failure cannot be averaged away by a passing majority.

The runner and its real product paths are proved separately, in
``tests/integration/test_phase200_semantic_evaluation.py``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.phase200 import checks

REPO = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "phase200_eval", REPO / "scripts" / "phase200_eval.py"
)
phase200_eval = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(phase200_eval)  # type: ignore[union-attr]
build_report = phase200_eval.build_report


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    return checks.load_corpus()


@pytest.fixture(scope="module")
def manifest() -> dict:
    return checks.load_manifest()


# ── The corpus and its manifest ───────────────────────────────────────


class TestCorpusShape:
    def test_at_least_thirty_episodes_over_three_categories(self, corpus):
        assert len(corpus) >= 30, f"the corpus holds {len(corpus)} episodes"
        by_category = {category: 0 for category in checks.CATEGORIES}
        for episode in corpus:
            by_category[episode["category"]] += 1
        assert all(count >= 10 for count in by_category.values()), by_category

    def test_every_episode_validates(self, corpus):
        for episode in corpus:
            checks.validate_episode(episode)  # raises CorpusError otherwise

    def test_a_third_is_held_out_in_every_category(self, corpus):
        for category in checks.CATEGORIES:
            rows = [episode for episode in corpus if episode["category"] == category]
            held = [row for row in rows if row["split"] == checks.SPLIT_HELD_OUT]
            assert len(held) * 3 >= len(rows), f"{category}: {len(held)} of {len(rows)} held out"

    def test_the_required_variations_are_covered(self, corpus):
        tags = {tag for episode in corpus for tag in episode["tags"]}
        for required in (
            "no_source", "partial_source", "stale_source", "revoked_source",
            "contradictory_source", "irrelevant_citation", "correction",
            "repeated_question", "dismissed_suggestion", "ambiguous_identity",
            "missing_owner", "missing_date", "uncertain_date", "long_context",
            "unavailable_tools", "model_failure", "omitted_evidence",
            "misleading_narrative",
        ):
            assert required in tags, f"no episode carries the {required!r} variation"

    def test_every_invariant_kind_is_exercised(self, corpus):
        kinds = {invariant["kind"] for episode in corpus for invariant in episode["invariants"]}
        assert kinds == set(checks.CHECKS), kinds

    def test_manifest_matches_the_episode_files(self, corpus, manifest):
        rebuilt = checks.build_manifest(corpus, split_rule=manifest["split_rule"])
        assert rebuilt["episodes"] == manifest["episodes"], (
            "manifest is stale: uv run python scripts/phase200_eval.py manifest"
        )
        assert rebuilt["counts"] == manifest["counts"]
        assert manifest["corpus_version"] == checks.CORPUS_VERSION

    def test_manifest_records_the_split_rule_and_the_held_out_ids(self, manifest, corpus):
        assert "before any prompt" in manifest["split_rule"]
        held = sorted(e["id"] for e in corpus if e["split"] == checks.SPLIT_HELD_OUT)
        assert sorted(manifest["held_out_ids"]) == held

    def test_material_hash_is_the_context_identity(self, corpus, manifest):
        digests = {row["id"]: row["material_sha256"] for row in manifest["episodes"]}
        for episode in corpus:
            assert checks.material_digest(episode) == digests[episode["id"]]

    def test_the_manifest_command_reports_staleness(self):
        result = subprocess.run(
            [sys.executable, "scripts/phase200_eval.py", "manifest", "--check"],
            cwd=REPO, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


# ── The split is separated before tuning ──────────────────────────────


class TestSplitSeparation:
    def test_tuning_episodes_exclude_the_held_out_set(self, corpus):
        tuning = checks.tuning_episodes(corpus)
        assert tuning, "no training episodes"
        assert all(episode["split"] == checks.SPLIT_TRAIN for episode in tuning)

    def test_a_tuning_helper_refuses_a_held_out_episode(self, corpus):
        held = next(e for e in corpus if e["split"] == checks.SPLIT_HELD_OUT)
        with pytest.raises(checks.HeldOutEpisodeError) as excinfo:
            checks.read_for_tuning(held)
        assert held["id"] in str(excinfo.value)

    def test_a_tuning_helper_reads_a_training_episode(self, corpus):
        train = next(e for e in corpus if e["split"] == checks.SPLIT_TRAIN)
        assert checks.read_for_tuning(train) == train["material"]


# ── Each invariant, on a good output and a bad one ────────────────────


def _episode(kind: str, params: dict, material: dict | None = None) -> dict:
    return {
        "id": "T-01",
        "corpus_version": checks.CORPUS_VERSION,
        "category": "update",
        "split": checks.SPLIT_TRAIN,
        "title": "synthetic",
        "tags": [],
        "material": material or {},
        "invariants": [{"kind": kind, "params": params}],
    }


class TestCorrectionHonoured:
    PARAMS = {"field": "deadline", "superseded": ["2026-03-03"], "current": "2026-04-14"}

    def test_the_corrected_value_passes(self):
        result = checks.check_correction_honoured(
            _episode("correction_honoured", self.PARAMS),
            {"text": "The review is on 2026-04-14."},
            self.PARAMS,
        )
        assert result.passed

    def test_restating_the_superseded_value_is_critical(self):
        result = checks.check_correction_honoured(
            _episode("correction_honoured", self.PARAMS),
            {"text": "The review is on 2026-03-03."},
            self.PARAMS,
        )
        assert not result.passed and result.critical
        assert result.failure_kind == checks.FAILURE_SUPERSEDED_RESTATED

    def test_naming_the_old_value_as_the_old_one_is_not_a_restatement(self):
        result = checks.check_correction_honoured(
            _episode("correction_honoured", self.PARAMS),
            {"text": "The review moved from 2026-03-03 to 2026-04-14."},
            self.PARAMS,
        )
        assert result.passed

    def test_a_field_holding_the_stale_value_is_critical(self):
        result = checks.check_correction_honoured(
            _episode("correction_honoured", self.PARAMS),
            {"text": "The review is on 2026-04-14.", "fields": {"deadline": "2026-03-03"}},
            self.PARAMS,
        )
        assert not result.passed and result.critical

    def test_omitting_the_correction_is_a_soft_failure(self):
        result = checks.check_correction_honoured(
            _episode("correction_honoured", self.PARAMS),
            {"text": "The brief is ready."},
            self.PARAMS,
        )
        assert not result.passed and not result.critical
        assert result.failure_kind == checks.FAILURE_CORRECTION_ABSENT


class TestQuestionNotRepeated:
    PARAMS = {"answered": [{"text": "Who owns it?", "keywords": ["who", "own"]}]}

    def test_a_new_question_passes(self):
        result = checks.check_question_not_repeated(
            _episode("question_not_repeated", self.PARAMS),
            {"questions": ["What is the rollback plan?"]},
            self.PARAMS,
        )
        assert result.passed

    def test_asking_an_answered_question_again_fails(self):
        result = checks.check_question_not_repeated(
            _episode("question_not_repeated", self.PARAMS),
            {"questions": ["Who owns the migration?"]},
            self.PARAMS,
        )
        assert not result.passed
        assert result.failure_kind == checks.FAILURE_QUESTION_REPEATED

    def test_a_repeat_is_not_a_critical_factual_failure(self):
        result = checks.check_question_not_repeated(
            _episode("question_not_repeated", self.PARAMS),
            {"questions": ["Who owns the migration?"]},
            self.PARAMS,
        )
        assert not result.critical


class TestAbsentSourceUnknown:
    PARAMS = {"field": "deadline", "reason": "no source carries a date"}
    MATERIAL = {"sources": [{"text": "Scope only. No schedule agreed."}]}

    def test_a_typed_unknown_passes(self):
        result = checks.check_absent_source_unknown(
            _episode("absent_source_unknown", self.PARAMS, self.MATERIAL),
            {"text": "No deadline is recorded.", "fields": {"deadline": {"unknown": "no_source"}}},
            self.PARAMS,
        )
        assert result.passed

    def test_an_invented_date_is_critical(self):
        result = checks.check_absent_source_unknown(
            _episode("absent_source_unknown", self.PARAMS, self.MATERIAL),
            {"text": "The rollout completes on 2026-08-01."},
            self.PARAMS,
        )
        assert not result.passed and result.critical
        assert result.failure_kind == checks.FAILURE_INVENTED_VALUE

    def test_a_forbidden_literal_is_critical(self):
        params = dict(self.PARAMS, forbidden=["net 30"])
        result = checks.check_absent_source_unknown(
            _episode("absent_source_unknown", params, self.MATERIAL),
            {"text": "Payment terms are net 30."},
            params,
        )
        assert not result.passed and result.critical

    def test_silence_without_a_typed_unknown_is_a_soft_failure(self):
        result = checks.check_absent_source_unknown(
            _episode("absent_source_unknown", self.PARAMS, self.MATERIAL),
            {"text": "The rewrite covers invoicing and dunning."},
            self.PARAMS,
        )
        assert not result.passed and not result.critical
        assert result.failure_kind == checks.FAILURE_MISSING_UNKNOWN


class TestTypedUnknownField:
    PARAMS = {"field": "owner", "alternatives": ["Alex Moreau", "Alex Whitfield"]}
    MATERIAL = {"sources": [{"text": "Alex Moreau, platform engineer. Alex Whitfield, release manager."}]}

    def test_leaving_the_ambiguity_open_passes(self):
        result = checks.check_typed_unknown_field(
            _episode("typed_unknown_field", self.PARAMS, self.MATERIAL),
            {"text": "Two people are called Alex; the owner is unknown.", "fields": {"owner": None}},
            self.PARAMS,
        )
        assert result.passed

    def test_resolving_the_ambiguity_to_one_name_is_critical(self):
        result = checks.check_typed_unknown_field(
            _episode("typed_unknown_field", self.PARAMS, self.MATERIAL),
            {"text": "Alex Moreau owns the rehearsal."},
            self.PARAMS,
        )
        assert not result.passed and result.critical
        assert result.failure_kind == checks.FAILURE_INVENTED_UNCERTAIN

    def test_naming_both_candidates_is_not_a_resolution(self):
        result = checks.check_typed_unknown_field(
            _episode("typed_unknown_field", self.PARAMS, self.MATERIAL),
            {
                "text": "It is either Alex Moreau or Alex Whitfield; unknown which.",
                "fields": {"owner": {"unknown": "ambiguous"}},
            },
            self.PARAMS,
        )
        assert result.passed

    def test_an_allowed_value_is_not_an_invention(self):
        params = {"field": "decision_acceptance", "allowed_values": ["unreviewed", "disputed"]}
        good = checks.check_typed_unknown_field(
            _episode("typed_unknown_field", params),
            {"fields": {"decision_acceptance": "disputed"}},
            params,
        )
        bad = checks.check_typed_unknown_field(
            _episode("typed_unknown_field", params),
            {"fields": {"decision_acceptance": "accepted"}},
            params,
        )
        assert good.passed
        assert not bad.passed and bad.critical


class TestStaleDecisionSuperseded:
    PARAMS = {"decision_id": "DEC-11", "stale_keywords": ["mysql"], "current_decision_id": "DEC-19"}

    def test_a_decision_marked_superseded_passes(self):
        result = checks.check_stale_decision_superseded(
            _episode("stale_decision_superseded", self.PARAMS),
            {"decisions": [{"id": "DEC-11", "text": "Use MySQL", "state": "superseded"}]},
            self.PARAMS,
        )
        assert result.passed

    def test_restating_it_as_current_is_critical(self):
        result = checks.check_stale_decision_superseded(
            _episode("stale_decision_superseded", self.PARAMS),
            {"decisions": [{"id": "DEC-11", "text": "Use MySQL", "state": "accepted", "current": True}]},
            self.PARAMS,
        )
        assert not result.passed and result.critical
        assert result.failure_kind == checks.FAILURE_STALE_DECISION

    def test_prose_that_states_the_stale_decision_unmarked_is_critical(self):
        result = checks.check_stale_decision_superseded(
            _episode("stale_decision_superseded", self.PARAMS),
            {"text": "The target store is MySQL."},
            self.PARAMS,
        )
        assert not result.passed and result.critical

    def test_prose_that_marks_it_superseded_passes(self):
        result = checks.check_stale_decision_superseded(
            _episode("stale_decision_superseded", self.PARAMS),
            {"text": "The MySQL decision was superseded by DEC-19: PostgreSQL."},
            self.PARAMS,
        )
        assert result.passed

    def test_saying_nothing_at_all_is_a_soft_failure(self):
        result = checks.check_stale_decision_superseded(
            _episode("stale_decision_superseded", self.PARAMS),
            {"text": "Progress is steady."},
            self.PARAMS,
        )
        assert not result.passed and not result.critical
        assert result.failure_kind == checks.FAILURE_MISSING_SUPERSESSION


class TestCitationNotSupported:
    PARAMS = {"claim_id": "c1", "citation": "doc:runbook", "claim_keywords": ["risk"]}

    def _claim(self, support: str, record: dict | None = None) -> dict:
        return {
            "span_id": "c1", "text": "The cutover risk is low.", "refs": ["doc:runbook"],
            "kind": "inference", "support": support, "acceptance": "unreviewed",
            "support_record": record,
        }

    def test_a_source_linked_claim_passes(self):
        result = checks.check_citation_not_supported(
            _episode("citation_not_supported", self.PARAMS),
            {"claims": [self._claim("source_linked")]},
            self.PARAMS,
        )
        assert result.passed

    def test_marking_it_supported_is_critical(self):
        result = checks.check_citation_not_supported(
            _episode("citation_not_supported", self.PARAMS),
            {"claims": [self._claim("supported", {"method": "field_mapping"})]},
            self.PARAMS,
        )
        assert not result.passed and result.critical
        assert result.failure_kind == checks.FAILURE_CITATION_SUPPORTED

    def test_asserting_nothing_is_not_a_failure(self):
        result = checks.check_citation_not_supported(
            _episode("citation_not_supported", self.PARAMS),
            {"claims": []},
            self.PARAMS,
        )
        assert result.passed

    def test_require_claim_turns_absence_into_a_soft_failure(self):
        params = dict(self.PARAMS, require_claim=True)
        result = checks.check_citation_not_supported(
            _episode("citation_not_supported", params), {"claims": []}, params
        )
        assert not result.passed and not result.critical
        assert result.failure_kind == checks.FAILURE_CLAIM_MISSING

    def test_another_claim_on_the_same_source_is_not_judged(self):
        other = {
            "span_id": "c9", "text": "Run 114 is scheduled.", "refs": ["doc:runbook"],
            "support": "supported", "support_record": {"method": "field_mapping"},
        }
        result = checks.check_citation_not_supported(
            _episode("citation_not_supported", self.PARAMS),
            {"claims": [other]},
            self.PARAMS,
        )
        assert result.passed

    def test_the_episode_ref_is_translated_through_the_run_ref_map(self):
        claim = dict(self._claim("supported", {"method": "field_mapping"}), span_id="s0", refs=["item:pitem_x"])
        result = checks.check_citation_not_supported(
            _episode("citation_not_supported", self.PARAMS),
            {"claims": [claim], "ref_map": {"doc:runbook": "item:pitem_x"}},
            dict(self.PARAMS, claim_id=""),
        )
        assert not result.passed and result.critical


# ── Severity, reports and review effort ───────────────────────────────


class TestCriticalCannotBeAveraged:
    def test_severity_comes_from_the_checker_not_the_corpus(self):
        assert checks.FAILURE_INVENTED_VALUE in checks.CRITICAL_FAILURE_KINDS
        assert checks.FAILURE_QUESTION_REPEATED not in checks.CRITICAL_FAILURE_KINDS
        episode = _episode("absent_source_unknown", {"field": "deadline", "critical": False})
        result = checks.check_episode(episode, {"text": "It lands on 2026-08-01."})
        assert result.critical, "an episode file cannot downgrade an invented value"

    def test_one_critical_failure_fails_a_report_of_thirty_two_passes(self, corpus):
        good = {"text": "Nothing is recorded; it is unknown.", "fields": {}, "claims": []}
        outputs = {episode["id"]: dict(good) for episode in corpus}
        clean = build_report(
            episodes=corpus,
            outputs={
                episode["id"]: {
                    "text": "unknown",
                    "fields": {},
                    "claims": [],
                    "decisions": [],
                }
                for episode in corpus
            },
            route={"model": "canned"},
            engine="canned",
        )
        assert clean["totals"]["critical_failures"] == 0

        poisoned = dict(outputs)
        victim = next(
            episode for episode in corpus
            if any(inv["kind"] == "absent_source_unknown" for inv in episode["invariants"])
        )
        poisoned[victim["id"]] = {"text": "The deadline is 2031-01-01.", "fields": {}, "claims": []}
        report = build_report(episodes=corpus, outputs=poisoned, route={"model": "canned"}, engine="canned")

        assert report["totals"]["critical_failures"] >= 1
        assert report["critical_verdict"] == "fail"
        assert report["verdict"] == "fail"
        passed = report["totals"]["passed"]
        assert passed >= 1, "the point of the rule is that a majority passing does not help"
        assert victim["id"] in report["review_effort"]["critical_failures"]


class TestReportFields:
    def test_a_report_names_everything_a_gate_reads(self, corpus):
        outputs = {
            episode["id"]: {
                "text": "unknown",
                "claims": [{"span_id": "s0", "text": "x", "refs": ["r"], "support": "source_linked"}],
                "latency_ms": 12.5,
            }
            for episode in corpus
        }
        report = build_report(
            episodes=corpus,
            outputs=outputs,
            route={"model": "m", "plan_id": "irp_1", "boundary": "private_network", "host": "192.0.2.1"},
            engine="route",
        )
        for key in (
            "corpus_version", "engine", "model", "route", "build", "episodes",
            "totals", "failures_by_kind", "support_judgments", "latency_ms",
            "review_effort", "verdict", "critical_verdict", "judge", "aborted",
        ):
            assert key in report, key
        assert report["route"]["plan_id"] == "irp_1"
        assert report["route"]["boundary"] == "private_network"
        assert report["route"]["host"] == "192.0.2.1"
        assert report["support_judgments"] == {"source_linked": len(corpus)}
        assert report["latency_ms"]["median"] == 12.5
        assert report["judge"]["enabled"] is False
        assert report["episodes"][0]["material_sha256"]

    def test_review_effort_counts_criticals_and_held_out_episodes_once(self, corpus):
        results = [
            checks.check_episode(episode, {"text": "unknown", "fields": {}, "claims": []})
            for episode in corpus
        ]
        effort = checks.review_effort(results)
        held = [e["id"] for e in corpus if e["split"] == checks.SPLIT_HELD_OUT]
        assert set(held) <= set(effort["items_to_inspect"])
        assert effort["total"] == len(set(effort["critical_failures"]) | set(effort["held_out_episodes"]))

    def test_support_judgments_count_every_claim_axis(self):
        counts = checks.support_judgments([
            {"claims": [{"support": "supported"}, {"support": "source_linked"}]},
            {"claims": [{"support": "supported"}]},
        ])
        assert counts == {"source_linked": 1, "supported": 2}


class TestAbortIsLoud:
    """HS-200-08 follow-through: a run that dies still writes a named report.

    The CI runner's abort was invisible -- the driver wrote no report at all,
    so every assertion died on ``KeyError: 'totals'``. The report now always
    carries an ``aborted`` column, and a run that did not finish is never a
    pass.
    """

    def test_a_completed_run_reports_an_empty_abort_column(self, corpus):
        report = build_report(
            episodes=corpus[:1],
            outputs={corpus[0]["id"]: {"text": "unknown", "latency_ms": 1.0}},
            route={"model": "m"},
            engine="canned",
        )
        assert report["aborted"] == ""
        assert report["aborted_traceback"] == ""

    def test_an_abort_names_its_reason_and_can_never_be_a_pass(self, corpus):
        report = build_report(
            episodes=corpus[:1],
            outputs={},
            route={"model": "m"},
            engine="canned",
            aborted="PluginProviderFailure: plugin_provider_failed:requirements_extractor",
            aborted_traceback="Traceback (most recent call last): ...",
        )
        assert "PluginProviderFailure" in report["aborted"]
        assert report["aborted_traceback"]
        assert report["verdict"] == "fail", "an incomplete run is never a pass"
        assert "aborted" in phase200_eval.summarise(report)

    def test_the_driver_writes_a_report_when_the_hub_cannot_boot(self, tmp_path, monkeypatch):
        """The exact runner shape: nothing ran, and the report still lands."""
        from tests.fixtures.phase200 import collectors

        class _HubIsDead(BaseException):
            """A BaseException, like the kernel's own PluginProviderFailure."""

        def _refuse(**_kwargs):
            raise _HubIsDead("the evaluation hub could not boot")

        monkeypatch.setattr(collectors, "evaluation_hub", _refuse)

        report_path = tmp_path / "report.json"
        raw_path = tmp_path / "raw.json"
        code = phase200_eval.main([
            "run", "--engine", "canned",
            "--canned", str(checks.CORPUS_ROOT.parent / "canned" / "harness.json"),
            "--episode", "MX-01",
            "--report", str(report_path), "--raw", str(raw_path),
        ])

        assert code == 1, "an aborted run fails the command"
        assert report_path.exists(), "an abort must still write the report"
        assert raw_path.exists(), "an abort must still write the raw outputs"
        report = json.loads(report_path.read_text())
        assert "_HubIsDead" in report["aborted"], report["aborted"]
        assert report["aborted_traceback"]
        assert report["verdict"] == "fail"
        assert report["totals"]["episodes"] == 1, "the selection is still reported"

    def test_a_control_signal_is_never_recorded_as_a_trial(self, tmp_path, monkeypatch):
        """Ctrl-C is the operator speaking; it is not an evaluation result."""
        from tests.fixtures.phase200 import collectors

        def _interrupt(**_kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(collectors, "evaluation_hub", _interrupt)

        with pytest.raises(KeyboardInterrupt):
            phase200_eval.main([
                "run", "--engine", "canned",
                "--canned", str(checks.CORPUS_ROOT.parent / "canned" / "harness.json"),
                "--episode", "MX-01",
                "--report", str(tmp_path / "report.json"),
            ])
        assert not (tmp_path / "report.json").exists()


class TestCannedFixture:
    def test_the_committed_canned_outputs_parse(self):
        payload = json.loads((checks.CORPUS_ROOT.parent / "canned" / "harness.json").read_text())
        assert "default" in payload and isinstance(payload["episodes"], dict)
        known = {episode["id"] for episode in checks.load_corpus()}
        assert set(payload["episodes"]) <= known
