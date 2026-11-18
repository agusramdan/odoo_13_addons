# Isolation and scope

The runner installs a process-local guard before importing pytest or collecting tests: it blocks import of psycopg2, psycopg, pg8000 and asyncpg, blocks common database modules already in `sys.modules`, and denies socket connect/connect_ex/create_connection. A self-test checks a blocked driver import and network connection. It does not prevent subprocesses, native code, preexisting connections, Unix file writes or every possible database driver; it is not a security boundary. Use a restricted container or OS network policy for untrusted test code. Do not run an Odoo server or initialize a registry in these tests. Avoid importing a real Odoo installation; the shim temporarily substitutes names only within its context. ORM integration behavior needs a separate test environment.

For an offline unit suite in a repository-provided Docker image, inspect the Dockerfile and pinned requirements first, then verify the container's actual interpreter and installed package versions. After that preflight, a restrictive invocation pattern is:

```sh
docker run --rm --network none --read-only \\
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \\
  --mount type=bind,src="$REPO",dst=/repo,readonly \\
  --mount type=bind,src="$SKILL",dst=/skill,readonly \\
  --env HOME=/tmp --env TMPDIR=/tmp \\
  --env PYTHONDONTWRITEBYTECODE=1 \\
  --workdir /repo --entrypoint python "$IMAGE" -B \\
  /skill/scripts/run_tests.py --addon "/repo/$ADDON"
```

Run one addon per invocation. Use only `/tmp` for writable scratch; do not mount the Docker socket, host ports, credentials, or writable source paths. Capture exit status and the runner's test summary/failing IDs; keep raw output in memory during diagnosis and redact credential-like fixture values before any display or persistence. This is containment for ordinary offline tests, not a complete sandbox; untrusted native code or external processes require stronger isolation.
