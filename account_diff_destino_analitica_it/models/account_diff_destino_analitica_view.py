# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountDiffDestinoAnaliticaView(models.Model):
	_name = 'account.diff.destino.analitica.view'
	_description = 'Account Diff Destino Analitica View'
	_auto = False
	
	aml_id = fields.Integer(string='AML ID')
	am_id = fields.Integer(string='AM ID')
	fecha = fields.Date(string='Fecha')
	diario = fields.Char(string='Diario')
	asiento = fields.Char(string='Asiento')
	cuenta = fields.Char(string='Cuenta')
	monto_conta = fields.Float(string='Monto En Contabilidad',digits=(12,2))
	monto_analiticas = fields.Float(string='Monto En Analitica',digits=(12,2))
	diferencia = fields.Float(string='Diferencia',digits=(12,2))