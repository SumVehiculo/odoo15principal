# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrPayslipRunMoveWizard(models.TransientModel):
	_name = 'hr.payslip.run.move.wizard'
	_description = 'Hr Payslip Run Move Wizard'

	name = fields.Char()
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Planilla')
	option = fields.Selection([('window', 'Pantalla'),
							   ('xlsx', 'Excel')], string='Ver en', default='window')
	with_analytic = fields.Boolean(default=True, string='Con Cuenta Analitica')
	debit = fields.Float(string='Total Debe', readonly=False)
	credit = fields.Float(string='Total Haber', readonly=False)
	difference = fields.Float(string='Diferencia', compute='_get_difference')
	journal_id = fields.Many2one('account.journal', string='Diario')
	account_id = fields.Many2one('account.account', string='Cuenta de Ajuste')

	@api.depends('debit', 'credit')
	def _get_difference(self):
		for record in self:
			record.difference = abs(record.debit - record.credit)

	def generate_move(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.type_doc_pla.id:
			raise UserError('No se ha configurado el tipo de comprobante para Planilla')
		if not MainParameter.partner_id.id:
			raise UserError('No se ha configurado un partner para Planilla')
		PR = self.env['hr.payslip.run'].browse(self._context.get('payslip_run_id'))
		extra_line = {}
		if self.debit > self.credit:
			extra_line = {
				'account_id': self.account_id.id,
				'debit': 0,
				'credit': self.difference,
				'type_document_id' : MainParameter.type_doc_pla.id,
				'nro_comp' : 'PLA'+(PR.name.code).replace("-", ""),
				'name': 'Ajuste por Redondeo',
				'partner_id': MainParameter.partner_id.id}
		if self.credit > self.debit:
			extra_line = {
				'account_id': self.account_id.id,
				'debit': self.difference,
				'credit': 0,
				'type_document_id' : MainParameter.type_doc_pla.id,
				'nro_comp' : 'PLA'+(PR.name.code).replace("-", ""),
				'name': 'Ajuste por Redondeo',
				'partner_id': MainParameter.partner_id.id}

		lines = self.env['hr.payslip.run.move'].search([])
		# print("lines",lines)
		extra_line = [(0, 0, extra_line)] if extra_line else []
		move = self.env['account.move'].create({
			'journal_id': self.journal_id.id,
			'date': PR.date_end,
			'glosa': 'PLANILLA DE REMUNERACIONES '+(PR.name.name),
			'ref': 'PLA'+(PR.name.code).replace("-", ""),
			'line_ids': extra_line + [
				(0, 0, {
					'account_id': line.account_id.id,
					'debit': line.debit,
					'credit': line.credit,
					'type_document_id' : MainParameter.type_doc_pla.id,
					'nro_comp' : 'PLA'+(PR.name.code).replace("-", ""),
					'name': line['description'] if line['description'] else None,
					'analytic_account_id': line['analytic_account_id'].id if line['analytic_account_id'].id else None,
					'partner_id':line['partner_id'].id if line['partner_id'].id else MainParameter.partner_id.id,
				}) for line in lines
			]
		})
		move.action_post()
		PR.account_move_id = move.id
		PR.state = 'close'
		PR.slip_ids.action_payslip_hecho()
		return self.env['popup.it'].get_message('Generacion de Asiento Exitosa')


	# METODOS PARA ANALISIS DE ASIENTOS DE PLANILLAS
	def get_sql(self):
		function = 'payslip_run_analytic_move' if self.with_analytic else 'payslip_run_move'
		sql = """
				CREATE OR REPLACE VIEW hr_payslip_run_move AS
				(
					SELECT row_number() OVER () AS id, *
					from %s(%d, %d)
					where debit!=0 or credit!=0
				)
			""" % (function, self.payslip_run_id.id, self.env.company.id)
		return sql

	def get_payslip_move_analysis(self):
		self._cr.execute(self.get_sql())
		if self.option == 'window':
			return self.get_payslip_move_analysis_window()
		else:
			return self.get_payslip_move_analysis_excel()

	def get_payslip_move_analysis_window(self):
		return {
			'name': 'Analisis Asiento Planilla',
			'type': 'ir.actions.act_window',
			'res_model': 'hr.payslip.run.move',
			'view_mode': 'tree',
			'views': [(False, 'tree')],
			'context': {'with_analytic': self.with_analytic}
		}

	def get_payslip_move_analysis_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		direccion = MainParameter.dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(direccion + 'Analisis_Asiento_Planilla.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Analisis Asiento Planilla")
		worksheet.set_tab_color('blue')
		HEADERS = ['SECUENCIA', 'REGLA SALARIAL', 'CODIGO', 'DEBE', 'HABER']
		if self.with_analytic:
			HEADERS = HEADERS[:3] + ['CUENTA ANALITICA'] + HEADERS[3:]
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		x, y = 1, 0
		total_credit = total_debit = 0
		for line in self.env['hr.payslip.run.move'].search([]):
			worksheet.write(x, 0, line.sequence or '', formats['especial1'])
			worksheet.write(x, 1, line.salary_rule_id.name or '', formats['especial1'])
			worksheet.write(x, 2, line.code or '', formats['especial1'])
			if self.with_analytic:
				worksheet.write(x, 3, line.analytic_account_id.name or '', formats['especial1'])
				y = 1
			worksheet.write(x, 3 + y, line.debit or 0, formats['numberdos'])
			worksheet.write(x, 4 + y, line.credit or 0, formats['numberdos'])
			total_debit += line.debit
			total_credit += line.credit
			x += 1
		worksheet.write(x, 3 + y, total_debit, formats['numbertotal'])
		worksheet.write(x, 4 + y, total_credit, formats['numbertotal'])

		widths = [12, 30, 10, 10, 10]
		if self.with_analytic:
			widths = widths[:3] + [30] + widths[3:]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()

		f = open(direccion + 'Analisis_Asiento_Planilla.xlsx', 'rb')
		return self.env['popup.it'].get_file('Analisis_Asiento_Planilla.xlsx', base64.encodebytes(b''.join(f.readlines())))