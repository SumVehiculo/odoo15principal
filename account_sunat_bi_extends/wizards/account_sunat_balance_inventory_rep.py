# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *

class AccountSunatBalanceInventoryRep(models.TransientModel):
	_inherit = 'account.sunat.balance.inventory.rep'

	def _get_sql_nom(self,type):
		sql,nomenclatura = super(AccountSunatBalanceInventoryRep,self)._get_sql_nom(type)
		if type == 22:
			sql = self._get_sql_22(self.period,self.company_id.id)
			nomenclatura = "032400"
		return sql,nomenclatura

	def _get_sql_22(self,period,company_id):
		sql = """
			SELECT 
			{period_code} as campo1,
			'09'as campo2,
			air.code as campo3,
			round(sum(aml.debit-aml.credit),2) as campo4,
			'1' as campo5,
			NULL as campo6
			FROM account_move_line aml
			LEFT JOIN account_move am on am.id = aml.move_id
			LEFT JOIN account_account aa on aa.id = aml.account_id
			LEFT JOIN account_integrated_results_catalog air on air.id = aa.account_integrated_result_id
			WHERE (am.date between '{date_start}' and '{date_end}') and 
			am.company_id = {company} and aa.account_integrated_result_id is not null and am.state = 'posted'
			GROUP BY air.id, air.code
			""".format(
			company = company_id,
			period_code = str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day))),
			date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			date_end = period.date_end.strftime('%Y/%m/%d'),
		)
		return sql