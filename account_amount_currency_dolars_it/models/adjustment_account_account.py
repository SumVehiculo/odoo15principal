# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api

class AdjustmentAccountAccount(models.Model):
	_name = 'adjustment.account.account'
	
	account_id = fields.Many2one('account.account',string='Cuenta',required=True)
	adjustment_type = fields.Selection([('global','Global'),('documento','Documento')],string='Tipo de ajuste',default='global')
	rate_type = fields.Selection([('sale','Venta'),('purchase','Compra')],string='Tipo de cambio',default='sale')
	company_id = fields.Many2one('res.company',string=u'Compañía',related='account_id.company_id',store=True)

	_sql_constraints = [
		('account_id_uniq', 'unique (account_id)', 'Solo puede haber un registro por cuenta!')
	]