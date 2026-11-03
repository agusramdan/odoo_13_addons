"""Synthetic controls of the verdict gate; not product tests."""
import contextlib
import io
import unittest
from focused_support import execute

class Probe(unittest.TestCase):
    def test_ok(self):
        pass

    @unittest.skip('synthetic skip')
    def test_skip(self):
        pass

    @unittest.expectedFailure
    def test_expected_failure(self):
        self.fail('synthetic expected failure')

    @unittest.expectedFailure
    def test_unexpected_success(self):
        pass

for label, selector, expected, wanted in [
    ('positive', '__main__.Probe.test_ok', 1, 0),
    ('mismatch', '__main__.Probe.test_ok', 2, 1),
    ('skip', '__main__.Probe.test_skip', 1, 1),
    ('expected failure', '__main__.Probe.test_expected_failure', 1, 1),
    ('unexpected success', '__main__.Probe.test_unexpected_success', 1, 1),
    ('missing', '__main__.Probe.no_such_test', 1, 1),
]:
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        try:
            execute([selector], expected)
        except SystemExit as exc:
            code = exc.code
    print(label, 'exit', code, 'expected', wanted)
    print(captured.getvalue())
    assert code == wanted

captured = io.StringIO()
code = None
with contextlib.redirect_stdout(captured):
    try:
        execute(['__main__.Probe.test_ok', '__main__.Probe.test_ok'], 2)
    except SystemExit as exc:
        code = exc.code
print('duplicate exit', code, 'expected 1')
assert code == 1
