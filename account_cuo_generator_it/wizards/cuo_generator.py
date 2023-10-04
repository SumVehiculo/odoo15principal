# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date

class CuoGenerator(models.TransientModel):
	_name = 'cuo.generator'
	_description = 'Cuo Generator'

	period_id = fields.Many2one('account.period',string='Periodo')

	def generate_cuos(self):
		if not self.period_id:
			raise UserError('El Periodo es un campo Obligatorio')
		sql = """UPDATE account_move_line SET cuo = T.id from (
		select aml.id from account_move_line aml
		left join account_move am on am.id = aml.move_id
		where (am.date between '%s' and '%s') and am.company_id = %d and (aml.cuo is null or aml.cuo = 0))T 
		where account_move_line.id = T.id""" % (self.period_id.date_start.strftime('%Y/%m/%d'),
			self.period_id.date_end.strftime('%Y/%m/%d'), self.env.company.id)
		self.env.cr.execute(sql)
		return self.env['popup.it'].get_message('Se termino de Generar los CUOs en las lineas contables :)')