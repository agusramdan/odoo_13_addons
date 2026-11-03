"""Compatibility adapter for canonical unit cases."""
from pathlib import Path

_cases = Path(__file__).resolve().parents[1] / "tests" / "unit" / "test_unit_sentry_model.py"
exec(compile(_cases.read_bytes(), str(_cases), "exec"), globals())
