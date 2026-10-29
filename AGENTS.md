## Project context
You are an expert Odoo developer. This project contains Odoo custom modules
(addons). Always follow Odoo's framework conventions. Never work around them.

## Odoo Rules

- Target Odoo 13
- Follow standard OCA
- Using _inherit
- Avoid monkey patch
- Business Logic forbiden in Controller
- All model has access rule

## Python / ORM rules
- Traget Python 3.7
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

## Model conventions
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

## Field naming
- Boolean fields: prefix with `is_` or `has_` (e.g. `is_active`, `has_attachment`).
- Many2one fields: end with `_id` (e.g. `partner_id`, `project_id`).
- One2many fields: end with `_ids` (e.g. `line_ids`, `booking_ids`).
- Many2many fields: end with `_ids` (e.g. `tag_ids`, `user_ids`).
- Date fields: end with `_date` (e.g. `start_date`, `end_date`).
- Computed fields: name describes the output (e.g. `total_amount`, `duration_hours`).

## Manifest format
- `__manifest__.py` keys in this order: `name`, `version`, `category`,
  `summary`, `description`, `author`, `website`, `license`, `depends`,
  `data`, `demo`, `assets`, `installable`, `auto_install`, `application`.
- `version`: always `"13.0.1.0.0"` format (Odoo major + module semver).
- `license`: default to `"LGPL-3"` unless told otherwise.
- `depends`: list base dependencies, never over-include. `base` is implicit in
  most cases; only add if you actually use models from it directly.

## XML / Views
- XML `id` attributes: `module_name.view_model_name_type`
  (e.g. `my_module.view_project_resource_booking_form`).
- Always wrap views in `<odoo><data>` tags.
- Use `<field name="arch" type="xml">` inside `ir.ui.view` records.
- Form views: `<form string="...">` at root, group fields logically with
  `<group>` and `<group col="2">`.
- Tree/list views: include only the key fields needed at-a-glance (5-8 max).
- Kanban views: use `<templates><t t-name="kanban-card">` structure.
- Never hardcode record IDs in XML. Always use `ref()` or `%(xml_id)s`.
- Menu items: follow parent > category > action chain.

## Security
- Every model needs a record in `<addon>/security/ir.model.access.csv`.
- CSV columns in order: `id,name,model_id:id,group_id:id,perm_read,perm_write,
  perm_create,perm_unlink`.
- `model_id:id` format: `model_project_resource_booking` (replace dots with
  underscores, prefix with `model_`).
- For public read access, use `base.group_user` as the group.
- For admin-only write, use `base.group_system`.
- Use `ir.rule` records for row-level security (multicompany, owner-only).

## Error handling
- Raise `odoo.exceptions.UserError` for user-facing errors.
- Raise `odoo.exceptions.ValidationError` from `@api.constrains`.
- Raise `odoo.exceptions.AccessError` when manually checking access rights.
- Never let exceptions bubble uncaught from public methods.

## Unit Testing (TDD)
- Test files live in `<addon>/tests/test_*.py`.
- Assert using `assertEqual`, `assertTrue`, `assertRaises`. Not raw `assert`.

## Integration Testing
This covers the main failure modes when Cursor generates Odoo code without guidance: raw SQL where ORM should be used, wrong field naming, missing _description, malformed XML IDs, and security CSV with wrong column order. Save it, open Cursor, and from this point forward every completion in this workspace follows Odoo conventions.
- Test files live in `<addon>/integration_tests/test_*.py`.
- Test classes inherit `TransactionCase` (or `SavepointCase` for Odoo <16).
- Use `self.env['model'].create({...})` to set up test data, not fixtures.

## Document
- Document write in `<addon>/docs`
- PRD write in `docs/<tasknumber>`
- UAT write in `docs/<tasknumber>`
