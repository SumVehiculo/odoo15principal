# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MainParameter(models.Model):
	_inherit = 'main.parameter'
	
	use_balance_inventory_kardex = fields.Boolean(string='Usar Kardex',default=False)
	catalog_fs_bi = fields.Char(string=u'Catálogo de Estados Financieros')
