# Access rights

- Every model needs a record in `<addon>/security/ir.model.access.csv`.
- CSV columns in order: `id,name,model_id:id,group_id:id,perm_read,perm_write,
  perm_create,perm_unlink`.
- `model_id:id` format: `model_project_resource_booking` (replace dots with
  underscores, prefix with `model_`).
- For public read access, use `base.group_user` as the group.
- For admin-only write, use `base.group_system`.
- Use `ir.rule` records for row-level security (multicompany, owner-only).

- Multi-company models need a group-less restriction row with a company
  domain: `"[('company_id', 'in', company_ids)]"` (`company_ids` evaluates to
  the user's allowed companies; append `+ [False]` when the company is
  optional).

For auditing beyond the data files (`sudo()`, SQL, public methods, ...), use the
`odoo-security` skill.
