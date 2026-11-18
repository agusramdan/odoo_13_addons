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
coverage_enabled = '--coverage' in args
if coverage_enabled:
    args.remove('--coverage')
coverage_min = 70
if '--coverage-min' in args:
    index = args.index('--coverage-min')
    try:
        coverage_min = float(args[index + 1])
    except (IndexError, ValueError):
        print('Usage: --coverage-min PERCENT', file=sys.stderr)
        raise SystemExit(2)
    if not 0 <= coverage_min <= 100:
        print('Coverage minimum must be between 0 and 100', file=sys.stderr)
        raise SystemExit(2)
    del args[index:index + 2]
if args and args[0] == '--': args = args[1:]
addon = None
if args and args[0] == '--addon':
    if len(args) != 2:
        print('Usage: run_tests.py [--coverage] [--coverage-min PERCENT] --addon PATH_TO_ADDON', file=sys.stderr)
        raise SystemExit(2)
    addon = Path(args[1]).resolve()
    unit = addon / 'tests' / 'unit'
    if not unit.is_dir():
        print('Unit test directory does not exist: ' + str(unit), file=sys.stderr)
        raise SystemExit(2)
    args = ['--import-mode=importlib', '--rootdir=' + str(unit), '--confcutdir=' + str(unit), str(unit)]
elif coverage_enabled:
    print('--coverage requires --addon PATH_TO_ADDON', file=sys.stderr)
    raise SystemExit(2)
elif not args:
    args = ['--ignore=' + str(ROOT / 'examples' / 'sample_addon'), str(ROOT / 'examples')]

coverage_run = None
if coverage_enabled:
    try:
        from importlib import import_module
        coverage_module = import_module('coverage')
    except ImportError:
        print('coverage package is required in the verified test image', file=sys.stderr)
        raise SystemExit(2)
    coverage_run = coverage_module.Coverage(data_file='/dev/shm/odoo-unit-test-coverage', source=[str(addon)], omit=['*/tests/*', '*/__pycache__/*'])
    coverage_run.start()
test_result = pytest.main(['-q', '-p', 'no:cacheprovider'] + args)
if coverage_run:
    coverage_run.stop()
    coverage_run.save()
    total = coverage_run.report(show_missing=True)
    if test_result == 0 and total < coverage_min:
        test_result = 1
raise SystemExit(test_result)
