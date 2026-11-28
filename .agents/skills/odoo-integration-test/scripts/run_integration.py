#!/usr/bin/env python3
"""Run Odoo integration tests against an explicitly selected test database."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
FORBIDDEN = {'-d', '--database', '-i', '--init', '-u', '--update', '--test-tags', '--test-enable', '--stop-after-init'}

def build_command(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--odoo-bin', required=True)
    parser.add_argument('--database', required=True)
    parser.add_argument('--addon', required=True)
    parser.add_argument('--mode', required=True, choices=('install', 'update'))
    parser.add_argument('--ack-test-db', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('extra', nargs=argparse.REMAINDER)
    a = parser.parse_args(argv)
    if not a.ack_test_db: parser.error('Explicit --ack-test-db is required')
    if not NAME.fullmatch(a.database) or len(a.database) > 63: parser.error('Invalid database identifier')
    if not NAME.fullmatch(a.addon): parser.error('Invalid addon technical name')
    if re.search(r'(^|_)(prod|production|live)($|_)', a.database, re.I): parser.error('Production-like database name rejected')
    if not Path(a.odoo_bin).is_file(): parser.error('odoo-bin file does not exist')
    extra = a.extra[1:] if a.extra and a.extra[0] == '--' else a.extra
    for item in extra:
        key = item.split('=', 1)[0]
        if key in FORBIDDEN or any(item.startswith(x) and item != x for x in ('-d', '-i', '-u')):
            parser.error('Conflicting Odoo option: ' + item)
    command = [sys.executable, str(Path(a.odoo_bin).resolve()), '-d', a.database,
               '-i' if a.mode == 'install' else '-u', a.addon,
               '--test-tags=/' + a.addon, '--stop-after-init'] + extra
    return command, a.dry_run

def main(argv=None):
    command, dry = build_command(sys.argv[1:] if argv is None else argv)
    if dry:
        print(subprocess.list2cmdline(command) if sys.platform == 'win32' else __import__('shlex').join(command))
        return 0
    return subprocess.call(command)

if __name__ == '__main__': raise SystemExit(main())
