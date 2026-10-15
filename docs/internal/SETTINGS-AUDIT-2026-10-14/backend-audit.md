# Settings backend audit and repair

Status: implemented and focused checks pass; hold for SHIP. No staging or
commit. Base: `eef72f987` (#1203). Worktree:
`/Users/karol/dev/tools/wt-settings-audit-20261014`.

The backend now preserves calendar identity and the whole source list on an
ordinary preference save. Accepted writes return the same migrated settings
projection as GET. Rhythm, Telegram preferences and Device name now persist.
These changes address Tenets 2 and 3 (first use and acceleration); the face
lane owns plain error words and canonical calendar type/name presentation.

## Causes and repair

1. **Calendar settings were lost on a successful full-document save.**
   `redacted_settings` adds the compatibility `calendar.subscription` alias
   (`holdspeak/services/settings_service.py:141`). The old writer gave that
   alias priority over `calendar.sources`, rebuilt one source with no label
   and `enabled=True`, and discarded the other sources. The red regression
   observed disabled native Work become unnamed and enabled, with Team lost.
   The writer now selects the legacy translation only when the incoming
   calendar patch explicitly contains subscription and omits sources
   (`holdspeak/services/settings_service.py:942`). Canonical sources win an
   echoed alias. A real subscription-only caller can replace or clear its
   source; unrelated partial edits retain all source values. Tests start at
   `tests/integration/test_calendar_settings.py:294`.

2. **Ordinary preferences could hit retired model-selector refusal.**
   GET stripped selectors only after family migration markers. The Thought
   write guard already refused them when an effective assignment existed
   before its marker. Successful PUT also returned raw `redacted_settings`,
   reintroducing retired selectors as the next full-document save base.
   GET and PUT now both use `_project_settings`
   (`holdspeak/services/settings_service.py:243`, `:1077`), with the same
   Thought assignment authority as the write guard. Meeting and Rails retain
   their own family marker gates; no unrelated default-family cutover is
   inferred. Explicit writes to retired selectors still return 400 and do
   not alter the retained Config bytes or assignments. Real assignment and
   migration-marker producers seed the regression at
   `tests/integration/test_desk_settings.py:391`.

3. **Rhythm, Telegram preferences and Device name returned success without
   saving.** The patch was merged, but `replace(current, ...)` omitted
   cadence, cadence_telegram and mesh. The writer now constructs the existing
   Config dataclasses and includes them in the accepted replacement
   (`holdspeak/services/settings_service.py:1023`). Existing secret bytes are
   preserved and remain redacted. The hub regression is at
   `tests/integration/test_desk_settings.py:467`.

4. **Explicit native-calendar reselection could not restore an erased name.**
   `calendar_use` returned immediately for an existing URL. It now repairs
   only a blank existing native label using the title found by that explicit
   action's existing EventKit lookup
   (`holdspeak/services/onboarding_service.py:300`). It preserves the saved
   ID, URL, enabled state, other sources and nonempty custom labels; the
   client-supplied stale label cannot override the detected title. Detection
   alone still performs no write. The regression starts at
   `tests/unit/test_onboarding_backends.py:203`.

## Focused proof

All commands ran through `.tmp/settings-audit/locked.py`, with an isolated
HOME, machine-state isolation switches and the shared test lock. No product
server, browser, calendar reader, mic, network or owner DB inspection ran.

Collection command:

```
python3 .tmp/settings-audit/locked.py backend-collect .venv/bin/python -m pytest --collect-only -q tests/integration/test_calendar_settings.py tests/integration/test_desk_settings.py
```

Collection output includes the new cases:

```
test_full_document_preference_save_preserves_named_disabled_native_and_other_calendars
test_canonical_calendar_sources_win_an_echoed_subscription_alias[sources0]
test_canonical_calendar_sources_win_an_echoed_subscription_alias[sources1]
test_legacy_subscription_only_can_replace_and_clear_canonical_sources
test_unrelated_partial_preference_save_preserves_every_calendar_source_byte
test_successive_ordinary_settings_saves_keep_retired_selectors_out[assignment-before-marker]
test_successive_ordinary_settings_saves_keep_retired_selectors_out[family-markers]
test_rhythm_telegram_and_device_name_settings_persist_without_changing_secrets
30 tests collected in 4.93s
```

Before product edits, the new regression subset produced:

```
7 failed, 1 passed in 3.93s
```

Full approved two-file command after the repair:

```
python3 .tmp/settings-audit/locked.py backend-green .venv/bin/python -m pytest -q -n8 --dist worksteal tests/integration/test_calendar_settings.py tests/integration/test_desk_settings.py
..............................                                           [100%]
30 passed in 4.98s
```

Exact logs: `.tmp/settings-audit/backend-collect.log`, `backend-red.log`,
`backend-green.log`. No corrective rerun was needed.

The bounded native reselect addition then collected and ran only
`tests/unit/test_onboarding_backends.py -k calendar`, through the same helper:

```
test_use_it_adds_the_macos_calendar_through_settings_once
test_use_it_on_a_macos_calendar_needs_the_permission
test_native_calendar_reselection_repairs_only_a_blank_name_without_changing_sources[repair-blank]
test_native_calendar_reselection_repairs_only_a_blank_name_without_changing_sources[keep-custom]
4/24 tests collected (20 deselected) in 0.20s
```

Before the onboarding product edit: `1 failed, 3 passed in 2.01s` (blank name
stayed blank). After the edit: `4 passed in 1.74s`. Exact helper logs are
`backend-calendar-reselect-collect.log`, `backend-calendar-reselect-red.log`,
`backend-calendar-reselect-green.log` under `.tmp/settings-audit/`.

## Limits and remaining observations

- Already erased calendar labels and already dropped sources cannot be
  reconstructed from the damaged Config alone. Explicit native reselection
  can now restore a blank label from its actual calendar title. No owner
  state was read or changed by this lane.
- `calendar_sources.py:132` derives success from a past event's last_seen,
  rather than a successful feed read. Empty successful feeds remain idle;
  later read failure can retain success. This requires a separate honest
  per-source refresh fact; no new framework was added here.
- Satellite `MeetingsConfig` remains a full-document writer. The backend
  round trip is now safe, but it still has separate debounce/conflict behavior.
  Frontend writer changes belong to the face audit, not this backend lane.
- The existing reconfiguration callback logs failures while retaining the
  accepted config (`holdspeak/services/settings_service.py:1066`). The tests
  prove saved settings and transport projections, not live runtime restart or
  OS behavior. Root owns the combined quick check and desk captures.

Tuesday: at the saved-config and API boundary, the owner can now change an
ordinary preference without losing calendar identity or receiving a model
migration error on the next edit. Live face and runtime closure are unverified
by this backend lane.
