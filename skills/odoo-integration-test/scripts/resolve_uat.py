#!/usr/bin/env python3
"""Read-only UAT configuration proposal; never approves or executes a run."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import plan_uat as planner


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def resolve(repo, task, profile_path, profile_sha256):
    if not planner.SAFE.fullmatch(task):
        raise ValueError('invalid task identifier')
    root = Path(repo).resolve()
    actual = Path(planner.git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    if root != actual:
        raise ValueError('repository root required')
    path = Path(profile_path)
    if path.is_absolute() or any(p in ('..', '.') for p in path.parts) or planner.SENSITIVE.search(profile_path) or path.name.startswith('.env'):
        raise ValueError('invalid profile path')
    if not re.fullmatch(r'[0-9a-f]{64}', profile_sha256):
        raise ValueError('invalid profile hash')
    first = planner.inventory(root)
    second = planner.inventory(root)
    candidate = hashlib.sha256(canonical(first)).hexdigest()
    blockers = {k: [] for k in ('candidate', 'profile', 'acceptance_authorization', 'isolation', 'runtime')}
    if first != second or any(x.get('unsupported_index') or x.get('worktree', {}).get('kind') == 'unsupported' for x in first['changes']):
        blockers['candidate'].append('candidate_inventory_incomplete_or_changed')
    # Read the committed blob only. A supplied hash proves byte identity, not approval.
    tree = planner.git(root, 'ls-tree', '-z', first['head'], '--', ':(literal)' + profile_path)
    entries = [x for x in tree.split(b'\0') if x]
    if len(entries) != 1 or not entries[0].startswith((b'100644 blob ', b'100755 blob ')):
        raise ValueError('profile must be a committed regular file')
    raw = planner.git(root, 'show', first['head'] + ':' + profile_path)
    if hashlib.sha256(raw).hexdigest() != profile_sha256:
        raise ValueError('profile hash mismatch')
    if len(raw) > 65536:
        raise ValueError('profile too large')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate profile key')
            result[key] = value
        return result
    try:
        profile = json.loads(raw, object_pairs_hook=unique)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError('invalid profile JSON') from None
    if not isinstance(profile, dict) or profile.get('task_id') != task:
        raise ValueError('profile task mismatch')
    # Only known, non-secret fields are ever copied to output.
    config = {}
    provenance = {}
    validators = {
        'database': lambda v: isinstance(v, str) and bool(planner.IDENT.fullmatch(v)) and not re.search(r'(^|_)(prod|production|live)($|_)', v, re.I),
        'runtime': lambda v: isinstance(v, str) and bool(re.fullmatch(r'python[0-9]+\.[0-9]+', v)),
        'max_runs': lambda v: type(v) is int and 1 <= v <= 10,
        'profile': lambda v: v in ('uat-native', 'uat-offline'),
        'data': lambda v: v == 'synthetic',
        'egress': lambda v: v == 'denied',
        'host_ports': lambda v: v == 'disabled',
        'database_lifecycle': lambda v: v == 'disposable',
        'cleanup': lambda v: v == 'exact-run-owned-only',
    }
    for key, validate in validators.items():
        value = profile.get(key)
        if validate(value):
            config[key] = value
            provenance[key] = 'committed_profile_unverified'
        else:
            blockers['profile'].append('missing_or_invalid_' + key)
    config['compose_project'] = 'uat-' + task[:35] + '-' + candidate[:12]
    provenance['compose_project'] = 'task_and_inventory_digest_unchecked_occupancy'
    config['resource_caps'] = {'odoo': {'memory_mib': 2048, 'cpu': 1, 'pids': 256}, 'postgres': {'memory_mib': 1024, 'cpu': 0.5, 'pids': 128}, 'offline': {'memory_mib': 512, 'cpu': 0.5, 'pids': 128}}
    provenance['resource_caps'] = 'conservative_proposal_capacity_unchecked'
    blockers['acceptance_authorization'].append('profile_and_hash_do_not_prove_acceptance_or_current_authorization')
    blockers['isolation'].append('compose_mounts_network_resources_and_occupancy_not_verified')
    blockers['runtime'].append('image_dependencies_cases_wrapper_ledger_and_capacity_not_verified')
    return {'read_only': True, 'execution_implemented': False, 'execution_authorized': False,
            'task_id': task, 'candidate': {'head': first['head'], 'inventory_sha256': candidate if first == second and not blockers['candidate'] else None, 'ignored_files': 'not inventoried', 'snapshot': 'not created'},
            'profile_artifact': {'path': profile_path, 'sha256': profile_sha256, 'source': 'committed_blob', 'acceptance': 'unverified'},
            'config_proposal': config, 'provenance': provenance, 'blockers': blockers}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--profile', required=True, help='repository-relative committed JSON profile')
    parser.add_argument('--profile-sha256', required=True, help='expected exact committed profile SHA-256; not proof of approval')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(resolve(args.repo, args.task_id, args.profile, args.profile_sha256), indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError) as exc:
        print('resolution blocked: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
