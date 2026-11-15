#!/usr/bin/env python3
"""Produce a read-only, non-authorizing Odoo UAT plan; never execute it."""
import argparse
import errno
import hashlib
import stat
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SAFE = re.compile(r'^[a-z][a-z0-9_-]{0,39}$')
IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,62}$')
SENSITIVE = re.compile(r'(^|[./_-])(secret|credential|password|token|private|\.env)([./_-]|$)', re.I)

def git(repo, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_NOSYSTEM='1')
    p = subprocess.run(['git', '-C', str(repo), *args], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, env=env, check=False)
    if p.returncode:
        raise ValueError('git inspection failed: ' + args[0])
    return p.stdout

def digest(b):
    return hashlib.sha256(b).hexdigest()

def items(data):
    return [os.fsdecode(x) for x in data.split(b'\0') if x]

def worktree_entry(repo, name):
    # Anchor every lookup to a held directory descriptor; never follow links.
    parts = name.split('/')
    if any(part in ('', '.', '..') for part in parts):
        return {'kind': 'unsupported'}
    if not all(hasattr(os, flag) for flag in ('O_NOFOLLOW', 'O_DIRECTORY', 'O_NONBLOCK')):
        return {'kind': 'unsupported'}
    fd = None
    try:
        fd = os.open(repo, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            if not stat.S_ISREG(os.fstat(file_fd).st_mode):
                return {'kind': 'unsupported'}
            hasher = hashlib.sha256()
            while True:
                chunk = os.read(file_fd, 1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
            return {'kind': 'file', 'sha256': hasher.hexdigest()}
        finally:
            os.close(file_fd)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return {'kind': 'deleted'}
        return {'kind': 'unsupported'}
    finally:
        if fd is not None:
            os.close(fd)

def inventory(repo):
    flags = git(repo, 'ls-files', '-v', '-z').split(b'\0')
    if any(record and (record[:1].islower() or record[:1] == b'S') for record in flags):
        raise ValueError('hidden index flags detected; candidate cannot be safely inventoried')
    head = git(repo, 'rev-parse', '--verify', 'HEAD').decode().strip()
    branch = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD').decode().strip() if subprocess.run(['git', '-C', str(repo), 'symbolic-ref', '--quiet', 'HEAD'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')).returncode == 0 else None
    staged = items(git(repo, 'diff', '--cached', '--name-only', '-z', '--no-renames'))
    unstaged = items(git(repo, 'diff', '--name-only', '-z', '--no-renames'))
    untracked = items(git(repo, 'ls-files', '--others', '--exclude-standard', '-z'))
    records = []
    sensitive = [name for name in set(staged + unstaged + untracked)
                 if SENSITIVE.search(name) or Path(name).name.startswith('.env')]
    if sensitive:
        raise ValueError('sensitive changed paths detected; names and contents withheld')
    for name in sorted(set(staged + unstaged + untracked)):
        entry = {'path': name, 'staged': name in staged, 'unstaged': name in unstaged, 'untracked': name in untracked}
        if SENSITIVE.search(name) or Path(name).name.startswith('.env'):
            entry['content'] = 'withheld-sensitive-path'
        else:
            entry['worktree'] = worktree_entry(repo, name)
            if name in staged:
                index = git(repo, 'ls-files', '--stage', '-z', '--', ':(literal)' + name)
                entry['index_entries'] = [os.fsdecode(v) for v in index.split(b'\0') if v]
                hashes = []
                for record in entry['index_entries']:
                    meta = record.split('\t', 1)[0].split()
                    if len(meta) == 3 and (meta[0] == '160000' or meta[2] != '0'):
                        entry['unsupported_index'] = True
                    if len(meta) == 3 and meta[0] != '160000':
                        hashes.append({'stage': meta[2], 'sha256': digest(git(repo, 'cat-file', 'blob', meta[1]))})
                entry['index_sha256'] = hashes
        records.append(entry)
    return {'head': head, 'branch': branch, 'staged': staged, 'unstaged': unstaged,
            'untracked': untracked, 'changes': records}

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True)
    p.add_argument('--task-id', required=True)
    p.add_argument('--addon')
    p.add_argument('--database')
    p.add_argument('--mode', choices=['install', 'update'])
    p.add_argument('--odoo-bin')
    p.add_argument('--runtime', help='Owner-selected runtime; never inferred from a tag')
    p.add_argument('--postgres-image', help='Explicit Owner-selected image reference')
    p.add_argument('--image-metadata', help='Explicit non-secret image qualification summary (not inspected)')
    p.add_argument('--lock-id', help='Explicit complete dependency-lock identifier')
    p.add_argument('--spec-id', help='Explicit accepted spec identity/hash')
    p.add_argument('--case-mapping', help='Explicit accepted case-to-command mapping identity')
    p.add_argument('--authorization', help='Existing authorization scope identifier; not a new approval')
    p.add_argument('--ledger', help='Existing non-secret ledger path (metadata only)')
    a = p.parse_args(argv)
    if not SAFE.fullmatch(a.task_id): p.error('task-id must match [a-z][a-z0-9_-]{0,39}')
    for field in ('addon', 'database'):
        value = getattr(a, field)
        if value and not IDENT.fullmatch(value): p.error('invalid ' + field)
    if a.database and re.search(r'(^|_)(prod|production|live)($|_)', a.database, re.I): p.error('production-like database rejected')
    repo = Path(a.repo).resolve()
    try:
        root = Path(os.fsdecode(git(repo, 'rev-parse', '--show-toplevel')).strip()).resolve()
        if repo != root: p.error('--repo must be the repository root')
        first = inventory(root)
        second = inventory(root)
        stable = first == second
        canonical = json.dumps(first, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
        candidate = digest(canonical)
        blocked = {k: [] for k in ('candidate', 'lock_image_qualification', 'case_mapping', 'authorization', 'wrapper_restrictions')}
        if not stable: blocked['candidate'].append('Candidate changed during inspection; repeat preflight.')
        if any(x.get('content') or x.get('unsupported_index') or x.get('worktree', {}).get('kind') == 'unsupported' for x in first['changes']): blocked['candidate'].append('Sensitive or unsupported changed paths withheld; candidate identity incomplete.')
        if not a.lock_id: blocked['lock_image_qualification'].append('Complete dependency lock not supplied.')
        if not a.runtime or not a.postgres_image or not a.image_metadata: blocked['lock_image_qualification'].append('Explicit runtime, PostgreSQL selection and qualified image metadata are required; not verified by planner.')
        else: blocked['lock_image_qualification'].append('Supplied metadata is an assertion only; independent qualification is required.')
        if not a.spec_id or not a.case_mapping: blocked['case_mapping'].append('Accepted spec binding and case-to-command mapping required.')
        if not a.authorization: blocked['authorization'].append('Existing task-scoped runtime authorization not supplied.')
        blocked['authorization'].append('Plan-only instruction prohibits execution; no approval is created or changed.')
        blocked['wrapper_restrictions'].append('Repository wrapper is mandatory for Compose UAT; wrapper, isolation, resource occupancy and capacity are not verified.')
        proposed = 'uat-' + a.task_id[:35] + '-' + candidate[:12]
        ledger = {'status': 'not supplied'}
        if a.ledger:
            lp = Path(a.ledger).expanduser().resolve()
            if lp == root or root in lp.parents: p.error('ledger must be outside repository')
            ledger = {'status': 'exists' if lp.exists() else 'absent', 'contents': 'not read; attempt budget unverified'}
        draft = None
        home = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes'))).expanduser()
        output = {'plan_only': True, 'execution_authorized': False, 'source': {'repo': str(root), **first, 'inspection_stable': stable, 'candidate_sha256': candidate if stable else None, 'identity_definition': 'sha256 canonical JSON of source inventory; incomplete if candidate blockers exist', 'ignored_files': 'not inventoried; not approved as candidate inputs'}, 'bindings': {'runtime': None, 'details': 'free-form values withheld; assertions not verified'}, 'proposed': {'project': proposed, 'database': a.database, 'evidence_dir': str(home / 'uat-evidence' / a.task_id / candidate), 'ledger': ledger, 'resource_caps': {'odoo': {'memory_mib': 2048, 'cpu': 1, 'pids': 256}, 'postgres': {'memory_mib': 1024, 'cpu': 0.5, 'pids': 128}, 'offline': {'memory_mib': 512, 'cpu': 0.5, 'pids': 128}}, 'resource_names_are_unchecked': True}, 'draft_helper_dry_run_argv': draft, 'blockers': blocked}
        print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=True))
        return 0
    except (OSError, ValueError) as exc:
        print('plan failed: ' + str(exc), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
