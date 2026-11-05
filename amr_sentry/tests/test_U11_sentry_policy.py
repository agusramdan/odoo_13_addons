"""Legacy selector; execute the canonical unit cases under the old module name."""
from pathlib import Path
_cases = Path(__file__).resolve().parent / "unit" / "test_unit_sentry_policy.py"
exec(compile(_cases.read_bytes(), str(_cases), "exec"), globals())
