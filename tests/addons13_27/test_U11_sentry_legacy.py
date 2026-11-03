"""Legacy offline selector: discover the canonical addon-owned U11 tests."""
from pathlib import Path
import sys
import unittest


def load_tests(loader, tests, pattern):
    root = Path(__file__).resolve().parents[2]
    sentry = str(root / 'amr_sentry' / 'tests')
    core = str(root / 'amr_service_client' / 'tests')
    paths = sys.path[:]
    names = ('requests', 'requests.exceptions', 'jwt')
    missing = object()
    saved = {name: sys.modules.get(name, missing) for name in names}
    try:
        for directory in (sentry, core):
            if directory not in sys.path:
                sys.path.insert(0, directory)
        suite = unittest.TestSuite()
        for directory in (sentry, core):
            # Enumerate only the legacy selector's top-level files. Generic
            # discovery imports every package, including Odoo integration tests.
            for path in sorted(Path(directory).glob('test_U11_sentry_*.py')):
                suite.addTests(unittest.TestLoader().loadTestsFromName(path.stem))
        return suite
    finally:
        sys.path[:] = paths
        for name, module in saved.items():
            if module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
