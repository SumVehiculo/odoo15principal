# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	txt_generated = fields.Boolean(string='Txt Generado', default=False)
	multipayment_ids = fields.One2many('hr.automate.multipayment', 'payslip_run_id', string='Pagos Multiples')
	multipayment_count = fields.Integer(compute='_compute_multipayment_count')

	def _compute_multipayment_count(self):
		for rec in self:
			rec.multipayment_count = len(rec.multipayment_ids)

	def generate_multipayments(self):
		if self.multipayment_ids and any(m.state == 'done' for m in self.multipayment_ids):
			raise UserError('No se puede generar pagos si ya se tiene registros de pagos de haberes en estado finalizado')
		self.multipayment_ids.unlink()

		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if  not MainParameter.journals_banks:
			raise UserError('Falta configurar bancos en la pestaña de Pagos Haberes y CTS en Parametros Generales de Nomina')
		if self.slip_ids:
			journal_banks = []
			format_banks = []
			#obtener todos los formatos de banco
			for slip in self.slip_ids:
				format_banks.append(slip.wage_bank.format_bank)
			#recorrer los bancos y agregarlo si existe el mismo formato
			for j in MainParameter.journals_banks:
				if j.bank_id.format_bank in format_banks:
					journal_banks.append(j)

			for journal in journal_banks:
				Multipayment = self.env['hr.automate.multipayment'].create({
					'is_hr_payment': True,
					'journal_id': journal.id,
					'payment_date': fields.Date.today(),
					# 'catalog_payment_id': self.env['einvoice.catalog.payment'].search([('code', '=', '003')], limit=1).id,
					'glosa': str(self.name.code[4:6])+"-"+str(self.name.code[0:4]),
					'payslip_run_id': self.id,
				})
				Multipayment.get_slip_ids()
			Employees = self.slip_ids.mapped('employee_id').filtered(lambda e: not e.wage_bank_account_id.bank_id.format_bank)
			if Employees:
				return self.env['popup.it'].get_message(
					'Se genero exitosamente algunos empleados a excepcion de los siguientes:\n' + '\n'.join(Employees.mapped('name'))
				)
		return self.env['popup.it'].get_message('Se genero exitosamente')

	def get_multipayments_view(self):
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.automate.multipayment",
			"views": [
				(self.env.ref('hr_automate_multipayment.view_hr_automate_multipayment_tree').id, "tree"),
				(self.env.ref('hr_automate_multipayment.view_hr_automate_multipayment_form').id, "form")],
			"domain": [['id', 'in', self.multipayment_ids.ids]],
			"name": "Pagos Haberes",
		}


class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	wage_account = fields.Many2one('res.partner.bank', related='employee_id.wage_bank_account_id')
	wage_bank = fields.Many2one('res.bank', related='employee_id.wage_bank_account_id.bank_id', store=True, string='Banco')
	# biweekly_advance = fields.Monetary(compute='_compute_basic_net', string='Adelanto Quincenal')
	multipayment_id = fields.Many2one('hr.automate.multipayment')
	is_text = fields.Boolean(string='Txt', default=True)

	# def _compute_basic_net(self):
	# 	res = super(HrPayslip, self)._compute_basic_net()
	# 	MainParameter = self.env['hr.main.parameter'].get_main_parameter()
	# 	for payslip in self:
	# 		payslip.biweekly_advance = payslip._get_salary_line_total(MainParameter.biweekly_advance_sr_id.code) if MainParameter.biweekly_advance_sr_id else 0
	# 	return res