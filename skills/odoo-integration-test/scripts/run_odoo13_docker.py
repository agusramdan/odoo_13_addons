#!/usr/bin/env python3
"""Task-scoped direct-Docker Odoo 13 addon integration runner."""
import argparse
import fcntl
import hashlib
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile
import uuid

TASK_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')
ADDON_RE = re.compile(r'^[a-z][a-z0-9_]{0,63}$')
DIGEST_RE = re.compile(r'^sha256:[0-9a-f]{64}$')


class Blocked(Exception):
    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code


def tests_succeeded(log, addon=None):
    count = re.search(r"Ran\s+(\d+)\s+tests?", log)
    modules = re.findall(r"(?m)^.*?Module ([\w.]+): (\d+) failures, (\d+) errors\s*$", log)
    if not count or int(count.group(1)) <= 0 or re.search(r"(?im)^FAILED|\b(?:failures|errors)=[1-9]", log):
        return False
    if modules:
        return (addon is None or any(name == addon for name, _, _ in modules)) and all(failures == "0" and errors == "0" for _, failures, errors in modules)
    if addon:
        pattern = r"(?m)^.*?odoo\.addons\.([a-z][a-z0-9_]*)\.tests\.[\w.]+ running tests\.\s*$"
        starts = list(re.finditer(pattern, log))
        for index, match in enumerate(starts):
            end = starts[index + 1].start() if index + 1 < len(starts) else len(log)
            counts = re.findall(r"Ran\s+(\d+)\s+tests?", log[match.end():end])
            if match.group(1) == addon and any(int(n) > 0 for n in counts):
                return True
        return False
    return bool(re.search(r"(?m)^OK(?:\s|$)", log))


def addons_root(snapshot, addon):
    root = pathlib.Path(snapshot)
    matches = [candidate for candidate in (root, root / 'addons')
               if (candidate / addon / '__manifest__.py').is_file()]
    if len(matches) != 1:
        raise Blocked('addon source missing or ambiguous within snapshot')
    return matches[0]


def _hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.digest()


def tree_hash(root):
    root = pathlib.Path(root)
    h = hashlib.sha256()
    for f in sorted(root.rglob('*')):
        if f.is_symlink():
            raise Blocked('snapshot/source contains symlink')
        if f.is_file():
            rel = f.relative_to(root).as_posix().encode()
            h.update(len(rel).to_bytes(4, 'big')); h.update(rel); h.update(_hash_file(f))
        elif not f.is_dir():
            raise Blocked('snapshot/source contains special file')
    return h.hexdigest()


def validate(task, addon, config_path=None):
    if not TASK_RE.fullmatch(task): raise Blocked('invalid task-id')
    if not ADDON_RE.fullmatch(addon): raise Blocked('invalid addon')
    home = pathlib.Path(os.environ.get('HERMES_HOME', pathlib.Path.home() / '.hermes'))
    task_dir = home / 'uat-state' / task
    p = pathlib.Path(config_path) if config_path else task_dir / 'integration-runner.json'
    if p != task_dir / 'integration-runner.json': raise Blocked('config must be the task-scoped integration-runner.json')
    if p.is_symlink() or not p.is_file(): raise Blocked('task config must already exist as a regular file')
    if p.stat().st_mode & 0o077: raise Blocked('task config permissions must be 0600 or stricter')
    try: c = json.loads(p.read_text())
    except Exception as e: raise Blocked('invalid task config JSON') from e
    if c.get('task_id') != task: raise Blocked('config task identity mismatch')
    if task not in str(c.get('snapshot', '')) or task not in str(c.get('ledger', '')): raise Blocked('task identifier missing from config paths')
    entry = c.get('addons', {}).get(addon)
    if not isinstance(entry, dict): raise Blocked('addon absent from approved task config')
    snapshot = pathlib.Path(c.get('snapshot', ''))
    manifest = c.get('manifest_sha256', '')
    if snapshot.is_symlink() or not snapshot.is_dir() or not re.fullmatch(r'[a-f0-9]{64}', str(manifest)): raise Blocked('invalid snapshot or manifest hash')
    if tree_hash(snapshot) != manifest: raise Blocked('snapshot manifest hash mismatch')
    c['_addons_root'] = str(addons_root(snapshot, addon))
    for key in ('odoo_image_id', 'postgres_image_id'):
        if not isinstance(c.get(key), str) or not DIGEST_RE.fullmatch(c[key]): raise Blocked('exact pinned image IDs required')
    ledger = pathlib.Path(c.get('ledger', ''))
    if ledger.is_symlink() or not ledger.is_file(): raise Blocked('existing ledger required; it is never created')
    if type(c.get('max_attempts')) is not int or c['max_attempts'] < 1: raise Blocked('invalid attempt budget')
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}', str(c.get('database', ''))): raise Blocked('invalid database identifier')
    if not isinstance(entry.get('test_tags'), str) or not re.fullmatch(r'/[a-z][a-z0-9_]{0,63}', entry['test_tags']): raise Blocked('invalid test selector')
    return c, entry


