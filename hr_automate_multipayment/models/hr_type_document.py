# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrTypeDocument(models.Model):
	_inherit = 'hr.type.document'

	bbva_code = fields.Char(string='Codigo BBVA')
	bcp_code = fields.Char(string='Codigo BCP')
	interbank_code = fields.Char(string='Codigo Interbank')
	banbif_code = fields.Char(string='Codigo BanBif')