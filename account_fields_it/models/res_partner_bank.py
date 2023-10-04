# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	is_detraction_account = fields.Boolean(string=u'Es Cuenta de Detracciones',default=False)