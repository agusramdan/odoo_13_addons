"""Compatibility adapter for canonical configuration cases."""
from pathlib import Path

_cases = Path(__file__).resolve().parents[1] / "tests" / "unit" / "test_unit_sentry_config.py"
exec(compile(_cases.read_bytes(), str(_cases), "exec"), globals())