def reserve_attempt(ledger_path, maximum, run_id):
    p = pathlib.Path(ledger_path)
    if p.is_symlink() or not p.is_file(): raise Blocked("existing ledger required")
    lock_fd = os.open(str(p) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(lock_fd, 0o600)
        with os.fdopen(lock_fd, "r+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            raw = p.read_text()
            if not re.fullmatch(r"(0|[1-9][0-9]*)\n", raw): raise Blocked("ledger format invalid")
            n = int(raw)
            if n >= maximum: raise Blocked("approved attempt budget exhausted")
            fd, temporary = tempfile.mkstemp(prefix="." + p.name + ".", dir=p.parent)
            try:
                with os.fdopen(fd, "w") as out:
                    out.write(str(n + 1) + chr(10)); out.flush(); os.fsync(out.fileno())
                os.chmod(temporary, p.stat().st_mode & 0o777)
                os.replace(temporary, p)
                directory = os.open(p.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try: os.fsync(directory)
                finally: os.close(directory)
            finally:
                try: os.unlink(temporary)
                except FileNotFoundError: pass
    except OSError as e:
        raise Blocked("ledger update failed") from e
    return n + 1


class Docker:
    def __init__(self, timeout): self.timeout = timeout
    def call(self, *args, check=True):
        try: r = subprocess.run(['docker', *map(str, args)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=self.timeout)
        except subprocess.TimeoutExpired as e: raise Blocked('docker command timed out') from e
        except OSError as e: raise Blocked('docker unavailable') from e
        if check and r.returncode:
            detail = r.stderr.strip().splitlines()[-1][:200] if r.stderr.strip() else 'no diagnostic'
            raise Blocked('docker operation failed: ' + ' '.join(map(str, args[:2])) + ': ' + detail)
        return r
    def inspect(self, kind, name):
        fmt = '{{json .Labels}}' if kind == 'network' else '{{json .Config.Labels}}'
        r = self.call(kind, 'inspect', '--format', fmt, name, check=False)
        if r.returncode and ('No such' in r.stderr or 'not found' in r.stderr): return None
        if r.returncode: raise Blocked('resource readback failed: ' + name)
        try: return json.loads(r.stdout)
        except Exception as e: raise Blocked('invalid resource readback: ' + name) from e


def _image_identity(d, image, pg=False):
    fmt = '{{.Id}}|{{json .Config.Env}}' if pg else '{{.Id}}|{{json .Config.Env}}|{{.Config.User}}'
    r = d.call('image', 'inspect', '--format', fmt, image)
    try:
        fields = r.stdout.strip().split('|', 2)
        ident, env = fields[:2]; env = json.loads(env)
        user = '' if pg else fields[2]
    except Exception as e: raise Blocked('image inspection malformed') from e
    if ident != image: raise Blocked('configured image ID does not match local image identity')
    if pg and 'PG_MAJOR=10' not in env: raise Blocked('PostgreSQL image is not major version 10')
    return user


def _image_uid(d, image, user, name, labels, task, run_id):
    d.call('create', '--pull=never', '--name', name, *labels, '--network', 'none', '--entrypoint', '/usr/bin/id', image, '-u', user, check=False)
    _assert_owned(d, 'container', name, task, run_id)
    output = d.call('start', '--attach', name).stdout.strip()
    try: status = int(d.call('wait', name).stdout.strip()); uid = int(output)
    except ValueError as e: raise Blocked('cannot resolve image user UID') from e
    if status != 0 or uid <= 0: raise Blocked('image user must be non-root')
    return uid


def _assert_owned(d, kind, name, task, run_id):
    labels = d.inspect(kind, name)
    if labels is None: raise Blocked('resource create/readback failed: ' + name)
    if labels.get('hermes.uat.task') != task or labels.get('hermes.uat.run') != run_id:
        raise Blocked('resource name collision with foreign ownership: ' + name)


def run(task, addon, config, entry, timeout=1800, docker=None):
    if not isinstance(timeout, int) or not 1 <= timeout <= 7200: raise Blocked('timeout must be 1..7200 seconds')
    d = docker or Docker(timeout)
    run_id = uuid.uuid4().hex
    safe_task = re.sub(r'[^a-z0-9_.-]', '-', task.lower())[:28]
    prefix = f'odoo13-{safe_task}-{run_id[:12]}'
    network, pg, app = prefix + '-net', prefix + '-pg', prefix + '-app'
    label_task, label_run = 'hermes.uat.task', 'hermes.uat.run'
    labels = [f'--label={label_task}={task}', f'--label={label_run}={run_id}']
    tmpdir = None
    secret_path = config_path = None
    secret = None
    odoo_uid_probe, pg_uid_probe = prefix + '-odoo-uid', prefix + '-pg-uid'
    resources = [('network', network), ('container', pg_uid_probe), ('container', odoo_uid_probe),
                 ('container', pg), ('container', app)]
    result_code = 1
    log_path = pathlib.Path(config['ledger']).parent / f'{task}-{addon}-{run_id}.log'
    try:
        reserve_attempt(config['ledger'], config['max_attempts'], run_id)
        odoo_user = _image_identity(d, config['odoo_image_id'])
        _image_identity(d, config['postgres_image_id'], pg=True)
        odoo_uid = _image_uid(d, config['odoo_image_id'], odoo_user, odoo_uid_probe, labels, task, run_id)
        pg_uid = _image_uid(d, config['postgres_image_id'], 'postgres', pg_uid_probe, labels, task, run_id)
        tmpdir = pathlib.Path(tempfile.mkdtemp(prefix=prefix + '-', dir=os.environ.get('TMPDIR')))
        tmpdir.chmod(0o700)
        secret_path = tmpdir / 'pgpass'; config_path = tmpdir / 'odoo.conf'
        secret = os.urandom(32).hex()
        secret_path.write_text(secret); secret_path.chmod(0o400)
        config_path.write_text('[options]\ndb_host = ' + pg + '\ndb_user = odoo\ndb_password = ' + secret + '\ndb_name = ' + config['database'] + '\n')
        config_path.chmod(0o400)
        try:
            subprocess.run(['sudo', '-n', 'chown', str(odoo_uid) + ':' + str(odoo_uid), str(config_path)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (OSError, subprocess.CalledProcessError) as e:
            raise Blocked('must be able to assign config ownership to Odoo image user') from e
        d.call('network', 'create', '--internal', *labels, network, check=False)
        _assert_owned(d, 'network', network, task, run_id)
        d.call('create', '--pull=never', '--name', pg, *labels, '--network', network,
                           '--memory', '1g', '--cpus', '0.5', '--pids-limit', '128',
                           '--tmpfs', '/var/lib/postgresql/data:rw,noexec,nosuid,size=2g',
                           '--mount', f'type=bind,src={secret_path},dst=/run/secrets/pgpass,readonly',
                           '-e', 'POSTGRES_USER=odoo', '-e', 'POSTGRES_PASSWORD_FILE=/run/secrets/pgpass',
                           '-e', 'POSTGRES_DB=postgres', config['postgres_image_id'], check=False)
        _assert_owned(d, 'container', pg, task, run_id)
        d.call('start', pg)
        deadline = __import__('time').monotonic() + min(timeout, 120)
        while True:
            ready = d.call('exec', pg, 'pg_isready', '-h', '127.0.0.1', '-U', 'odoo', '-d', 'postgres', check=False)
            if ready.returncode == 0: break
            if __import__('time').monotonic() >= deadline: raise Blocked('PostgreSQL readiness timed out')
            __import__('time').sleep(1)
        d.call('exec', pg, 'createdb', '-U', 'odoo', config['database'])
        app_args = ['create', '--pull=never', '--name', app, *labels, '--network', network,
                    '--memory', '2g', '--cpus', '1', '--pids-limit', '256',
                    '--mount', f"type=bind,src={config.get('_addons_root', pathlib.Path(config['snapshot']) / 'addons')},dst=/mnt/odoo-src,readonly",
                    '--mount', f'type=bind,src={config_path},dst=/run/uat/odoo.conf,readonly',
                    '--entrypoint', 'sleep', config['odoo_image_id'], 'infinity']
        d.call(*app_args, check=False)
        _assert_owned(d, 'container', app, task, run_id)
        d.call('start', app)
        odoo_cmd = ['exec', '-e', 'HOME=/tmp', app, 'python3', '/usr/bin/odoo',
                    '--config=/run/uat/odoo.conf', '--stop-after-init',
                    '--addons-path=/mnt/odoo-src,/usr/lib/python3/dist-packages/odoo/addons',
                    '--database=' + config['database'], '-i', addon,
                    '--test-enable', '--test-tags=' + entry['test_tags'],
                    '--log-level=test', '--without-demo=all']
        execution = d.call(*odoo_cmd, check=False)
        result_code = execution.returncode
        logs = d.call('logs', app, check=False)
        log = (logs.stdout + logs.stderr + execution.stdout + execution.stderr).replace(secret, '[REDACTED]')
        log_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        log_fd = os.open(str(log_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(log_fd, 'w') as f: f.write(log)
        if result_code != 0 or logs.returncode != 0 or not tests_succeeded(log, addon):
            raise Blocked('Odoo execution failed or tests were not explicitly successful; log: ' + str(log_path), result_code or 1)
    except KeyboardInterrupt:
        result_code = 130
        raise
    finally:
        cleanup_error = None
        for kind, name in reversed(resources):
            try:
                labels_found = d.inspect(kind, name)
                if labels_found is None: continue
                if labels_found.get(label_task) != task or labels_found.get(label_run) != run_id:
                    raise Blocked('refusing cleanup of resource with foreign ownership: ' + name)
                d.call('rm' if kind == 'container' else 'network', '-f' if kind == 'container' else 'rm', name, check=False)
                if d.inspect(kind, name) is not None: raise Blocked('cleanup verification failed: ' + name)
            except Exception as e:
                cleanup_error = cleanup_error or e
        if secret_path:
            try: secret_path.unlink(missing_ok=True)
            except OSError as e: cleanup_error = cleanup_error or e
        if config_path:
            try: config_path.unlink(missing_ok=True)
            except OSError as e: cleanup_error = cleanup_error or e
        if tmpdir:
            try: tmpdir.rmdir()
            except OSError as e: cleanup_error = cleanup_error or e
        if cleanup_error: raise Blocked('cleanup incomplete: ' + str(cleanup_error))
    if result_code == 0: print('NATIVE TEST LOG: ' + str(log_path))
    return result_code


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--task-id', required=True); ap.add_argument('--addon', required=True)
    ap.add_argument('--config', help='must be $HERMES_HOME/uat-state/<TASK>/integration-runner.json')
    ap.add_argument('--timeout', type=int, default=1800)
    a = ap.parse_args(argv)
    try:
        c, entry = validate(a.task_id, a.addon, a.config)
        previous = signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
        try: rc = run(a.task_id, a.addon, c, entry, a.timeout)
        finally: signal.signal(signal.SIGTERM, previous)
        print('NATIVE INTEGRATION TEST PASS: task={} addon={} (not full UAT acceptance)'.format(a.task_id, a.addon))
        return rc
    except Blocked as e:
        print('NATIVE INTEGRATION TEST FAILED/BLOCKED: ' + str(e), file=sys.stderr); return e.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == '__main__': sys.exit(main())
