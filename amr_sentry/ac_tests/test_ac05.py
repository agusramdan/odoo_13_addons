"""AC-05: no sufficient oracle; never a green empty suite."""
import sys
REASON = 'Real SDK logging/unhandled isolation and outside-telemetry oracle unavailable'
if __name__ == '__main__':
    print('NOT RUN: ' + REASON)
    sys.exit(2)
def load_tests(loader, tests, pattern):
    raise RuntimeError('NOT RUN: ' + REASON)
