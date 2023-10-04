# -*- encoding: utf-8 -*-
from odoo import fields, models, _

class ResCompany(models.Model):
	_inherit = 'res.company'

	logistic_picking_done_restrict = fields.Boolean(string='Picking Done Restriction')
