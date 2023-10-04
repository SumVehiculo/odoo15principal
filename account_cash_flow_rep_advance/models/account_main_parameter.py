# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MainParameter(models.Model):
	_inherit = 'account.main.parameter'

	use_counterpart_cash_flow = fields.Boolean(string='Usar Flujo de Caja en Contrapartida', default=False)