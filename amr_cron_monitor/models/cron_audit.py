import logging
import time
from datetime import datetime

from odoo import api, fields, models, registry

_logger = logging.getLogger(__name__)


class CronExecution(models.Model):
    _name = 'amr.cron.execution'
    _description = 'Cron Execution Audit'
    _order = 'started_at desc, id desc'

    cron_id = fields.Many2one('ir.cron', string='Cron', index=True, ondelete='set null', readonly=True)
    cron_name = fields.Char(readonly=True)
    started_at = fields.Datetime(readonly=True, index=True)
    finished_at = fields.Datetime(readonly=True)
    state = fields.Selection([
        ('started', 'Started'),
        ('returned', 'Returned (not necessarily successful)'),
        ('raised', 'Raised exception'),
    ], readonly=True, index=True)
    duration_seconds = fields.Float(readonly=True)
    error_message = fields.Text(readonly=True)


class IrCron(models.Model):
    _inherit = 'ir.cron'

    amr_monitor_enabled = fields.Boolean(string='Monitor Cron', default=False)
    amr_grace_minutes = fields.Integer(string='Allowed Delay (min)', default=60)
    amr_max_runtime_minutes = fields.Integer(string='Max Runtime (min)', default=30)

    @api.model
    def _amr_write_audit(self, values, audit_id=None):
        # Independent transaction ensures STARTED survives a rollback in the job transaction.
        # Never allow audit failure to prevent the business cron from executing.
        try:
            with registry(self.env.cr.dbname).cursor() as cr:
                audit_env = api.Environment(cr, 1, {})
                audit_model = audit_env['amr.cron.execution']
                if audit_id:
                    audit_model.browse(audit_id).write(values)
                    result = audit_id
                else:
                    result = audit_model.create(values).id
                cr.commit()
                return result
        except Exception:
            _logger.exception('AMR cron audit write failed')
            return None

    @api.model
    def _callback(self, *args, **kwargs):
        # Odoo 13's standard signature is (model_name, method_name, args, job_id).
        # Verify against the exact deployed Odoo 13 patch/fork before production.
        job_id = kwargs.get('job_id')
        if job_id is None and len(args) >= 4:
            job_id = args[3]
        cron = self.browse(job_id).exists() if job_id else self.browse()
        if not cron or not cron.amr_monitor_enabled:
            return super(IrCron, self)._callback(*args, **kwargs)

        started = datetime.utcnow()
        tick = time.monotonic()
        audit_id = self._amr_write_audit({
            'cron_id': cron.id,
            'cron_name': cron.name,
            'started_at': fields.Datetime.to_string(started),
            'state': 'started',
        })
        try:
            result = super(IrCron, self)._callback(*args, **kwargs)
        except BaseException as exc:
            if audit_id:
                self._amr_write_audit({
                    'finished_at': fields.Datetime.now(),
                    'state': 'raised',
                    'duration_seconds': time.monotonic() - tick,
                    'error_message': str(exc)[:2000],
                }, audit_id)
            raise
        else:
            if audit_id:
                self._amr_write_audit({
                    'finished_at': fields.Datetime.now(),
                    'state': 'returned',
                    'duration_seconds': time.monotonic() - tick,
                }, audit_id)
            return result
