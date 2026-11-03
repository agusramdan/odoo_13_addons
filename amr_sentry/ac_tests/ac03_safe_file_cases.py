"""Compatibility adapter for canonical safe-file cases."""
from pathlib import Path

_cases = Path(__file__).resolve().parents[1] / "tests" / "unit" / "test_unit_sentry_safe_file.py"
exec(compile(_cases.read_bytes(), str(_cases), "exec"), globals())
