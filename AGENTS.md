## Project context
You are an expert Odoo developer. This project contains Odoo custom modules
(addons). Always follow Odoo's framework conventions. Never work around them.

## Indentation

- Use 4 spaces per indentation level for source code and XML; do not use tabs for indentation.
- Apply this to new files and changed sections; do not reformat unrelated files outside the task scope.

## Odoo Rules

- Target Odoo 13, Python 3.7.3
- Follow standard OCA
- Using _inherit
- Avoid monkey patch
- Business Logic forbiden in Controller
- All model has access rule

## Error handling
- Raise `odoo.exceptions.UserError` for user-facing errors.
- Raise `odoo.exceptions.ValidationError` from `@api.constrains`.
- Raise `odoo.exceptions.AccessError` when manually checking access rights.
- Never let exceptions bubble uncaught from public methods.

## Document
- Document write in `<addon>/docs`
- PRD write in `docs/<tasknumber>`
- UAT write in `docs/<tasknumber>`
