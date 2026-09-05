# HS-174-11 walk facts

Generated: 2026-09-05T15:51:34.404746
Hub: 127.0.0.1:64020

## remote-api

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| remote_enabled | (OFF is the expected default) | OFF | DATA | Streamable HTTP transport state |
| active_count | (varies) | 0 | DATA | active credential count |
| total_count | (varies) | 0 | DATA | total credential count |
| probe_exists | false | False | MATCH | walk-174-probe credential pre-existing check |
| hub_host | (THIS DEVICE or hostname) | THIS DEVICE | DATA | hub host identity |
| hub_mesh | (bool) | MESH OFF | DATA | mesh state from hub |

## credential-probe

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| probe_skipped | (skip when remote OFF or probe exists) | credential probe: remote OFF | DATA | write guard denied the credential probe |
| remote_state | OFF (expected default) | REMOTE OFF | MATCH | remote listener is OFF; zero writes is the expected outcome |

## settings-system

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| hub_row_remote_cell | REMOTE OFF | REMOTE OFF | DATA | REMOTE cell on the hub row |
| streamable_http_state | OFF | OFF | DATA | Streamable HTTP toggle row |
| credential_count_token | (absent at zero, N CREDENTIALS when >0) | --- | DATA | credentials count token |
| active_count_token | (absent at zero, N ACTIVE when >0) | --- | DATA | active credentials count |
| issue_credential_absent_when_off | true (absent when OFF) | True | MATCH | Issue credential button should be absent when remote is OFF |
| hub_row_remote_cell | REMOTE OFF | REMOTE OFF | DATA | REMOTE cell on the hub row |
| streamable_http_state | OFF | OFF | DATA | Streamable HTTP toggle row |
| credential_count_token | (absent at zero, N CREDENTIALS when >0) | --- | DATA | credentials count token |
| active_count_token | (absent at zero, N ACTIVE when >0) | --- | DATA | active credentials count |
| issue_credential_absent_when_off | true (absent when OFF) | True | MATCH | Issue credential button should be absent when remote is OFF |

## shade-receipts

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| finished_rows | (varies) | 4 | DATA | Finished rows in the shade |
| remote_chips_in_finished | (none expected -- no overnight run yet) | [] | DATA | REMOTE . <ip> badges in Finished rows |
| chip_with_time_inside | false (no chip should carry a time inside) | False | MATCH | defect check: chip carrying a time |
| finished_rows | (varies) | 4 | DATA | Finished rows in the shade |
| remote_chips_in_finished | (none expected -- no overnight run yet) | [] | DATA | REMOTE . <ip> badges in Finished rows |
| chip_with_time_inside | false (no chip should carry a time inside) | False | MATCH | defect check: chip carrying a time |

## rhythm

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| runs_on_value | THIS DEVICE | THIS DEVICE | MATCH | Runs on host (expected THIS DEVICE on the owner's desk) |
| run_now_count | 1 (once, on the sweep row) | 1 | MATCH | Run now verb count (counsel C3: one verb, once) |
| awake_caption_present | false (caption absent when local) | False | MATCH | WHILE THIS MAC IS AWAKE caption (absent when Runs on = THIS DEVICE) |
| runs_on_value | THIS DEVICE | THIS DEVICE | MATCH | Runs on host (expected THIS DEVICE on the owner's desk) |
| run_now_count | 1 (once, on the sweep row) | 1 | MATCH | Run now verb count (counsel C3: one verb, once) |
| awake_caption_present | false (caption absent when local) | False | MATCH | WHILE THIS MAC IS AWAKE caption (absent when Runs on = THIS DEVICE) |

## door

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| confluence_row_state | (NOT INSTALLED / SIGN IN / SIGNED IN AS) | CConfluence○NOT SET UPConnect | DATA | Confluence source row connection state |
| confluence_defaults | ['RECENT BLOGS', 'PAGES BY ID'] | [] | DATA | Confluence default watch labels |
| github_row_present | true (provider listed in connections) | True | MATCH | github row presence (provider in connections API) |
| jira_row_present | true (provider listed in connections) | True | MATCH | jira row presence (provider in connections API) |
| confluence_row_present | true (provider listed in connections) | True | MATCH | confluence row presence (provider in connections API) |
| confluence_row_state | (NOT INSTALLED / SIGN IN / SIGNED IN AS) | CConfluence○NOT SET UPConnect | DATA | Confluence source row connection state |
| confluence_defaults | ['RECENT BLOGS', 'PAGES BY ID'] | [] | DATA | Confluence default watch labels |
| github_row_present | true (provider listed in connections) | True | MATCH | github row presence (provider in connections API) |
| jira_row_present | true (provider listed in connections) | True | MATCH | jira row presence (provider in connections API) |
| confluence_row_present | true (provider listed in connections) | True | MATCH | confluence row presence (provider in connections API) |

## Shots

- settings-system @ 1440: `walk-remote-1440.png`
- shade-receipts @ 1440: `walk-shade-receipts-1440.png`
- rhythm @ 1440: `walk-rhythm-1440.png`
- door @ 1440: `walk-door-1440.png`
- settings-system @ 393: `walk-remote-393.png`
- shade-receipts @ 393: `walk-shade-receipts-393.png`
- rhythm @ 393: `walk-rhythm-393.png`
- door @ 393: `walk-door-393.png`

## Defects

None.

