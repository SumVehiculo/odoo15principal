from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAsset(models.Model):
	_inherit = 'account.asset'

	invoice_id_it = fields.Many2one('account.move', string='Factura', copy=False)
	partner_id = fields.Many2one('res.partner', string='Socio')