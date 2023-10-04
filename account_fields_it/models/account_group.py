# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountGroup(models.Model):
	_inherit = 'account.group'

	type = fields.Selection([
							('0','Balance'),
							('1','Subcuenta')
							],string='Tipo')
	clasification_sheet = fields.Selection([
											('0',u'Situación Financiera'),
											('1','Resultados por Naturaleza'),
											('2','Resultados por Función'),
											('3','Resultados'),
											('4','Cuenta de Orden'),
											('5','Cuenta de Mayor')
											],string=u'Clasificación Hoja de Trabajo')