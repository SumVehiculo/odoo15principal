# -*- coding: utf-8 -*-
from odoo import models, fields
class CompanyBranchAddress(models.Model):
	_inherit = 'res.company.branch.address'

	address_external_id = fields.Char(string='Address external UUID', copy=False)