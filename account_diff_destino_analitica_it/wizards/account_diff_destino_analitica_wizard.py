# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO

import base64
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	import openpyxl
except:
	install('openpyxl==3.0.5')

class AccountDiffDestinoAnaliticaWizard(models.TransientModel):
	_name = 'account.diff.destino.analitica.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	date_from = fields.Date(string=u'Fecha Inicial',required=True)
	date_to = fields.Date(string=u'Fecha Final',required=True)
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla', required=True)

	def get_report(self):
		if self.type_show == 'pantalla':
			self.env.cr.execute("""CREATE OR REPLACE view account_diff_destino_analitica_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")

			return {
				'name': 'Diferencia Analitica VS Contabilidad',
				'type': 'ir.actions.act_window',
				'res_model': 'account.diff.destino.analitica.view',
				'view_mode': 'tree',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def get_excel(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_excel_sql_export(self._get_sql())
		return self.env['popup.it'].get_file('Diferencia Analitica VS Contabilidad.xlsx',workbook)

	def _get_sql(self):
		sql = """select a2.id as aml_id,
				a4.id as am_id,
				a4.date as fecha,
				a5.name as diario,
				a4.name as asiento,
				a3.code as cuenta,
				a2.balance as monto_conta,
				a1.monto  as monto_analiticas,
				abs(a2.balance)-abs(a1.monto) as diferencia 
				from 
				(
				select  move_id,sum(round(amount,2)) as monto  from account_analytic_line where company_id={company_id}
				and (date between '{date_from}' and '{date_to}')
				group by move_id) a1

				left join account_move_line a2 on a2.id=a1.move_id
				left join account_account a3 on a3.id=a2.account_id
				left join account_move a4 on a4.id=a2.move_id
				left join account_journal a5 on a5.id=a4.journal_id
				where (abs(a2.balance)-abs(a1.monto))<>0   
				order by a4.date,a5.name,a4.name
				""".format(
					date_from = self.date_from.strftime('%Y/%m/%d'),
					date_to = self.date_to.strftime('%Y/%m/%d'),
					company_id = self.company_id.id
				)
		return sql