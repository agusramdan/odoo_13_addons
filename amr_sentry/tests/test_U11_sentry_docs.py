"""Legacy adapter for canonical documentation cases."""
from pathlib import Path

_cases = Path(__file__).resolve().parent / "unit" / "test_unit_sentry_docs.py"
exec(compile(_cases.read_bytes(), str(_cases), "exec"), globals())
