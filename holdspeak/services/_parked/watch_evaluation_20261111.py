# PARKED: one evaluation core now commits success bookkeeping for manual and scheduled reads.
from __future__ import annotations

from typing import Any
from holdspeak.services.watch_service import WATCH_SWEEP_MAX

class _ParkedBody:
    def _mark_read(self, watch_id: str) -> None:
        """A read that found nothing new still counts as a successful check."""
        try:
            with self._db._connection() as conn:
                conn.execute(
                    "UPDATE connector_watches SET last_success_at=datetime('now'), "
                    "last_error=NULL WHERE id=?",
                    (watch_id,),
                )
        except Exception:  # pragma: no cover - bookkeeping only
            pass

    def _evaluate_core(
        self,
        principal: Principal,
        watch_id: str,
        *,
        trigger_kind: str = "manual",
        now_iso: str | None = None,
        txn_hook: Any | None = None,
    ) -> dict[str, Any]:
        """Shared evaluation core: snapshot -> diff -> evaluation -> observations.

        Callers:
        - evaluate_once (manual, trigger_kind="manual", no txn_hook)
        - evaluate_due  (scheduled, trigger_kind="scheduled", txn_hook
          writes bookkeeping + circuit reset in the same transaction)

        txn_hook: if provided, called as txn_hook(conn, watch_id, now_iso)
        inside the write transaction after baseline advance.

        Idempotent: UNIQUE(watch_id, watch_revision, source_revision)
        ensures the same source revision evaluates once.
        """
        from holdspeak.project_contracts import generate_pobs_id
        from holdspeak.refs import format as format_ref

        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)

        connector_id = watch.get("connector_id", "")
        watch_revision = int(watch.get("revision") or 0)
        now = now_iso or datetime.now(timezone.utc).isoformat(timespec="seconds")

        # 1. Fetch fresh snapshot via the admitted adapter path.
        # PHILO-17 evalerror: a read that fails records its cause on the
        # watch, as `baseline_watch` does, for the owner's Evaluate and the
        # scheduled sweep alike (both come through here). Needs you and the
        # Room's source row read `last_error`; a success clears it (5d,
        # `_mark_read`, `record_refresh`).
        try:
            entities = self._fetch(principal, watch)
            # HS-167-02: drain provider metadata (calls count) set by the
            # snapshot adapter's thread-local before any other code runs.
            from holdspeak.services.watch_sources import drain_fetch_meta
            fetch_meta = drain_fetch_meta()
            snapshot = normalize_snapshot(connector_id, entities)
        except Exception as exc:
            self._repo.record_refresh_error(watch_id, str(exc))
            raise

        # 1b. HS-200-43 F1: THE FIRST EVALUATION OF AN EMPTY BASELINE IS
        # SILENT.  `diff_snapshots` emits a discovered event for every
        # entity absent from the baseline, and the baseline it reads is
        # `watch["snapshot"]` -- `baseline_state` is never consulted by
        # evaluation.  So a watch whose snapshot is empty or NULL (the
        # Door/Interview shape when `baseline_watch` raised, every legacy
        # row promoted by `_backfill_watch_graduation`, and every
        # `ensure_meeting_watch` row -- which NO caller ever baselines)
        # would discover its whole source as new the first time it ran:
        # counsel measured 30 entities -> 30 transitions, 30 observations,
        # 1 effect.  Delaying that evaluation does not prevent it.
        #
        # Instead the first run ESTABLISHES the baseline and reports
        # nothing: zero transitions, zero observations, zero effects, no
        # evaluation row.  Bookkeeping still advances through the caller's
        # txn_hook, so the watch comes due again on its normal cadence and
        # the SECOND run is a real diff against a real baseline.
        if not (watch.get("snapshot") or {}):
            self._persist_baseline(watch_id, snapshot)
            if txn_hook is not None:
                # The scheduler's bookkeeping (last_evaluated_at,
                # next_evaluation_at, circuit reset) must advance even
                # though no evaluation row exists -- otherwise the watch
                # stays due forever and re-baselines every sweep.
                with self._db._connection() as conn:
                    txn_hook(conn, watch_id, now)
            return {
                "watch_id": watch_id,
                "evaluation_id": "",
                "state": "baselined",
                "transitions": 0,
                "observation_ids": [],
                "message": (
                    f"Baseline established from {len(snapshot['entities'])} "
                    "entities; the first evaluation is silent"
                ),
                "_transitions": [],
            }

        # 2. Compute source_revision (deterministic hash of snapshot).
        snapshot_json_str = json.dumps(
            snapshot, sort_keys=True, separators=(",", ":"),
        )
        source_revision = hashlib.sha256(
            snapshot_json_str.encode("utf-8"),
        ).hexdigest()[:32]

        # 3. Idempotency: same (watch_id, watch_revision, source_revision)?
        existing = self._repo.find_evaluation_by_source(
            watch_id, watch_revision, source_revision,
        )
        if existing is not None:
            # PHILO-15 B61: the source WAS read, and said nothing new: that
            # is a successful check (the row is fresh, not STALE).
            self._mark_read(watch_id)
            return {
                "watch_id": watch_id,
                "evaluation_id": existing["id"],
                "state": "no_op",
                "transitions": 0,
                "observation_ids": [],
                "message": "Identical snapshot already evaluated",
            }

        # 4. Diff against the stored baseline.
        baseline = watch.get("snapshot") or {}
        transitions = diff_snapshots(
            connector_id, baseline, snapshot, query_kind=str(watch.get("query_kind") or ""),
            # An Automation's watch names the event a newly seen entity is
            # (a PR that enters "review requested of me" is a review request).
            discovery_event=str((watch.get("query") or {}).get("discovery_event") or ""),
        )

        # 5. Persist: evaluation + observations + baseline in one txn.
        evaluation_id = f"weval_{uuid.uuid4().hex[:12]}"
        observation_ids: list[str] = []

        project_id = watch.get("project_id") or ""
        source_key = ""
        if project_id:
            sources = self._repo.list_project_sources(project_id)
            for s in sources:
                if s.get("source_ref") == f"watch:{watch_id}":
                    source_key = s.get("id", "")
                    break
        if not source_key:
            source_key = f"watch:{watch_id}"

        try:
            with self._db._connection() as conn:
                # 5a. Evaluation row.
                # HS-167-02: persist provider metadata (calls count)
                # on the evaluation for the OBSERVE receipt to read.
                meta_str = json.dumps(fetch_meta) if fetch_meta else "{}"
                self._repo.create_evaluation_in_transaction(
                    conn,
                    evaluation_id=evaluation_id,
                    watch_id=watch_id,
                    watch_revision=watch_revision,
                    source_revision=source_revision,
                    trigger_kind=trigger_kind,
                    state="completed",
                    started_at=now,
                    completed_at=now,
                    metadata_json=meta_str,
                )

                # 5b. Observations for each transition (160 collector
                #     discipline: deterministic pobs_ IDs, watch.transition
                #     kind, canonical subject refs).
                if project_id and transitions:
                    for event in transitions:
                        entity_ref = event.get("entity_ref", "")
                        event_type = event.get("event_type", "")
                        facts = event.get("facts", {})
                        fact = {
                            "event_type": event_type,
                            "entity_ref": entity_ref,
                            "changed": facts.get("changed", {}),
                        }
                        # Conductor K4: name the entity, so the weekly
                        # update can say what closed (a PR title, a URL).
                        if facts.get("entity_title"):
                            fact["entity_title"] = str(facts["entity_title"])
                        if facts.get("url"):
                            fact["url"] = str(facts["url"])
                        fact_str = json.dumps(
                            fact, sort_keys=True, separators=(",", ":"),
                        )
                        content_hash = hashlib.sha256(
                            fact_str.encode("utf-8"),
                        ).hexdigest()[:32]

                        obs_id = generate_pobs_id(
                            adapter="watch",
                            source_id=source_key,
                            source_version=event.get("source_revision", ""),
                            fact_key=content_hash,
                        )

                        was_inserted = (
                            self._db.project_observations
                            .insert_observation_in_transaction(
                                conn,
                                observation_id=obs_id,
                                project_id=project_id,
                                source_id=source_key,
                                observation_kind="watch.transition",
                                subject_ref=format_ref("watch", watch_id),
                                source_version=event.get(
                                    "source_revision", "",
                                ),
                                observed_at=now,
                                fact_json=fact_str,
                                content_hash=content_hash,
                            )
                        )
                        if was_inserted:
                            observation_ids.append(obs_id)

                # 5c. Update evaluation with observation IDs.
                if observation_ids:
                    conn.execute(
                        "UPDATE watch_evaluations "
                        "SET observation_ids_json=? WHERE id=?",
                        (
                            json.dumps(
                                observation_ids, separators=(",", ":"),
                            ),
                            evaluation_id,
                        ),
                    )

                # 5d. Advance baseline (same snapshot write as
                #     record_refresh but inside the caller's transaction).
                conn.execute(
                    "UPDATE connector_watches "
                    "SET snapshot_json=?, last_success_at=datetime('now'), "
                    "last_error=NULL, updated_at=datetime('now') "
                    "WHERE id=?",
                    (snapshot_json_str, watch_id),
                )

                # 5e. Caller-supplied transactional hook (evaluate_due
                #     writes bookkeeping + circuit here).
                if txn_hook is not None:
                    txn_hook(conn, watch_id, now)

        except sqlite3.IntegrityError:
            # S-3 counsel: TOCTOU on the UNIQUE(watch_id, watch_revision,
            # source_revision) constraint.  find_evaluation_by_source ran
            # outside the write transaction; a concurrent evaluation
            # inserted the row first.  Return the typed no_op result
            # exactly as if the idempotency check had caught it.
            existing = self._repo.find_evaluation_by_source(
                watch_id, watch_revision, source_revision,
            )
            if existing is not None:
                return {
                    "watch_id": watch_id,
                    "evaluation_id": existing["id"],
                    "state": "no_op",
                    "transitions": 0,
                    "observation_ids": [],
                    "message": "Identical snapshot already evaluated (concurrent)",
                }
            # If somehow the row still doesn't exist, re-raise.
            raise

        return {
            "watch_id": watch_id,
            "evaluation_id": evaluation_id,
            "state": "completed",
            "transitions": len(transitions),
            "observation_ids": observation_ids,
            "message": (
                f"Evaluation complete: {len(transitions)} transitions, "
                f"{len(observation_ids)} observations"
            ),
            # Internal: raw transition dicts for rule matching (HS-164-03).
            # Consumed by evaluate_due only; never serialised to the caller.
            "_transitions": transitions,
        }

    def evaluate_once(
        self,
        principal: Principal,
        watch_id: str,
        graduated_only: bool = False,
    ) -> dict[str, Any]:
        """Manual evaluation: snapshot -> diff -> transitions -> observations.

        MANUAL only (P5 owns scheduling).  Fetches a fresh snapshot,
        diffs it against the stored baseline via diff_snapshots (which
        already speaks GitHub PR semantics: review/checks/head/state/
        merge), persists a watch_evaluations row, emits watch.transition
        observations via the 160 collector discipline (deterministic
        pobs_ IDs, evidence links, the project binding as source), and
        advances the baseline.

        Idempotent: UNIQUE(watch_id, watch_revision, source_revision)
        ensures the same source revision evaluates once.  Repeated
        identical snapshots produce zero new observations (WAT-006's
        spirit at the read level).

        Manual evaluation IGNORES circuit state: the owner's hand
        overrides.  A successful manual evaluation closes the circuit
        (streak reset, circuit closed) via the post-txn update.
        Only the scheduler (evaluate_due) respects the circuit.

        HS-200-43: a manual evaluation now RECORDS ITS EFFECTS, exactly
        as a scheduled one does, and returns them under the existing
        ``effects`` key.  Before this the owner's own hand could evaluate
        a watch all day and the steward would never see a thing.
        """
        self._graduated(watch_id, graduated_only)
        self._owner(principal)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        result = self._evaluate_core(
            principal, watch_id,
            trigger_kind="manual",
            now_iso=now,
        )

        # 5f. Graduated columns (non-critical; outside the txn).
        # Byte-identical to the pre-extraction behavior.
        if result["state"] == "completed":
            self._repo.update_watch_spec(
                watch_id,
                baseline_state="established",
                last_evaluated_at=now,
            )
            # Counsel M-1: the docstring's promise made real -- a
            # successful manual evaluation closes the circuit.
            self._repo.update_watch_circuit(
                watch_id,
                circuit_state="closed",
                circuit_failure_streak=0,
                circuit_opened_at=None,
            )

        # HS-200-43 P2-g: a manual evaluation that established a
        # baseline still RAN. `_persist_baseline` set baseline_state;
        # last_evaluated_at is this seam's to write, or the face shows a
        # watch the owner just evaluated as never evaluated.
        if result["state"] == "baselined":
            self._repo.update_watch_spec(watch_id, last_evaluated_at=now)

        # HS-200-43: the same guard the scheduler runs. Idempotent by
        # idempotency_key, so a scheduled pass over the same evaluation
        # mints nothing new.
        matched_effects = self._record_effects_if_any(result, watch_id)

        # `_transitions` is the internal raw-transition channel between
        # _evaluate_core and the effect recorder. `_evaluate_core`'s
        # docstring has always said it is never serialised to the caller;
        # it leaked out of evaluate_once until HS-200-43. Strip it here,
        # at the one public seam, rather than in _evaluate_core -- the
        # scheduler still needs it on the way past.
        payload = {k: v for k, v in result.items() if k != "_transitions"}
        if matched_effects:
            payload["effects"] = matched_effects
        return payload

    def evaluate_due(
        self,
        principal: Principal,
        *,
        limit: int | None = WATCH_SWEEP_MAX,
        admit: Any = None,
    ) -> list[dict[str, Any]]:
        """Evaluate graduated watches that are due based on their cadence.

        PHILO-9-02 (the steward beat, section 4: "watch evaluation keeps its
        own admission"): ``admit(watch_id, evaluate)`` -- given by the owner's
        admitted trigger -- runs each watch's evaluation as its own admitted
        ``project.watch.evaluate`` child with its leaf receipt.

        Per-watch isolation: one failure isolates, the outcome is
        recorded, and the loop continues.  NEVER raises.

        The durable circuit (HS-164-01 columns): N consecutive failures
        open it for that watch (CIRCUIT_FAILURE_THRESHOLD); evaluation
        is refused with an honest ``skipped_circuit_open`` outcome while
        the cooldown window has not elapsed.  After the window, ONE
        half-open probe is allowed through: success closes the circuit
        (streak=0); failure re-opens with a fresh opened_at.

        Boundary rule: evaluate_due owns graduated watches (state IN
        ('active','tested')) with a real next_evaluation_at column.
        A legacy watch (state='') has no scheduler since the watch fold
        (2026-11-08; ReactionService is parked). Never two schedulers on
        one row.

        Manual evaluate_once on a circuit-open watch: the OWNER's hand
        overrides — manual evaluation still runs (and its success closes
        the circuit).  Only THIS scheduler respects the circuit.

        HS-200-43 F2: BOUNDED. At most ``limit`` watches are evaluated per
        call, oldest-due first (`list_due_watches` orders by
        `next_evaluation_at ASC`).  Each watch can cost a serial
        `gh`/`acli` subprocess with a 5-10s timeout, and this runs on the
        heartbeat thread with the calendar refresh and the sweep receipt
        queued behind it.  The watches left over are not dropped -- they
        stay due and the next sweep takes them, oldest first, so no watch
        can starve.  ``self.last_sweep_deferred`` carries how many were
        left for the caller's receipt.

        The bound is for the UNATTENDED sweep only.  The owner's
        explicit triggers pass ``limit=None`` and evaluate everything --
        he is standing there watching it happen:
        `POST /api/steward/trigger` (`web/routes/steward.py`), the MCP
        `project.steward.trigger` tool, `Run now` on the Rhythm row
        (`web/routes/system/settings.py` -> `run_sweep(watch_limit=None)`)
        and the MCP `heartbeat.run_now` tool.  Only
        `runtime/heartbeat.py`'s scheduled loop takes the default.
        """
        self._owner(principal)
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat(timespec="seconds")

        outcomes: list[dict[str, Any]] = []
        due_watches = self._repo.list_due_watches(now_iso)

        # Oldest-due first is the repo query's ORDER BY; the slice is the
        # bound. `last_sweep_deferred` is an attribute rather than part of
        # the return value because `evaluate_due`'s list contract is read
        # by the steward route, the MCP trigger tool and two e2e rigs.
        self.last_sweep_deferred = 0
        if limit is not None and len(due_watches) > int(limit):
            self.last_sweep_deferred = len(due_watches) - int(limit)
            due_watches = due_watches[: int(limit)]

        for watch in due_watches:
            watch_id = watch["id"]
            try:
                # ── Circuit gate ───────────────────────────────────
                circuit_state = watch.get("circuit_state", "closed")
                circuit_streak = int(watch.get("circuit_failure_streak", 0))
                circuit_opened_at = watch.get("circuit_opened_at")
                is_probe = False

                if circuit_state in ("open", "half_open"):
                    if circuit_opened_at:
                        opened = datetime.fromisoformat(circuit_opened_at)
                        if opened.tzinfo is None:
                            opened = opened.replace(tzinfo=timezone.utc)
                        elapsed = (now - opened).total_seconds()
                        if elapsed < CIRCUIT_COOLDOWN_SECONDS:
                            # Still in cooldown — skip with honest outcome.
                            outcomes.append({
                                "watch_id": watch_id,
                                "outcome": "skipped_circuit_open",
                                "circuit_state": circuit_state,
                                "circuit_failure_streak": circuit_streak,
                            })
                            continue
                    # Cooldown elapsed: allow ONE half-open probe.
                    is_probe = True

                # ── Bookkeeping txn hook ───────────────────────────
                cadence = max(1, int(watch.get("evaluation_cadence_minutes", 60)))
                next_eval_iso = (
                    now + timedelta(minutes=cadence)
                ).isoformat(timespec="seconds")

                def _make_txn_hook(wid, next_iso, repo):
                    """Factory: capture per-watch values for the closure."""
                    def hook(conn, _wid, eval_now):
                        # Bookkeeping: advance timestamps transactionally.
                        conn.execute(
                            "UPDATE connector_watches "
                            "SET last_evaluated_at=?, next_evaluation_at=?, "
                            "    baseline_state='established' "
                            "WHERE id=?",
                            (eval_now, next_iso, wid),
                        )
                        # Circuit: success resets.
                        repo.update_watch_circuit_in_transaction(
                            conn, wid,
                            circuit_state="closed",
                            circuit_failure_streak=0,
                            circuit_opened_at=None,
                        )
                    return hook

                txn_hook = _make_txn_hook(
                    watch_id, next_eval_iso, self._repo,
                )

                def _evaluate(watch_id: str = watch_id, txn_hook: Any = txn_hook) -> tuple[Any, Any]:
                    result = self._evaluate_core(
                        principal, watch_id,
                        trigger_kind="scheduled",
                        now_iso=now_iso,
                        txn_hook=txn_hook,
                    )
                    # ── HS-164-03: rule matching + effect recording ───
                    # HS-200-43: through the shared guard, so a manual
                    # evaluation mints the identical effects.
                    return result, self._record_effects_if_any(result, watch_id)

                result, matched_effects = (_evaluate() if admit is None
                                           else admit(watch_id, _evaluate))

                outcome_type = "probe_half_open" if is_probe else "evaluated"
                # Idempotent no_op is still a successful evaluation
                # (same snapshot already seen).
                if result["state"] == "no_op":
                    outcome_type = "evaluated"
                # HS-200-43 F1: an empty baseline was filled in silently.
                # Named honestly rather than reported as an evaluation --
                # nothing was diffed and nothing was observed.
                if result["state"] == "baselined":
                    outcome_type = "baselined"

                outcome_entry: dict[str, Any] = {
                    "watch_id": watch_id,
                    "outcome": outcome_type,
                    "evaluation_id": result.get("evaluation_id"),
                    "transitions": result.get("transitions", 0),
                    "observation_ids": result.get("observation_ids", []),
                }
                if matched_effects:
                    outcome_entry["effects"] = matched_effects
                outcomes.append(outcome_entry)

            except Exception as exc:
                # M-1: drain stale thread-local fetch metadata so a
                # failed Jira fetch never leaks calls into the next
                # watch's evaluation on the same thread.
                from holdspeak.services.watch_sources import drain_fetch_meta as _drain
                _drain()
                # Per-watch isolation: record failure, update circuit,
                # advance bookkeeping, continue.
                try:
                    cadence = max(1, int(
                        watch.get("evaluation_cadence_minutes", 60),
                    ))
                    next_eval_iso = (
                        now + timedelta(minutes=cadence)
                    ).isoformat(timespec="seconds")
                    new_streak = circuit_streak + 1

                    if new_streak >= CIRCUIT_FAILURE_THRESHOLD:
                        new_circuit_state = "open"
                        new_opened_at = now_iso
                    else:
                        new_circuit_state = watch.get(
                            "circuit_state", "closed",
                        )
                        new_opened_at = watch.get("circuit_opened_at")

                    # Write bookkeeping + circuit in one transaction.
                    with self._db._connection() as conn:
                        conn.execute(
                            "UPDATE connector_watches "
                            "SET last_evaluated_at=?, next_evaluation_at=? "
                            "WHERE id=?",
                            (now_iso, next_eval_iso, watch_id),
                        )
                        self._repo.update_watch_circuit_in_transaction(
                            conn, watch_id,
                            circuit_state=new_circuit_state,
                            circuit_failure_streak=new_streak,
                            circuit_opened_at=new_opened_at,
                        )

                        # HS-164-04: emit steward.intervention_required
                        # in-transaction on circuit-open TRANSITION.
                        if (
                            new_circuit_state == "open"
                            and circuit_state != "open"
                        ):
                            try:
                                project_id = watch.get(
                                    "project_id",
                                    watch.get("bound_project_id", ""),
                                )
                                self._ledger.append_in_transaction(
                                    conn,
                                    principal,
                                    event_type="steward.intervention_required",
                                    producer="WatchService",
                                    subject_ref=f"watch:{watch_id}",
                                    source_revision="",
                                    facts={
                                        "reason": "circuit_open",
                                        "watch_id": watch_id,
                                        "project_id": project_id,
                                        "failure_streak": new_streak,
                                    },
                                    refs=[
                                        f"watch:{watch_id}",
                                        f"project:{project_id}",
                                    ],
                                )
                            except Exception:
                                pass  # Event must never break circuit write.
                except Exception:
                    pass  # Double-fault: even failure recording failed.

                outcomes.append({
                    "watch_id": watch_id,
                    "outcome": "failed",
                    "error": str(exc),
                })

        return outcomes
