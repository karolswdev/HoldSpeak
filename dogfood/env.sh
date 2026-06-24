# Source this for an interactive dogfood session:  source dogfood/env.sh
# It exports DOGFOOD_HOME and defines an `hs` shell function that runs the
# repo's holdspeak against the isolated sandbox HOME. Your real shell HOME is
# left untouched.
_DOGFOOD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
export DOGFOOD_HOME="${DOGFOOD_HOME:-$_DOGFOOD_DIR/_home}"
export DOGFOOD_INTEL_BASE_URL="${DOGFOOD_INTEL_BASE_URL:-http://192.168.1.43:8080/v1}"
export DOGFOOD_INTEL_MODEL="${DOGFOOD_INTEL_MODEL:-Qwen3.5-9B-UD-Q6_K_XL.gguf}"

hs() { "$_DOGFOOD_DIR/hs" "$@"; }

echo "dogfood env loaded. DOGFOOD_HOME=$DOGFOOD_HOME"
echo "  intel endpoint: $DOGFOOD_INTEL_BASE_URL ($DOGFOOD_INTEL_MODEL)"
echo "  use:  hs doctor   |   hs import dogfood/_audio/<scenario>.wav"
