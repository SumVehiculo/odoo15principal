# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date
import calendar

class CodeSunatUpdate(models.TransientModel):
	_name = "code.sunat.update"

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	nivel = fields.Integer(string='Nivel',required=True)

	def generate(self):
		code_sunat = self.env['account.code.sunat.table'].search([])
		for c in range(2,self.nivel+1):
			codes = code_sunat.filtered(lambda l: len(l.name) == c )
			for code in codes:
				self.env.cr.execute("""UPDATE account_account SET code_sunat = '{code_sunat}' where LEFT(code,{nivel}) = '{code_sunat}' and company_id = {company_id}""".format(
					nivel = c,
					code_sunat = code.name,
					company_id = self.company_id.id,
				))

		return self.env['popup.it'].get_message('SE ACTUALIZÓ CORRECTAMENTE EL PLAN DE CODIGO SUNAT.')