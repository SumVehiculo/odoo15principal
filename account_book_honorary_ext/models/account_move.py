# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	honorary_type = fields.Selection([
		('R', 'Recibo por Honorario'),
		('N', u'Nota de Crédito'),
		('D', 'Dieta'),
		('O', 'Otro Comprobante')
	], default='R', string='Tipo Recibos de Honorarios')