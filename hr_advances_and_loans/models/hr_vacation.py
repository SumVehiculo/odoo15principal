# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrVacation(models.Model):
	_inherit = 'hr.vacation'

	def import_advances(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.grat_advance_id:
			raise UserError('No se ha configurado un tipo de adelanto para Vacaciones en Parametros Generales de la pestaña Vacaciones')
		log = ''
		Lot = self.payslip_run_id
		for line in self.line_ids:
			sql = """
				select sum(ha.amount) as amount,
				ha.employee_id
				from hr_advance ha
				inner join hr_advance_type hat on hat.id = ha.advance_type_id
				where ha.discount_date >= '{0}' and
					  ha.discount_date <= '{1}' and
					  ha.employee_id = {2} and
					  ha.state = 'not payed' and
					  hat.id = {3}
				group by ha.employee_id
				""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.vaca_advance_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			if data:
				line.advance_amount = data[0]['amount']
				line.total = line.neto_total - line.quinta - line.advance_amount - line.loan_amount
				log += '%s\n' % line.employee_id.name
			self.env['hr.advance'].search([('discount_date', '>=', Lot.date_start),
										   ('discount_date', '<=', Lot.date_end),
										   ('employee_id', '=', line.employee_id.id),
										   ('state', '=', 'not payed'),
										   ('advance_type_id.id', '=', MainParameter.vaca_advance_id.id)]).turn_paid_out()

		if log:
			return self.env['popup.it'].get_message('Se importo adelantos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun adelanto')

	def import_loans(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.grat_loan_id:
			raise UserError('No se ha configurado un tipo de prestamo para Vacaciones en Parametros Generales de la pestaña Vacaciones')
		log = ''
		Lot = self.payslip_run_id
		for line in self.line_ids:
			sql = """
				select sum(hll.amount) as amount,
				hll.employee_id
				from hr_loan_line hll
				inner join hr_loan_type hlt on hlt.id = hll.loan_type_id
				where hll.date >= '{0}' and
					  hll.date <= '{1}' and
					  hll.employee_id = {2} and
					  hll.validation = 'not payed' and
					  hlt.id = {3}
				group by hll.employee_id
				""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.vaca_loan_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			if data:
				line.loan_amount = data[0]['amount']
				line.total = line.neto_total - line.quinta - line.advance_amount - line.loan_amount
				log += '%s\n' % line.employee_id.name
			self.env['hr.loan.line'].search([('date', '>=', Lot.date_start),
											 ('date', '<=', Lot.date_end),
											 ('employee_id', '=', line.employee_id.id),
											 ('validation', '=', 'not payed'),
											 ('loan_type_id.id', '=', MainParameter.vaca_loan_id.id)]).turn_paid_out()

		if log:
			return self.env['popup.it'].get_message('Se importo prestamos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun prestamo')

	def set_amounts(self, line_ids, Lot, MainParameter):
		super(HrVacation, self).set_amounts(line_ids, Lot, MainParameter)
		inp_adv = MainParameter.vaca_advance_id.input_id
		inp_loan = MainParameter.vaca_loan_id.input_id
		for line in line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			adv_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_adv)
			loan_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_loan)
			adv_line.amount = line.advance_amount
			loan_line.amount = line.loan_amount

class HrVacationLine(models.Model):
	_inherit = 'hr.vacation.line'

	advance_amount = fields.Float(string='(-) Monto Adelanto')
	loan_amount = fields.Float(string='(-) Monto Prestamo')

	def compute_vacation_line(self):
		super(HrVacationLine, self).compute_vacation_line()
		for record in self:
			record.total = record.neto_total - record.quinta - record.advance_amount - record.loan_amount