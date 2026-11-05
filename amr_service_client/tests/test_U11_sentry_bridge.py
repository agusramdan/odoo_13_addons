"""Compatibility adapter for AC selectors; canonical tests live in tests/unit."""
from pathlib import Path

_adapter_file = __file__
_cases = Path(__file__).resolve().parent / "unit" / "test_unit_sentry_bridge.py"
try:
    __file__ = str(_cases)
    exec(compile(_cases.read_bytes(), str(_cases), "exec"), globals())
finally:
    __file__ = _adapter_file
