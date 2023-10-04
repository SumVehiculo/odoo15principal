# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *

class NatureResultWizard(models.TransientModel):
	_inherit = 'nature.result.wizard'

	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)

	def _get_nature_result_sql(self):
		if self.currency == 'pen':
			sql = """
			CREATE OR REPLACE VIEW nature_result AS 
			(
				SELECT row_number() OVER () AS id,
				at.name,
				at.group_nature,
				sum(debe) - sum(haber) as total,
				at.order_nature
				from get_bc_register('{period_from}','{period_to}',{company}) bcr
				left join account_account aa on aa.code = bcr.cuenta and aa.company_id = {company}
				left join account_type_it at on at.id = aa.account_type_it_id
				where group_nature is not null
				group by at.name,at.group_nature,at.order_nature
				order by at.order_nature
			)
			""".format(
					period_from = self.period_from.code,
					period_to = self.period_to.code,
					company = self.company_id.id
				)
		else:
			sql_not_journal = "'{%s}'"%('0')
			param = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
			if param.journal_exchange_exclude:
				sql_not_journal = "'{%s}'" % (','.join(str(i) for i in param.journal_exchange_exclude.ids))
			sql = """
			CREATE OR REPLACE VIEW nature_result AS 
			(
				SELECT row_number() OVER () AS id,
				at.name,
				at.group_nature,
				sum(bcr.debe) - sum(bcr.haber) as total,
				at.order_nature
				from get_f1_register_usd('{period_from}','{period_to}',{company},{sql_not_journal}) bcr
				left join account_account aa on aa.id = bcr.account_id
				left join account_type_it at on at.id = aa.account_type_it_id
				where at.group_nature is not null
				group by at.name,at.group_nature,at.order_nature
				order by at.order_nature
			)
			""".format(
					period_from = self.period_from.code,
					period_to = self.period_to.code,
					company = self.company_id.id,
					sql_not_journal = sql_not_journal
				)
		return sql