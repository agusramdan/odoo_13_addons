#!/bin/sh
# Static lifecycle tests only: mock docker; never contact a daemon.
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/bin" "$tmp/evidence"
printf '%s\n' '#!/bin/sh' 'printf "%s\n" "$*" >> "$MOCK_CALLS"' 'case "$*" in *\ ps\ --all\ --quiet) printf "%s\n" "${MOCK_CONTAINERS:-}";; *volume\ ls\ --quiet*) printf "%s\n" "${MOCK_VOLUMES:-}";; *network\ ls\ --quiet*) printf "%s\n" "${MOCK_NETWORKS:-}";; esac' 'case "$*" in *"$MOCK_FAIL_MATCH"*) [ -z "${MOCK_FAIL_MATCH:-}" ] || exit 1;; esac' 'exit "${MOCK_DOCKER_EXIT:-0}"' > "$tmp/bin/docker"
chmod +x "$tmp/bin/docker"
compose_file="$repo/tests/docker-compose-uat.yml"
export PATH="$tmp/bin:$PATH" MOCK_CALLS="$tmp/calls"
export UAT_COMPOSE_PROJECT=task-uat-79 UAT_STATE_FILE="$tmp/state"
export UAT_EVIDENCE_DIR="$tmp/evidence" UAT_COMPOSE_FILE="$compose_file"
export UAT_PROFILE=uat-offline UAT_MAX_RUNS=3 UAT_DB_NAME=odoo13uat
export UAT_PYTHON_RUNTIME=3.8.20

# Three invocations count as three total started attempts and each cleans only
# the named project; a fourth invocation is rejected before calling docker.
for n in 1 2 3; do
  "$repo/tests/run-uat.sh" uat-runner
  [ "$(cat "$UAT_STATE_FILE")" = "$n" ]
done
if "$repo/tests/run-uat.sh" uat-runner 2>"$tmp/limit.err"; then
  echo 'expected the fourth attempt to be rejected' >&2; exit 1
fi
grep -q 'maximum of 3 total started attempts' "$tmp/limit.err"
[ "$(wc -l < "$MOCK_CALLS")" -eq 18 ]
[ "$(grep -c ' up --abort-on-container-exit --exit-code-from uat-runner uat-runner$' "$MOCK_CALLS")" -eq 3 ]
[ "$(grep -c ' down --volumes --remove-orphans$' "$MOCK_CALLS")" -eq 3 ]
! grep -Eq 'prune| -v$' "$MOCK_CALLS"
[ -f "$tmp/evidence/attempt-1.log" ]
[ "$(stat -c %a "$tmp/evidence")" = 700 ]
[ "$(stat -c %a "$tmp/evidence/attempt-1.log")" = 600 ]

# A mismatched Compose file is rejected before any Docker invocation.
rm -f "$MOCK_CALLS"
export UAT_COMPOSE_FILE="$repo/tests/Dockerfile.uat"
if "$repo/tests/run-uat.sh" uat-runner 2>"$tmp/path.err"; then
  echo 'expected mismatched Compose path to be rejected' >&2; exit 1
fi
grep -q 'Compose file path must be the exact' "$tmp/path.err"
[ ! -s "$MOCK_CALLS" ]
export UAT_COMPOSE_FILE="$compose_file"

# Any extant project resource blocks use and cleanup; inventory errors do too.
export MOCK_CONTAINERS='old-container-id'
if "$repo/tests/run-uat.sh" uat-runner 2>"$tmp/reused.err"; then
  echo 'expected reused project to be rejected' >&2; exit 1
fi
grep -q 'already has resources' "$tmp/reused.err"
[ "$(wc -l < "$MOCK_CALLS")" -eq 3 ]
for kind in VOLUMES NETWORKS; do
  rm -f "$MOCK_CALLS" "$UAT_STATE_FILE"
  export MOCK_CONTAINERS='' MOCK_VOLUMES='' MOCK_NETWORKS=''
  eval "export MOCK_$kind='old-project-resource'"
  if "$repo/tests/run-uat.sh" uat-runner 2>"$tmp/reused-$kind.err"; then
    echo "expected pre-existing project $kind to be rejected" >&2; exit 1
  fi
  grep -q 'already has resources' "$tmp/reused-$kind.err"
  [ ! -e "$UAT_STATE_FILE" ]
  [ "$(wc -l < "$MOCK_CALLS")" -eq 3 ]
  eval "export MOCK_$kind=''"
done
rm -f "$MOCK_CALLS"
export MOCK_CONTAINERS='' MOCK_VOLUMES='' MOCK_NETWORKS=''
export MOCK_DOCKER_EXIT=0

# Inventory failure fails closed before ledger increment or cleanup.
rm -f "$UAT_STATE_FILE" "$MOCK_CALLS"
cat > "$tmp/bin/docker" <<'MOCK'
#!/bin/sh
printf '%s\n' "$*" >> "$MOCK_CALLS"
exit 1
MOCK
chmod +x "$tmp/bin/docker"
if "$repo/tests/run-uat.sh" uat-runner 2>"$tmp/inventory.err"; then
  echo 'expected inventory failure to be rejected' >&2; exit 1
fi
grep -q 'cannot verify Compose project is resource-free' "$tmp/inventory.err"
[ ! -e "$UAT_STATE_FILE" ]
[ "$(wc -l < "$MOCK_CALLS")" -eq 1 ]

# Cleanup failure must fail the wrapper, even if the service command succeeds.
rm -f "$UAT_STATE_FILE" "$MOCK_CALLS"
export MOCK_DOCKER_EXIT=0
# Mock fails only the scoped down command, not the service invocation.
cat > "$tmp/bin/docker" <<'MOCK'
#!/bin/sh
printf '%s\n' "$*" >> "$MOCK_CALLS"
case "$*" in *' ps --all --quiet') exit 0;; *' down --volumes --remove-orphans') exit 1;; esac
exit 0
MOCK
chmod +x "$tmp/bin/docker"
if "$repo/tests/run-uat.sh" uat-runner 2>"$tmp/cleanup.err"; then
  echo 'expected cleanup failure to block closure' >&2; exit 1
fi
grep -q 'cleanup FAILED; closure blocked' "$tmp/cleanup.err"
echo 'mock lifecycle checks passed; Docker daemon was not contacted'
