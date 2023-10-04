# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrTypeDocument(models.Model):
	_name = 'hr.type.document'
	_description = 'Type Document'

	sunat_code = fields.Char(string='Codigo SUNAT')
	afp_code = fields.Char(string='Codigo AFP')
	description = fields.Char(string='Descripcion')
	name = fields.Char(string='Abreviacion')