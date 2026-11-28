---
name: odoo-browser-test
description: Use when testing Odoo 13 in a real browser.
---

# Odoo 13 browser test

Run one explicit Odoo `HttpCase.browser_js` method:

```sh
python3 .agents/skills/odoo-browser-test/scripts/run.py --addon /absolute/path/to/addon --test Class.test_method --timeout 1800
```

Requires Docker daemon access, Odoo 13 and PostgreSQL 10 images locally or network access to pull them, and network access to archived Debian packages on first build. The runner builds Chromium and websocket-client into a temporary image. It starts a fresh PostgreSQL tmpfs and an Odoo container on an internal Docker network without published ports, copies the selected addon and transitive sibling addon dependencies into a read-only container filesystem, and removes run-labelled containers/network afterward. No existing database or credentials are used. Dependencies outside the selected addon's parent must already be available in the Odoo image; missing dependencies fail the run. Symlinked local addon directories and malformed manifests fail explicitly. Cleanup errors make the run fail. Review the addon and tests before running: addon code executes in the container. Docker daemon administrators can inspect temporary credentials. Logs may contain test data; treat captured output accordingly.

**Mandatory:** all addon browser test files must reside in `<addon>/tests/browser/`; never place them elsewhere. For Odoo 13 discovery, put `from .browser import test_browser` in `<addon>/tests/__init__.py`, and create `<addon>/tests/browser/__init__.py` (it may be empty); define the selected `HttpCase` in `<addon>/tests/browser/test_browser.py`. The selected test must be imported this way, use `post_install` if appropriate, and actually call `browser_js`. The runner checks a unique static definition under this directory, plus reported logs and exit status. Dynamic imports or monkeypatching may defeat these checks; inspect trusted code. Addon code can forge logs, alter Odoo execution, or call `browser_js` deceptively: a zero exit is only reported success, never independent proof of browser execution or test location. This is not UAT. A synthetic test does not validate user workflows.

Docker isolation is defense in depth, not a sandbox for hostile addons. The app has no published ports, a read-only root, dropped capabilities, no-new-privileges, 3 GiB memory, 2 CPUs and 256 processes; PostgreSQL has the same resource limits and a disposable tmpfs database. The internal network still connects both containers. Docker daemon/kernel vulnerabilities, daemon administrators, image builds, log volume, host disk, and other daemon resources are outside these limits. Review code and images; run untrusted code only in an independently isolated disposable VM. Source path validation is not race-free against concurrent filesystem mutation. The execution deadline bounds Docker calls after validation, not build preparation, cleanup or daemon-side work; cleanup uses separate bounded calls and can fail, requiring manual inspection of run-labelled resources. A Docker create/build may finish after its client times out, even after automatic cleanup succeeds. Once daemon-side operations have settled, rerun `python3 .agents/skills/odoo-browser-test/scripts/run.py --recover RUN_ID` using the 32-character ID printed in the run label; repeat reconciliation and inspect labelled resources as needed. Recovery removes containers, networks and final images bearing that label only. It cannot cancel ongoing daemon work or guarantee cleanup; stopped/unreachable daemons, interrupted builds, build cache/intermediate layers, pulled base images and daemon storage may require administrator inspection or pruning under separate authorization. Labels are not a security boundary against daemon users.

Run runner checks with `python3 -m unittest discover -s .agents/skills/odoo-browser-test/tests -v`.
