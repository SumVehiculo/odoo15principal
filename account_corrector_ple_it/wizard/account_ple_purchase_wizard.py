# -- coding: utf-8 --

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPlePurchaseFix(models.TransientModel):
	_name = 'account.ple.purchase.wizard'
	_description = 'Account Ple Purchase Wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):
		sql = """
			CREATE OR REPLACE view account_ple_purchase_book as (%s)""" % (
				self._get_sql()
			)

		self.env.cr.execute(sql)

		return {
			'name': 'Corrector PLE Compras',
			'type': 'ir.actions.act_window',
			'res_model': 'account.ple.purchase.book',
			'view_mode': 'tree',
			'view_type': 'form',
		}

	def _get_sql(self):
		sql = """
			select row_number() OVER () AS id, t.* from (
			select a1.periodo::character varying,a1.fecha_cont,a1.libro,a1.fecha_e,a1.td,a1.serie,a1.numero,a2.campo_41_purchase as estado,
			case when a1.td in ('03','10','02') or a1.partner_id = (select cancelation_partner from account_main_parameter where company_id = %d) or (a1.cng = a1.total and a1.total <> 0) then '0'
				else (case when a1.fecha_e < (to_char((a1.fecha_cont::timestamp - '1 year'::interval)::timestamp with time zone, 'yyyy/mm'::text) || '/01')::date
					 then '7'
					 else (case when to_char(a1.fecha_e::timestamp with time zone, 'yyyymm'::text)::integer < to_char(a1.fecha_cont::timestamp with time zone, 'yyyymm'::text)::integer then '6' else '1' end)
					  end)
			end as estado_c,
			a1.am_id
			from get_compras_1_1('%s','%s',%d,'pen') a1
			left join account_move a2 on a2.id = a1.am_id) t
			where t.estado<>t.estado_c
		""" % (self.company_id.id,self.period.date_start.strftime('%Y/%m/%d'),self.period.date_end.strftime('%Y/%m/%d'),self.company_id.id)

		return sql