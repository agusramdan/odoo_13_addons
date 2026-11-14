-- Run as PostgreSQL administrator. Replace password before execution.
CREATE ROLE cron_monitor_ro LOGIN PASSWORD 'CHANGE_ME';
GRANT CONNECT ON DATABASE odoo13 TO cron_monitor_ro;
-- Connect to the Odoo database before running the following grants.
GRANT USAGE ON SCHEMA public TO cron_monitor_ro;
GRANT SELECT ON TABLE ir_cron, amr_cron_execution TO cron_monitor_ro;
-- Re-run SELECT grants after addon upgrade if tables are recreated.
