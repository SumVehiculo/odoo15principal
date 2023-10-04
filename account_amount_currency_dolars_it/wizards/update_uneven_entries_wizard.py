# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
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

class UpdateRateDolarsWizard(models.TransientModel):
	_name = 'update.uneven.entries.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		return fiscal_year.id if fiscal_year else None

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())
	period_id = fields.Many2one('account.period',string='Periodo')

	def get_report_excel(self):

		self.ensure_one()
		self.env.cr.execute("""SELECT am.name as voucher, am.ref as referencia, am.date as fecha_contable,
			aj.name as diario, T.amount as monto_descuadre FROM (SELECT aml.move_id,
			sum(coalesce(aml.amount_c)) as amount
			FROM account_move_line aml
			LEFT JOIN account_move am ON aml.move_id = am.id
			WHERE am.state = 'posted' AND aml.display_type IS NULL AND aml.account_id IS NOT NULL 
			AND (am.date BETWEEN '{date_from}' AND '{date_to}') AND am.company_id = {company_id}
			GROUP BY aml.move_id
			HAVING sum(coalesce(aml.amount_c)) <> 0)T
			LEFT JOIN account_move am on am.id = T.move_id
			LEFT JOIN account_journal aj on aj.id = am.journal_id""".format(
			company_id = self.company_id.id,
			date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
			date_to = self.period_id.date_end.strftime('%Y/%m/%d')))
			
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

		return self.env['popup.it'].get_file('Asientos con descuadre.xlsx',output_datas)

	def fix_moves(self):
		self.env.cr.execute("""SELECT am.id as move_id, am.name as move_name, am.date, am.ref, am.state as parent_state, 
			am.journal_id, am.company_id, rc.currency_id as company_currency_id, am.currency_rate as tc, T.amount as amount_c 
			FROM (SELECT aml.move_id, sum(coalesce(aml.amount_c)) as amount
			FROM account_move_line aml
			LEFT JOIN account_move am ON aml.move_id = am.id
			WHERE am.state = 'posted' AND aml.display_type IS NULL AND aml.account_id IS NOT NULL 
			AND (am.date BETWEEN '{date_from}' AND '{date_to}') AND am.company_id = {company_id}
			GROUP BY aml.move_id
			HAVING sum(coalesce(aml.amount_c)) <> 0)T
			LEFT JOIN account_move am on am.id = T.move_id
			LEFT JOIN account_journal aj on aj.id = am.journal_id
			LEFT JOIN res_company rc on rc.id = am.company_id""".format(
			company_id = self.company_id.id,
			date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
			date_to = self.period_id.date_end.strftime('%Y/%m/%d')))
		res = self.env.cr.dictfetchall()

		param = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		if not param.profit_account_ed:
			raise UserError(u'No esta Configurada la Cuenta de Ganancias Diferencia de Cambio en sus Parametros Principales.')
		if not param.loss_account_ed:
			raise UserError(u'No esta Configurada la Cuenta de Pérdidas Diferencia de Cambio en sus Parametros Principales.')
		for move in res:
			sql = u"""
				INSERT INTO account_move_line (move_id,move_name,date,ref,parent_state,journal_id,company_id,company_currency_id,
				account_id,account_internal_type,account_root_id,sequence,name,quantity,reconciled,blocked,tax_exigible,tc,amount_c,is_adjustment) VALUES 
				(%d,'%s','%s','%s','%s',%d,%d,%d,%d,'%s',%d,10,'AJUSTE POR REDONDEO EN CONVERSIÓN',1,False,False,True,%0.4f,%0.2f,True)""" % (
					move['move_id'],
					move['move_name'],
					move['date'],
					move['ref'],
					move['parent_state'],
					move['journal_id'],
					move['company_id'],
					move['company_currency_id'],
					param.profit_account_ed.id if move['amount_c']>0 else param.loss_account_ed.id,
					param.profit_account_ed.internal_type if move['amount_c']>0 else param.loss_account_ed.internal_type,
					param.profit_account_ed.root_id.id if move['amount_c']>0 else param.loss_account_ed.root_id.id,
					move['tc'],
					move['amount_c']*-1
				)

			self.env.cr.execute(sql)
		return self.env['popup.it'].get_message('SE ACTUALIZARON CORRECTAMENTE LOS ASIENTOS DESCUADRADOS')