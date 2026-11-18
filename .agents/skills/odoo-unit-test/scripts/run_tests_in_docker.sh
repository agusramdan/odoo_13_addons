#!/bin/sh
set -eu

SKILL_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
REPO_DIR=$(pwd -P)
IMAGE=${ODOO_UNIT_TEST_IMAGE:-unittest:odoo13-python373}
CONTAINER_ID=$(hostname)
HOST_REPO_DIR=$(docker inspect "$CONTAINER_ID" --format '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || true)
[ -n "$HOST_REPO_DIR" ] || { echo 'Cannot map /workspace to a Docker-host path; run from the configured development container.' >&2; exit 2; }
case "$REPO_DIR" in
  /workspace) REPO_REL= ;;
  /workspace/*) REPO_REL=${REPO_DIR#/workspace/} ;;
  *) echo 'Current repository must be under /workspace.' >&2; exit 2 ;;
esac
if [ -n "$REPO_REL" ]; then HOST_REPO_DIR=${HOST_REPO_DIR%/}/$REPO_REL; fi


command -v docker >/dev/null 2>&1 || { echo 'Docker is required; host-Python fallback is disabled.' >&2; exit 2; }
docker info >/dev/null 2>&1 || { echo 'Docker daemon is unavailable.' >&2; exit 2; }

# Build the repository's Odoo 13 unittest image from the devcontainer definition.
docker build --tag "$IMAGE" --file "$REPO_DIR/.devcontainer/Dockerfile.unittest" "$REPO_DIR"

PYTHON_VERSION=$(docker run --rm --entrypoint python3 "$IMAGE" --version 2>&1)
[ "$PYTHON_VERSION" = 'Python 3.7.3' ] || {
  echo "Wrong test runtime: expected Python 3.7.3, got $PYTHON_VERSION" >&2
  exit 2
}

COVERAGE=
COVERAGE_MIN=
if [ "${1-}" = "--coverage" ]; then COVERAGE=--coverage; shift; fi
if [ "${1-}" = "--coverage-min" ]; then
  [ "$#" -ge 2 ] || { echo 'Usage: --coverage-min PERCENT' >&2; exit 2; }
  COVERAGE_MIN=$2
  shift 2
fi
if [ "${1-}" = "--addon" ] && [ "$#" -eq 2 ]; then
  ADDON=$(CDPATH= cd -- "$2" && pwd -P)
  case "$ADDON/" in
    "$REPO_DIR/"*) CONTAINER_ADDON=/workspace/${ADDON#"$REPO_DIR"/} ;;
    *) echo 'Addon must be inside the current repository.' >&2; exit 2 ;;
  esac
  set -- ${COVERAGE:+"$COVERAGE"} ${COVERAGE_MIN:+--coverage-min "$COVERAGE_MIN"} --addon "$CONTAINER_ADDON"
elif [ -n "$COVERAGE" ] || [ -n "$COVERAGE_MIN" ]; then
  echo '--coverage options require --addon PATH_TO_ADDON.' >&2
  exit 2
fi


docker run --rm \
  --mount "type=bind,src=$HOST_REPO_DIR,dst=/workspace,readonly" \
  --workdir /workspace \
  "$IMAGE" "$@"
