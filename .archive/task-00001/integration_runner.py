#!/usr/bin/env python3
"""Run an explicitly selected Odoo 13 HttpCase in disposable Docker resources."""
import argparse
import ast
import os
import pathlib
import re
import secrets
import signal
import subprocess
import sys
import time
import uuid


def browser_test_started(log, name, selector):
    pattern = r'odoo\.addons\.' + re.escape(name) + r'\.tests\.browser\.[\w.]+: Starting ' + re.escape(selector) + r'\b'
    return bool(re.search(pattern, log))


def local_addons(addon):
    root = addon.parent.resolve()
    found = {}
    pending = [addon]
    while pending:
        current = pending.pop()
        if current.name in found:
            continue
        if current.is_symlink() or current.resolve().parent != root:
            raise ValueError('unsafe local addon path: ' + str(current))
        manifest = ast.literal_eval((current / '__manifest__.py').read_text())
        dependencies = manifest.get('depends', [])
        if not isinstance(dependencies, (list, tuple)) or any(not isinstance(d, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', d) for d in dependencies):
            raise ValueError('invalid dependencies in ' + str(current))
        found[current.name] = current
        for dependency in dependencies:
            sibling = root / dependency
            if sibling.is_symlink():
                raise ValueError('unsafe local addon symlink: ' + str(sibling))
            if sibling.exists():
                if not (sibling / '__manifest__.py').is_file():
                    raise ValueError('invalid local addon: ' + str(sibling))
                pending.append(sibling)
    return list(found.values())


def validate_paths(addon, selector):
    path = pathlib.Path(os.path.abspath(addon))
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('symlink in addon path: ' + str(part))
    for root, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            if (pathlib.Path(root) / name).is_symlink():
                raise ValueError('symlink in addon: ' + str(pathlib.Path(root) / name))
    browser = path / 'tests' / 'browser'
    if not browser.is_dir():
        raise ValueError('browser tests must be in <addon>/tests/browser')
    cls, method = selector.split('.')
    matches = []
    for file in browser.rglob('*.py'):
        tree = ast.parse(file.read_text(), filename=str(file))
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == cls:
                matches += [file for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method]
    if len(matches) != 1:
        raise ValueError('selector must have exactly one definition in tests/browser')
    return path


def cleanup(run):
    """Reconcile resources visible now; daemon operations may complete later."""
    label = 'odoo.browser.run=' + run
    failed = False
    for listing, removal in ((['ps', '-aq', '--filter', 'label=' + label], ['rm', '-f']),
                             (['network', 'ls', '-q', '--filter', 'label=' + label], ['network', 'rm']),
                             (['image', 'ls', '-aq', '--filter', 'label=' + label], ['image', 'rm', '-f'])):
        try:
            result = subprocess.run(['docker', *listing], capture_output=True, text=True, timeout=30, check=True)
            for resource in set(result.stdout.split()):
                subprocess.run(['docker', *removal, resource], check=True, stdout=subprocess.DEVNULL, timeout=30)
        except (OSError, subprocess.SubprocessError) as e:
            failed = True
            print('cleanup failed: ' + str(e), file=sys.stderr)
    return not failed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--addon', help='path to addon directory')
    p.add_argument('--test', help='Class.method')
    p.add_argument('--recover', help='run identifier to reconcile after daemon operations settle')
    p.add_argument('--timeout', type=int, default=1800)
    a = p.parse_args()
    if a.recover:
        if not re.fullmatch(r'[0-9a-f]{32}', a.recover) or a.addon or a.test:
            p.error('invalid recovery identifier or conflicting arguments')
        return 0 if cleanup(a.recover) else 1
    if not a.addon or not a.test:
        p.error('--addon and --test are required')
    addon = pathlib.Path(a.addon)
    name = addon.name
    if not re.fullmatch(r'[a-z][a-z0-9_]*', name) or not (addon / '__manifest__.py').is_file() or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\.test[A-Za-z0-9_]*', a.test) or not 1 <= a.timeout <= 7200:
        p.error('invalid addon, Class.test_method, or timeout (1..7200)')
    try:
        addon = pathlib.Path(os.path.abspath(addon))
        addons = local_addons(addon)
    except (OSError, ValueError, SyntaxError, AttributeError) as e:
        print('BLOCKED: local dependencies: ' + str(e), file=sys.stderr)
        return 1
    run = uuid.uuid4().hex
    prefix = 'odoo-browser-' + run
    network, pg, app, image = (prefix + x for x in ('-net', '-pg', '-app', ':local'))
    label = 'odoo.browser.run=' + run
    print('RUN label={} image={}'.format(label, image), flush=True)
    password = secrets.token_hex(24)
    deadline = time.monotonic() + a.timeout
    def call(*args, check=True):
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError('run deadline exceeded')
        result = subprocess.run(['docker', *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=left)
        if check and result.returncode:
            raise RuntimeError('docker ' + args[0] + ' failed: ' + result.stdout[-2000:].replace(password, '[REDACTED]'))
        return result
    def interrupted(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupted)
    try:
        call('info')
        call('build', '--pull=false', '--label', label, '-t', image, str(pathlib.Path(__file__).resolve().parent))
        call('image', 'inspect', 'postgres:10-alpine', check=False).returncode and call('pull', 'postgres:10-alpine')
        call('network', 'create', '--internal', '--label', label, network)
        call('create', '--name', pg, '--label', label, '--network', network, '--memory', '3g', '--cpus', '2', '--pids-limit', '256', '--tmpfs', '/var/lib/postgresql/data:rw,size=2g', '-e', 'POSTGRES_USER=odoo', '-e', 'POSTGRES_PASSWORD=' + password, 'postgres:10-alpine')
        call('start', pg)
        while call('exec', pg, 'pg_isready', '-U', 'odoo', check=False).returncode:
            if time.monotonic() >= deadline:
                raise TimeoutError('database readiness timeout')
            time.sleep(1)
        call('create', '--name', app, '--label', label, '--network', network, '--memory', '3g', '--cpus', '2', '--pids-limit', '256', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--read-only', '--tmpfs', '/tmp:rw,exec,nosuid,size=1g', '--tmpfs', '/var/lib/odoo:rw,uid=101,gid=101,mode=0700,size=1g', '-e', 'HOST=' + pg, '-e', 'USER=odoo', '-e', 'PASSWORD=' + password, image, '--database=browser_test', '-i', name, '--test-enable', '--test-tags=/' + name + ':TestIssuerLifecycle', '--stop-after-init', '--without-demo=all', '--log-level=test')
        for local in addons:
            call('cp', str(local), app + ':/mnt/extra-addons/' + local.name)
        result = call('start', '-a', app, check=False)
        log = result.stdout.replace(password, '[REDACTED]')
        print(log)
        counts = re.findall(r'Ran\s+(\d+)\s+tests?', log)
        count = sum(map(int, counts))
        print('EVIDENCE addon={} selector={} count={} docker_exit={}'.format(name, a.test, count, result.returncode))
        if (result.returncode or count < 1 or 'Starting TestIssuerLifecycle.' not in log or 'skipped TestIssuerLifecycle.' in log
                or re.search(r'\b[1-9]\d* (?:failures|errors)\b|\b(?:failures|errors)=[1-9]', log)):
            raise RuntimeError('test failed, browser evidence absent, or no tests executed')
        status = 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired, TimeoutError, KeyboardInterrupt) as e:
        print('BLOCKED OR FAILED:', str(e).replace(password, '[REDACTED]'), file=sys.stderr)
        status = 1
    finally:
        cleanup_failed = not cleanup(run)
        print('RECOVERY: python3 {} --recover {}'.format(pathlib.Path(__file__).resolve(), run), file=sys.stderr)
    if cleanup_failed:
        return 1
    if status == 0:
        print('REPORTED SUCCESS: untrusted addon logs are not proof of browser execution (not UAT)')
    return status

if __name__ == '__main__':
    sys.exit(main())
