from odoo import api, fields, models, http
from odoo.exceptions import UserError

class Order(models.Model):
    name = fields.Char()
    @api.multi
    def action_approve(self):
        if self.amount <= 0: raise UserError('Amount must be positive')
        self.state = 'approved'
    @api.model
    def cron_expire(self):
        return self.env['sale.order'].search([('state', '=', 'draft')]).write({'state': 'expired'})

class ApprovalWizard(models.TransientModel):
    def action_confirm(self):
        self.env['sale.order'].browse(self.order_id).write({'state': 'approved'})

class OrderController(http.Controller):
    @http.route('/order/status', type='json', auth='user')
    def status(self, order): return {'state': order.state}
