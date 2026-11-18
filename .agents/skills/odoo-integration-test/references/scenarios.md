# Scenarios

* Model: create records through ORM; assert persistence, computed values, constraints and relations; test access rights using a test user and `with_user` only if present in your Odoo 13 target, otherwise use `sudo(user)`.
* Wizard: create a transient record and invoke its action; assert the resulting persistent records.
* Workflow: create the actual business records and validate state transitions and denied transitions with appropriate users.
* Cron: invoke the actual cron method against controlled fixtures, assert effects and idempotency where expected. Do not rely on a wall-clock scheduler.
* Controller: use `HttpCase`, controlled authentication and `@tagged('-at_install', 'post_install')`; never expose live endpoints or secrets. Browser tests have additional dependencies.
* External API: patch the HTTP client where the addon looks it up; use fake responses. Assert request content and failure handling. Never call live payment, email, or other external services.

`TransactionCase` isolates each method with rollback. `SavepointCase` shares setup and rolls individual tests back to savepoints; avoid persistent changes outside that lifecycle. These do not undo module installation, commits, external calls, filesystem changes, or other processes. See [Odoo 13 testing](https://www.odoo.com/documentation/13.0/developer/reference/addons/testing.html).
