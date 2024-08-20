# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TypeOperationKardex(models.Model):
	_inherit = 'type.operation.kardex'
	
	account_id = fields.Many2one('account.account',string=u'Cuenta',company_dependent=True, domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]")
	category_account = fields.Boolean(string=u'Usar cuenta Categoria',default=False)