#!/bin/bash
# Push web/.env.local values to Vercel (production, preview, development).
# Skips VERCEL_OIDC_TOKEN (Vercel injects this automatically per-project at
# runtime) and AUTH_URL (set separately once the production domain is known).
# Never echoes secret values.
set -euo pipefail

# Preview env vars are scoped by git branch on Vercel; this project has no
# connected git repo, so preview is skipped (CLI-based deploys use
# production/development scoping only).
ENV_FILE=".env.local"
ENVIRONMENTS=(production development)
SKIP_KEYS=("VERCEL_OIDC_TOKEN" "AUTH_URL")

should_skip() {
  local key="$1"
  for s in "${SKIP_KEYS[@]}"; do
    [[ "$key" == "$s" ]] && return 0
  done
  return 1
}

while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  if should_skip "$key"; then
    echo "skip: $key"
    continue
  fi
  for env in "${ENVIRONMENTS[@]}"; do
    if printf '%s' "$value" | vercel env add "$key" "$env" --yes --force >/tmp/vercel-env-add.log 2>&1; then
      echo "ok: $key -> $env"
    else
      echo "FAILED: $key -> $env"
      cat /tmp/vercel-env-add.log
    fi
  done
done < <(grep -E '^[A-Z_]+=' "$ENV_FILE")

rm -f /tmp/vercel-env-add.log
