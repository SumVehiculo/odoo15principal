# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	analytic_tag_ids = fields.Many2many('account.analytic.tag','contract_analytic_tag_rel', 'contract_id', 'analytic_tag_id', string='Etiqueta Analitca')