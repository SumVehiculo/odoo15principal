# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountBatchPayment(models.Model):
	_inherit = 'account.batch.payment'

	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	glosa = fields.Char(string='Glosa')