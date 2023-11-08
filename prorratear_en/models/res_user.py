# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class LandedCostIt(models.Model):
	_inherit = 'landed.cost.it'

	prorratear_en = fields.Selection([('cantidad', ''), ('valor', 'Por Valor')],string='Prorratear en funcion', required=True, default='valor')
