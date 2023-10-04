# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	import openpyxl
except:
	install('openpyxl==3.0.5')

class AccountWrongSignWizard(models.TransientModel):
	_name = 'account.wrong.sign.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		return fiscal_year.id if fiscal_year else None

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())
	period_id = fields.Many2one('account.period',string='Periodo',required=True)

	
	def get_report(self):
		self.ensure_one()
		sql_not_journal = "'{%s}'"%('0')
		param = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		if param.journal_exchange_exclude:
			sql_not_journal = "'{%s}'" % (','.join(str(i) for i in param.journal_exchange_exclude.ids))
		self.env.cr.execute("""SELECT dg.periodo,aj.name as libro,dg.voucher,dg.fecha,dg.td_sunat,dg.nro_comprobante,dg.doc_partner as ruc, dg.partner,dg.cuenta, 
		dg.balance as monto_mn,
		dg.importe_me as monto_me, dg.tc
		FROM get_diariog_usd('%s','%s',%d,%s) dg
		LEFT JOIN  account_move am ON am.id = dg.move_id
		LEFT JOIN account_journal aj on aj.id = am.journal_id
		where (case when dg.balance > 0 then '+' when dg.balance < 0 then '-' else '0' end) <> (case when dg.importe_me > 0 then '+' when dg.importe_me < 0 then '-' else '0' end)
		and (case when dg.balance > 0 then '+' when dg.balance < 0 then '-' else '0' end) <> '0' and (case when dg.importe_me > 0 then '+' when dg.importe_me < 0 then '-' else '0' end) <> '0'
		"""%(self.period_id.code,self.period_id.code,self.company_id.id,sql_not_journal))
		res = self.env.cr.fetchall()
		colnames = [
			desc[0] for desc in self.env.cr.description
		]
		res.insert(0, colnames)

		wb = openpyxl.Workbook()
		ws = wb.active
		row_position = 1
		col_position = 1
		for index, row in enumerate(res, row_position):
			for col, val in enumerate(row, col_position):
				ws.cell(row=index, column=col).value = val
		output = BytesIO()
		wb.save(output)
		output.getvalue()
		output_datas = base64.b64encode(output.getvalue())
		output.close()

		return self.env['popup.it'].get_file('Monto en Dolares con signo errado.xlsx',output_datas)