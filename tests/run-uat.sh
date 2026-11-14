#!/bin/sh
# Task-scoped UAT lifecycle wrapper. Never run without a separate live authorization.
set -eu

fail() { printf '%s\n' "run-uat: $*" >&2; exit 64; }
: "${UAT_COMPOSE_PROJECT:?Set a unique task-scoped Compose project name}"
: "${UAT_STATE_FILE:?Set an explicit persistent attempt-ledger path outside ephemeral volumes}"
: "${UAT_EVIDENCE_DIR:?Set an evidence directory outside ephemeral volumes}"
: "${UAT_COMPOSE_FILE:?Set the approved Compose file path}"
: "${UAT_PROFILE:?Set the explicitly approved Compose profile}"
[ "${UAT_MAX_RUNS:-3}" = 3 ] || fail 'UAT_MAX_RUNS must be exactly 3 total attempts'
[ "${UAT_DB_NAME:-odoo13uat}" = odoo13uat ] || fail 'database name must be odoo13uat'
[ "${UAT_PYTHON_RUNTIME:-3.7.3}" = 3.7.3 ] || fail 'Python runtime selection must be 3.7.3'
printf '%s' "$UAT_COMPOSE_PROJECT" | grep -Eq '^[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}$' || fail 'invalid Compose project name'
case "$UAT_STATE_FILE:$UAT_EVIDENCE_DIR" in /*:/*) ;; *) fail 'state and evidence paths must be absolute' ;; esac
case "$UAT_STATE_FILE:$UAT_EVIDENCE_DIR" in *'/var/lib/'*|*'/run/'*) fail 'state/evidence must be outside ephemeral service volumes' ;; esac
expected_compose_file=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/docker-compose-uat.yml
[ -f "$UAT_COMPOSE_FILE" ] || fail 'Compose file not found'
actual_compose_file=$(realpath -e -- "$UAT_COMPOSE_FILE") || fail 'cannot resolve Compose file path'
[ "$actual_compose_file" = "$expected_compose_file" ] || fail 'Compose file path must be the exact tests/docker-compose-uat.yml template'
[ "$#" -gt 0 ] || fail 'pass the approved Compose service names explicitly'

umask 077
mkdir -p "$(dirname "$UAT_STATE_FILE")" "$UAT_EVIDENCE_DIR"
chmod 700 "$UAT_EVIDENCE_DIR"
lock="${UAT_STATE_FILE}.lock"
command -v flock >/dev/null 2>&1 || fail 'flock is required for an atomic attempt ledger'
exec 9>"$lock"
flock -x 9
# Refuse any pre-existing project resources before incrementing the attempt
# ledger or allowing up/down. A failed/ambiguous inventory is fail-closed.
if ! existing_containers=$(docker compose -f "$UAT_COMPOSE_FILE" -p "$UAT_COMPOSE_PROJECT" --profile "$UAT_PROFILE" ps --all --quiet 2>&1); then
  fail 'cannot verify Compose project is resource-free'
fi
if ! existing_volumes=$(docker volume ls --quiet --filter "label=com.docker.compose.project=$UAT_COMPOSE_PROJECT" 2>&1); then
  fail 'cannot verify Compose project is resource-free'
fi
if ! existing_networks=$(docker network ls --quiet --filter "label=com.docker.compose.project=$UAT_COMPOSE_PROJECT" 2>&1); then
  fail 'cannot verify Compose project is resource-free'
fi
[ -z "$existing_containers$existing_volumes$existing_networks" ] || fail 'Compose project already has resources; refusing reused-project cleanup'

count=0
if [ -e "$UAT_STATE_FILE" ]; then
  IFS= read -r count < "$UAT_STATE_FILE" || fail 'cannot read attempt ledger'
  case "$count" in ''|*[!0-9]*) fail 'invalid attempt ledger' ;; esac
fi
[ "$count" -lt 3 ] || fail 'maximum of 3 total started attempts reached'
count=$((count + 1))
printf '%s\n' "$count" > "${UAT_STATE_FILE}.new"
mv "${UAT_STATE_FILE}.new" "$UAT_STATE_FILE"
flock -u 9

log="$UAT_EVIDENCE_DIR/attempt-${count}.log"
cleanup_status=0
cleanup() {
  rc=$?
  trap - EXIT HUP INT TERM
  # Exact project + exact Compose file only; no global prune or DB-wide command.
  if ! docker compose -f "$UAT_COMPOSE_FILE" -p "$UAT_COMPOSE_PROJECT" --profile "$UAT_PROFILE" down --volumes --remove-orphans >>"$log" 2>&1; then
    cleanup_status=1
    printf '%s\n' 'run-uat: scoped Compose cleanup FAILED; closure blocked' >&2
  fi
  if [ "$cleanup_status" -ne 0 ]; then exit 70; fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# The wrapper never invents test commands; caller supplies authorized service names.
# Logs are kept outside Compose-managed volumes for post-cleanup review.
set +e
docker compose -f "$UAT_COMPOSE_FILE" -p "$UAT_COMPOSE_PROJECT" --profile "$UAT_PROFILE" up --abort-on-container-exit --exit-code-from "$1" "$@" >"$log" 2>&1
rc=$?
set -e
exit "$rc"
