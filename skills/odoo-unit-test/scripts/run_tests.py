#!/usr/bin/env python3
import sys
from pathlib import Path
from isolation import install, self_check

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
install()
self_check()
try:
    import pytest
except ImportError:
    print('pytest is required: python -m pip install -r requirements.txt', file=sys.stderr)
    raise SystemExit(2)
args = sys.argv[1:]
if args and args[0] == '--': args = args[1:]
if args and args[0] == '--addon':
    if len(args) != 2:
        print('Usage: run_tests.py --addon PATH_TO_ADDON', file=sys.stderr)
        raise SystemExit(2)
    unit = Path(args[1]).resolve() / 'tests' / 'unit'
    if not unit.is_dir():
        print('Unit test directory does not exist: ' + str(unit), file=sys.stderr)
        raise SystemExit(2)
    args = ['--import-mode=importlib', '--rootdir=' + str(unit), '--confcutdir=' + str(unit), str(unit)]
elif not args:
    args = ['--ignore=' + str(ROOT / 'examples' / 'sample_addon'), str(ROOT / 'examples')]
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider'] + args))
