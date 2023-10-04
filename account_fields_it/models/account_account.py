# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAccount(models.Model):
	_inherit = 'account.account'

	m_close = fields.Selection([
								('1','Costo de Ventas'),
								('2','Cierre Clase 9'),
								('3','Cierre Cuentas Resultados'),
								('4','Cierre de Activo y Pasivo')
								],string='Metodo de cierre')
	account_close_id = fields.Many2one('account.account',string='Cuenta de Cierre')
	account_type_it_id = fields.Many2one('account.type.it',string='Tipo Estado Financiero')
	account_type_cash_id = fields.Many2one('account.efective.type',string='Tipo Flujo de Efectivo')
	patrimony_id = fields.Many2one('account.patrimony.type',string='Tipo Patrimonio Neto')
	type_adquisition = fields.Selection([
										('1','Mercaderia'),
										('2','Activo Fijo'),
										('3','Otros Activo'),
										('4','Gastos de Educacion, Recreacion, Salud, Mantenimiento de Activos'),
										('5','Otros no Incluidos en 4')
										],string='Tipo de Adquisicion')
	check_moorage = fields.Boolean(string='Tiene destino', default=False)
	a_debit = fields.Many2one('account.account',string='Amarre al Debe')
	a_credit = fields.Many2one('account.account',string='Amarre al Haber')
	is_document_an = fields.Boolean(string='Tiene Analisis por Documento', default=False)
	financial_entity = fields.Char(string='Entidad Financiera',size=100)
	code_sunat = fields.Char(string='Codigo Sunat',size=20)
	code_bank = fields.Char(string='Codigo Banco',size=6)
	account_number = fields.Char(string='Numero de Cuenta',size=50)
	clasification_sheet = fields.Selection([
											('0',u'Situación Financiera'),
											('1','Resultados por Naturaleza'),
											('2','Resultados por Función'),
											('3','Resultados'),
											('4','Cuenta de Orden'),
											('5','Cuenta de Mayor')
											],string=u'Clasificación Hoja de Trabajo')
	dif_cambio_type = fields.Selection([('global','Global'),('doc','Por Documento')],default='global',string='Tipo Diferencia de Cambio')