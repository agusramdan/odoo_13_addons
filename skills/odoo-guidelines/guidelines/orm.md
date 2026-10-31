# Recordsets, domains and context

- Use recordset methods (`filtered`, `grouped`, `mapped`, `sorted`) where they
  read better than a loop.
- Recordsets/collections are booleans: write `if records:` / `if some_list:`,
  not `if len(...)`.
- Don't read a non-relational field on a multi-record set (it raises); iterate
  or `mapped`. Conversely, guard single-record assumptions with `ensure_one()`.
- Combine domains with `odoo.fields.Domain`: the `&`, `|`, `~` operators for
  domains written inline, `Domain.AND`/`Domain.OR` for a list of domains you
  already hold. Never hand-build `'&'`/`'|'` prefix-notation lists.
- Propagate context with `with_context(...)` (it's a frozendict, immutable);
  name custom context keys carefully and prefix module-specific ones (a stray
  `default_<field>` in context leaks into unrelated `create` calls).
- Delegation inheritance (`_inherits`) inherits fields but **not** methods; avoid
  it where you can (chained `_inherits` is unsupported).

# Computes, onchange and constraints

- `create` must accept a list of vals (`@api.model_create_multi`); don't call
  `create` per record in a loop (see [Batch ORM calls](performance.md#batch-orm-calls)).
- `@api.depends` must list **every** field the compute reads; stored computes
  need correct dependencies and no side effects.
- `@api.onchange` is UI-only: never rely on it for data integrity; enforce
  invariants with `@api.constrains` or SQL constraints declared as model
  attributes (`_x_check = models.Constraint("CHECK (...)", "msg")`; the
  attribute name must start with `_`). Indexes are declared the same way
  (`_x_index = models.Index(...)`, `models.UniqueIndex(...)`). Flag
  `_sql_constraints`: on master it is **ignored** with a log warning, the
  constraint is never created.

# Methods and extension points

- Methods are private (`_` prefix) by default. A public name is an RPC entry
  point: make one only when it must be callable from outside, and decorate
  with `@api.private` a public name that must not be exposed.
- Logic that another module actually overrides goes in its own small method
  (`self._get_partner_domain()`); other modules extend methods, not lines.
  Don't pre-split for extension points that don't exist yet.
- Don't use `odoo.http.request` in models: it is absent in crons, RPC, tests
  and the shell. Pass what the model needs in from the controller.

# Transactions and exceptions

- **Never** call `cr.commit()` / `cr.rollback()` unless you opened your own
  cursor; the framework owns the transaction. Any unavoidable commit needs an
  explicit comment justifying it.
- Catch **specific** exceptions over the smallest possible block; let unexpected
  ones propagate to the framework. To recover from framework exceptions, wrap the
  work in `with self.env.cr.savepoint():` (note: >64 savepoints per transaction
  degrades PostgreSQL, so bound batch sizes).

# Model conventions

- Use Odoo ORM methods exclusively. Never write raw SQL unless the task is
  explicitly a SQL report or performance-critical batch operation with a comment
  explaining why ORM is insufficient.
- Use `self.env['model.name']` to access other models, not direct class imports.
- Use `self.env.ref('module.xml_id')` to resolve external IDs.
- Computed fields must declare `compute='_compute_field_name'` and, if stored,
  `store=True`. Always define `depends` via `@api.depends`.
- Inverse fields must declare `inverse='_inverse_field_name'`.
- Constrain methods use `@api.constrains` and raise `ValidationError`, never
  `AssertionError`.
- Onchange methods use `@api.onchange` and return warning dicts when needed.
- Never use `cr.execute` or `self._cr.execute` unless inside a method clearly
  marked with `# SQL: required for performance`.
- Use `sudo()` sparingly. If you use it, add a comment explaining the privilege
  escalation: `# sudo: bypass record rules for background scheduler`.
- `fields.Date.today()` and `fields.Datetime.now()`. Never use Python's `datetime`
  directly in field defaults unless converting to Odoo format.
- Class name: PascalCase matching the model name (e.g. `ProjectResourceBooking`
  for `project.resource.booking`).
- `_name`: dotted lowercase (e.g. `project.resource.booking`).
- `_description`: human-readable string, always present.
- `_inherit` for extension, `_inherits` only for delegation inheritance (rare).
- Distinguish Python class inheritance from Odoo ORM model inheritance. Do not
  assume subclassing a Python class derived from `models.AbstractModel` alone
  creates a concrete persisted model or correctly registers ORM inheritance.
- When creating a new concrete model from an abstract ORM mixin, declare the
  class on `models.Model` and set both `_name` and `_inherit` to the Odoo model
  names explicitly. Example:
  ```python
  class AmrResourceUserMapping(models.Model):
      _name = 'oidc.issuer.user.mapping'
      _inherit = 'amr.resource.registry.access'
  ```
  Do not replace `_inherit` with Python syntax such as
  `class AmrResourceUserMapping(RegistryAccess)` as the sole inheritance
  declaration. Preserve `_description`, `_rec_name`, fields, and methods.
- For an in-place extension of an existing Odoo model, set `_inherit` without
  `_name`; for a new concrete model based on an abstract mixin, use `_name` and
  `_inherit` together. Use `models.AbstractModel` for an abstract reusable
  mixin, not a persisted concrete model.
- Verify model inheritance in the live Odoo registry: inspect `_name`,
  `_inherit`, `_abstract`, `_auto`, and `_table`, then verify the physical table
  exists and ORM operations work in a fresh isolated database. Source-level
  checks and offline tests alone do not prove registry registration or table
  creation.
- Field order: `_name`, `_description`, `_inherit`, `_order`, then fields
  grouped by type (Char/Int/Float > Date/Datetime > Many2one > One2many >
  Many2many > computed), then methods ordered: CRUD overrides, compute,
  inverse, constrains, onchange, action methods.
- `name` field should be the primary display field; include `_rec_name = 'name'`
  if the display field has a different name.
