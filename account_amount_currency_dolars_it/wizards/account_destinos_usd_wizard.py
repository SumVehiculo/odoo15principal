# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO

import base64

class AccountDestinosUsdWizard(models.TransientModel):
	_name = 'account.destinos.usd.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	def get_fiscal_year(self):
		fiscal_year = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).fiscal_year
		return fiscal_year.id if fiscal_year else None

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())
	period_id = fields.Many2one('account.period',string='Periodo')
	journal_id = fields.Many2one('account.journal',string='Diario',required=True)
	date = fields.Date(string='Fecha',required=True)
	glosa = fields.Char(string='Glosa',required=True)

	def do_moves(self):
		m = self.env['account.move'].search([('ref','=','DEST-'+self.period_id.code+' USD'),('company_id','=',self.company_id.id)],limit=1)
		if m:
			if m.state =='posted':
				m.button_cancel()
			m.line_ids.unlink()
			m.name = "/"
			m.unlink()

		self.env.cr.execute("""select T.*, aa.id as account_id FROM (
							select a1.des_debe as cuenta,sum(a2.amount_c) as amount_c from get_destinos('{period}',{company_id})  a1
							left join account_move_line a2 on a2.id=a1.aml_id
							group by a1.des_debe
							union all
							select a1.des_haber as cuenta, -sum(a2.amount_c) as amount_c from get_destinos('{period}',{company_id})  a1
							left join account_move_line a2 on a2.id=a1.aml_id
							group by a1.des_haber)T
							left join (select * from account_account where company_id={company_id}) aa on aa.code = T.cuenta 
							where aa.deprecated <> TRUE
							""".format(
			company_id = self.company_id.id,
			period = self.period_id.code))
		res = self.env.cr.dictfetchall()
		lineas = []

		for elemnt in res:
			vals = (0,0,{
				'name': self.glosa,
				'debit': 0,
				'credit': 0, 
				'amount_c': elemnt['amount_c'], 
				'date': self.date,
				'account_id': elemnt['account_id'],
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		
		asiento = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.date,
			'glosa': self.glosa,
			'ref': 'DEST-'+self.period_id.code+' USD', 
			'line_ids':lineas})

		asiento.post()
		
		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': asiento.id,
		}