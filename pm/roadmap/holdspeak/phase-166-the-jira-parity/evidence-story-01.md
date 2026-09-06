# Evidence - HS-166-01

- **Story:** HS-166-01 - The acli pack + the connection ledger (many accounts × many sites; switch-and-verify)
- **Status:** done
- **Date:** 2026-09-02

## Proof

### Captured run — 2026-09-03T02:31:08Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-01-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0ec8656704add97be1f10a71235084ea8e8d1107

```text
=== SCOPED (isolated HOME) ===
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
241 passed, 2 skipped in 40.78s
=== LIVE (real acli, real HOME) ===
acli: /opt/homebrew/bin/acli
ref parity (bare == url-form): True karolsaneapple.atlassian.net|karolsane+apple@gmail.com
known_accounts (acli registry): [('karolsaneapple.atlassian.net', 'karolsane+apple@gmail.com', True)]
add -> state: disconnected | ref: karolsaneapple.atlassian.net|karolsane+apple@gmail.com
readiness before probe: {"state": "partial", "connections": 1, "connected": 0}
LIVE status: connected | code: None | account: {'site': 'karolsaneapple.atlassian.net', 'email': 'karolsane+apple@gmail.com'} | last_connected_at set: True
WRONG-EMAIL status: owner_action_required | code: authentication_required | recovery: acli jira auth login --site karolsaneapple.atlassian.net --email nobody@example.com --token
readiness after: {"state": "connected", "connections": 2, "connected": 1}
rows: [('karolsaneapple.atlassian.net|nobody@example.com', 'owner_action_required'), ('karolsaneapple.atlassian.net|karolsane+apple@gmail.com', 'connected')]
LIVE PROOF OK
```
