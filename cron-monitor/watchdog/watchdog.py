import logging
import os
import time
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import requests

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
log = logging.getLogger('cron-watchdog')

DB = dict(host=os.environ['PGHOST'], port=int(os.getenv('PGPORT', '5432')),
          dbname=os.environ['PGDATABASE'], user=os.environ['PGUSER'],
          password=os.environ['PGPASSWORD'], connect_timeout=8,
          options='-c default_transaction_read_only=on -c statement_timeout=10000')
KUMA_CRON = os.environ['KUMA_CRON_PUSH_URL']
KUMA_WATCHDOG = os.environ['KUMA_WATCHDOG_PUSH_URL']
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL_SECONDS', '60'))
STALE_AFTER = int(os.getenv('AUDIT_STALE_MINUTES', '120'))

SQL = """
SELECT c.id, c.cron_name, c.nextcall, c.amr_grace_minutes, c.amr_max_runtime_minutes,
       (EXTRACT(EPOCH FROM ((now() AT TIME ZONE 'UTC') - c.nextcall)) / 60.0) AS overdue_min,
       a.state AS last_state, a.started_at AS last_started,
       a.finished_at AS last_finished,
       (EXTRACT(EPOCH FROM ((now() AT TIME ZONE 'UTC') - a.started_at)) / 60.0) AS age_min
FROM ir_cron c
LEFT JOIN LATERAL (
  SELECT state, started_at, finished_at
  FROM amr_cron_execution
  WHERE cron_id = c.id
  ORDER BY started_at DESC, id DESC LIMIT 1
) a ON true
WHERE c.active AND c.numbercall != 0 AND c.amr_monitor_enabled
ORDER BY c.id
"""


def push(url, status, message):
    # Avoid logging secret push URLs.
    r = requests.get(url, params={'status': status, 'msg': message[:180]}, timeout=10)
    r.raise_for_status()


def check():
    with psycopg2.connect(**DB) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SQL)
            rows = cur.fetchall()
    if not rows:
        return False, 'No enabled monitored cron found'
    failures = []
    tabel = str.maketrans('', '', ';:?/#\'\"\\')
    for row in rows:
        name = str(row['cron_name']).translate(tabel)[:50]
        overdue = float(row['overdue_min'] or 0)
        grace = max(1, int(row['amr_grace_minutes'] or 10))
        runtime = max(1, int(row['amr_max_runtime_minutes'] or 30))
        age = float(row['age_min'] or 0)
        state = row['last_state']
        if state == 'started' and age > runtime:
            failures.append(f'{name}: running/unclosed {age:.0f}m')
        elif overdue > grace and state != 'started':
            failures.append(f'{name}: nextcall overdue {overdue:.0f}m')
        elif state == 'raised':
            failures.append(f'{name}: last callback raised')
        elif state == 'returned' and age > STALE_AFTER and overdue > 0:
            failures.append(f'{name}: last callback {age:.0f}m ago')
    if failures:
        return False, '; '.join(failures[:3]) + (f' (+{len(failures)-3} more)' if len(failures)>3 else '')
    return True, f'{len(rows)} monitored cron(s), no overdue alarms'


def main():
    while True:
        try:
            healthy, msg = check()
            log.info('cron_health=%s %s', healthy, msg)
            push(KUMA_CRON, 'up' if healthy else 'down', msg)
            push(KUMA_WATCHDOG, 'up', 'watchdog cycle completed')
        except Exception as exc:
            log.exception('watchdog cycle failed')
            try:
                push(KUMA_CRON, 'down', 'watchdog check failed: ' + type(exc).__name__)
            except Exception:
                log.exception('cannot push cron status')
            # Do not send watchdog UP on a failed cycle. Its push monitor will time out.
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
