# HS-173-06 walk facts

Generated: 2026-09-05T14:01:48.742695
Hub: 127.0.0.1:55902

## steward-policy-api

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| project_name | (owner's project) | Complete del | DATA | real desk content |
| eligible_effect_kinds | (list, github_comment expected absent) | [] | DATA | from steward policy |
| github_comment_enabled | false | False | MATCH | github_comment absent as expected |

## room-health-api

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| health:review_wait | (absent when no data) | absent | DATA | signal not present in health payload |
| health:issue_aging:tone | (green/amber/red or absent) | green | DATA | from Room health payload |
| health:issue_aging:summary | (signal summary) | --- | DATA | from Room health payload |
| health:ci | (absent when no data) | absent | DATA | signal not present in health payload |
| health:release | (absent when no data) | absent | DATA | signal not present in health payload |
| health:assessment | (at_risk or on_track) | on_track | DATA | from Room health payload |

## room-health

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| health_section_present | (true when signals have data, false when no data) | True | DATA | HEALTH section on Room face |
| health_row:review_wait | (absent when no data for this signal) | absent | DATA | HEALTH row not rendered |
| health_row:issue_aging | (tone . primary . cells with data tokens) | tone=--- . ISSUE AGING . CLEAR | DATA | HEALTH row on Room face |
| health_row:ci | (absent when no data for this signal) | absent | DATA | HEALTH row not rendered |
| health_row:release | (absent when no data for this signal) | absent | DATA | HEALTH row not rendered |
| bottleneck_rows | (varies) | 0 | DATA | bottleneck rows in NEEDS YOU section |
| needs_you_rows | (varies) | 0 | DATA | generic NEEDS YOU rows in Room |
| nudge_verb_present | false (github_comment not eligible) | present=False (count=0) | DATA | Nudge verb on reviewer-bottleneck NEEDS YOU rows |
| health_section_present | (true when signals have data, false when no data) | True | DATA | HEALTH section on Room face |
| health_row:review_wait | (absent when no data for this signal) | absent | DATA | HEALTH row not rendered |
| health_row:issue_aging | (tone . primary . cells with data tokens) | tone=--- . ISSUE AGING . CLEAR | DATA | HEALTH row on Room face |
| health_row:ci | (absent when no data for this signal) | absent | DATA | HEALTH row not rendered |
| health_row:release | (absent when no data for this signal) | absent | DATA | HEALTH row not rendered |
| bottleneck_rows | (varies) | 0 | DATA | bottleneck rows in NEEDS YOU section |
| needs_you_rows | (varies) | 0 | DATA | generic NEEDS YOU rows in Room |
| nudge_verb_present | false (github_comment not eligible) | present=False (count=0) | DATA | Nudge verb on reviewer-bottleneck NEEDS YOU rows |

## update-editor

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| latest_update_status | (draft or published) | --- | DATA | latest update state |
| latest_update_generator | (deterministic or model label) | deterministic | DATA | who generated the update |
| generator_token | (deterministic or model label) | Deterministic | DATA | generator token on update face |
| claim_chip_count | (varies) | 0 | DATA | claim chips in update body |
| unverified_count | (varies, 0 for deterministic) | 0 | DATA | UNVERIFIED markers in update body |
| host_chip | (model host or absent for deterministic) | --- | DATA | EgressChip on update card |
| host_chip_present | (true when model, false when deterministic) | False | DATA | EgressChip presence |
| model_token | (model name when model-generated, empty for deterministic) |  | DATA | model name token in footer |
| latest_update_status | (draft or published) | --- | DATA | latest update state |
| latest_update_generator | (deterministic or model label) | deterministic | DATA | who generated the update |
| generator_token | (deterministic or model label) | Deterministic | DATA | generator token on update face |
| claim_chip_count | (varies) | 0 | DATA | claim chips in update body |
| unverified_count | (varies, 0 for deterministic) | 0 | DATA | UNVERIFIED markers in update body |
| host_chip | (model host or absent for deterministic) | --- | DATA | EgressChip on update card |
| host_chip_present | (true when model, false when deterministic) | False | DATA | EgressChip presence |
| model_token | (model name when model-generated, empty for deterministic) |  | DATA | model name token in footer |

## steward-posture

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| effects_row_count | (6 kinds including github_comment) | 6 | DATA | Effects CheckGadget rows in steward posture |
| effect_row:0 | (label . checked . egress chip if external) | Refreshed sources . checked=False . egress=None | DATA | effect kind row |
| effect_row:1 | (label . checked . egress chip if external) | Created proposals . checked=False . egress=None | DATA | effect kind row |
| effect_row:2 | (label . checked . egress chip if external) | Applied proposal effects . checked=False . egress=None | DATA | effect kind row |
| effect_row:3 | (label . checked . egress chip if external) | Drafted update . checked=False . egress=model | DATA | effect kind row |
| effect_row:4 | (label . checked . egress chip if external) | Door item created . checked=False . egress=None | DATA | effect kind row |
| effect_row:5 | (label . checked . egress chip if external) | Reviewer nudge . checked=False . egress=GITHUB.COM | DATA | effect kind row |
| per_nudge_approval | true | True | MATCH | PER-NUDGE APPROVAL token present |
| nudge_template_visible | (true when github_comment checked, false otherwise) | False | DATA | Nudge text row visibility |
| reviewer_nudge_checked | false (github_comment not enabled by default) | False | MATCH | Reviewer nudge CheckGadget state |
| reviewer_nudge_egress_chip | GITHUB.COM | GITHUB.COM | MATCH | EgressChip on Reviewer nudge row (Article III: egress where egress happens) |
| effects_row_count | (6 kinds including github_comment) | 6 | DATA | Effects CheckGadget rows in steward posture |
| effect_row:0 | (label . checked . egress chip if external) | Refreshed sources . checked=False . egress=None | DATA | effect kind row |
| effect_row:1 | (label . checked . egress chip if external) | Created proposals . checked=False . egress=None | DATA | effect kind row |
| effect_row:2 | (label . checked . egress chip if external) | Applied proposal effects . checked=False . egress=None | DATA | effect kind row |
| effect_row:3 | (label . checked . egress chip if external) | Drafted update . checked=False . egress=model | DATA | effect kind row |
| effect_row:4 | (label . checked . egress chip if external) | Door item created . checked=False . egress=None | DATA | effect kind row |
| effect_row:5 | (label . checked . egress chip if external) | Reviewer nudge . checked=False . egress=GITHUB.COM | DATA | effect kind row |
| per_nudge_approval | true | True | MATCH | PER-NUDGE APPROVAL token present |
| nudge_template_visible | (true when github_comment checked, false otherwise) | False | DATA | Nudge text row visibility |
| reviewer_nudge_checked | false (github_comment not enabled by default) | False | MATCH | Reviewer nudge CheckGadget state |
| reviewer_nudge_egress_chip | GITHUB.COM | GITHUB.COM | MATCH | EgressChip on Reviewer nudge row (Article III: egress where egress happens) |

## Shots

- room-health @ 1440: `walk-room-health-1440.png`
- update-editor @ 1440: `walk-update-1440.png`
- steward-posture @ 1440: `walk-steward-policy-1440.png`
- room-health @ 393: `walk-room-health-393.png`
- update-editor @ 393: `walk-update-393.png`
- steward-posture @ 393: `walk-steward-policy-393.png`

## Defects

None.

