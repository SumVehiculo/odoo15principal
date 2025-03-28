# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	use_balance_inventory_kardex = fields.Boolean(string='Usar Kardex',default=False)
	catalog_fs_bi = fields.Selection([
		('01', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - SECTOR DIVERSAS - INDIVIDUAL'),
		('02', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - SECTOR SEGUROS - INDIVIDUAL'),
		('03', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - SECTOR BANCOS Y FINANCIERAS - INDIVIDUAL'),
		('04', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - ADMINISTRADORAS DE FONDOS DE PENSIONES (AFP)'),
		('05', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - AGENTES DE INTERMEDIACIÓN'),
		('06', 'SUPERINTENDENCIA DEL MERCADO DE VALores - FONDOS DE INVERSIÓN'),
		('07', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - PATRIMONIO EN FIDEICOMISOS'),
		('08', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - ICLV'),
		('09', 'OTROS NO CONSIDERADOS EN LOS ANTERIORES')
	], string=u'Catálogo de Estados Financieros')
