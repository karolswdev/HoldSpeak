#!/bin/sh
# Build a scratch HOME that looks like his Mac for the detection faces:
# gh signed in, acli with two Jira sites and one Confluence, Claude Code and Codex signed in.
# Every CLI here is a STUB (answers from files, no network). Never the real tools.
set -e
H="$1"
mkdir -p "$H/bin" "$H/.config/gh" "$H/.config/acli" "$H/.claude" "$H/.codex" "$H/repos/platform"
git -C "$H/repos/platform" init -q
cat > "$H/.config/gh/hosts.yml" <<'Y'
github.com:
    users:
        karolswdev:
    git_protocol: https
    user: karolswdev
Y
cat > "$H/.config/acli/jira_config.yaml" <<'Y'
current_profile: "c1:a1"
profiles:
  - site: acme.atlassian.net
    email: karol@acme.example
    display_name: Karol (Acme)
    auth_type: oauth
    cloud_id: c1
    account_id: a1
  - site: acme-platform.atlassian.net
    email: karol@acme.example
    display_name: Karol (Platform)
    auth_type: api_token
    cloud_id: c2
    account_id: a1
Y
cat > "$H/.config/acli/confluence_config.yaml" <<'Y'
current_profile: "c1:a1"
profiles:
  - site: acme.atlassian.net
    email: karol@acme.example
    display_name: Karol (Acme)
    auth_type: oauth
    cloud_id: c1
    account_id: a1
Y
echo '{"claudeAiOauth":{"accessToken":"rig-not-a-token"}}' > "$H/.claude/.credentials.json"
echo '{"OPENAI_API_KEY":null,"tokens":{"access_token":"rig-not-a-token"}}' > "$H/.codex/auth.json"
cat > "$H/bin/gh" <<'S'
#!/bin/sh
# STUB gh for the rig
case "$1 $2" in
  "auth status") echo "github.com"; echo "  ✓ Logged in to github.com account karolswdev (keyring)"; echo "  - Active account: true"; exit 0;;
  "--version"*) echo "gh version 2.81.0 (stub)"; exit 0;;
esac
echo "stub gh: $*" >&2; exit 1
S
cat > "$H/bin/acli" <<'S'
#!/bin/sh
# STUB acli for the rig: remembers the last switch, echoes it on status
ST="$HOME/.acli-stub-current"
if [ "$2 $3" = "auth switch" ]; then
  shift 3; site=""; email=""
  while [ $# -gt 0 ]; do case "$1" in --site) site="$2"; shift 2;; --email) email="$2"; shift 2;; *) shift;; esac; done
  printf '%s\n%s\n' "$site" "$email" > "$ST"; echo "✓ Switched to $site"; exit 0
fi
if [ "$2 $3" = "auth status" ]; then
  site=$(sed -n 1p "$ST" 2>/dev/null); email=$(sed -n 2p "$ST" 2>/dev/null)
  printf '✓ Authenticated\n  Site: %s\n  Email: %s\n  Authentication Type: oauth\n' "${site:-acme.atlassian.net}" "${email:-karol@acme.example}"; exit 0
fi
if [ "$1" = "--version" ]; then echo "acli 1.3.0 (stub)"; exit 0; fi
echo "stub acli: $*" >&2; exit 1
S
cat > "$H/bin/claude" <<'S'
#!/bin/sh
[ "$1" = "--version" ] && { echo "2.1.302 (Claude Code) (stub)"; exit 0; }
echo "stub claude: no model calls in this rig" >&2; exit 3
S
cat > "$H/bin/codex" <<'S'
#!/bin/sh
[ "$1" = "--version" ] && { echo "codex-cli 0.161.0 (stub)"; exit 0; }
echo "stub codex: no model calls in this rig" >&2; exit 3
S
chmod +x "$H/bin/"*
