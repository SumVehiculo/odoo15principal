# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	worker_type_id = fields.Many2one('hr.worker.type', string='Tipo de Trabajador', help='TABLA 08 SUNAT')
	structure_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial', required=True)
	work_suspension_ids = fields.One2many('hr.work.suspension', 'contract_id')
	membership_id = fields.Many2one('hr.membership', string='Afiliacion', required=True)
	is_afp = fields.Boolean(string='Es AFP', related='membership_id.is_afp')
	commision_type = fields.Selection([('flow','Flujo'),('mixed','Mixta')],string='Tipo de Comision AFP')
	cuspp = fields.Char(string='CUSPP')
	social_insurance_id = fields.Many2one('hr.social.insurance', string='Seguro Social')
	distribution_id = fields.Many2one('hr.analytic.distribution', string='Distribucion Analitica', required=True)
	workday_id = fields.Many2one('hr.workday', string='Jornada Laboral', required=True)
	situation_id = fields.Many2one('hr.situation', string='Situacion', required=True, help='TABLA 15 SUNAT')
	situation_code = fields.Char(related='situation_id.code')
	situation_reason_id = fields.Many2one('hr.reasons.leave',string='Motivo de Baja', help='TABLA 17 SUNAT')
	labor_regime = fields.Selection([('general', 'Regimen General'),
									 ('small', 'Pequeña Empresa'),
									 ('micro', 'Micro Empresa'),
									 ('practice', 'Practicante'),
									 ('fourth-fifth', 'Trabajadores de 4ta-5ta')], string='Regimen Laboral', required=True)
	less_than_four = fields.Boolean(string='Trabajador con menos de 4 Horas al dia', default=False)
	other_employers = fields.Char(string='Otros Empleadores', default='No', help='Otros Empleadores por Rentas de Quinta Categoria')
	sctr_id = fields.Many2one('hr.sctr', string='SCTR')
	exception = fields.Selection([('L', 'Licencia sin remuneracion en el mes'),
								  ('U', 'Subsidio pagado directamente por ESSALUD'),
								  ('J', 'Pensionado por jubilacion en el mes'),
								  ('I', 'Pensionado por invalidez en el mes'),
								  ('P', 'Relacion laboral inicio despues del cierre de planillas'),
								  ('O', 'Otro Motivo')
								], string='Excepcion de aportar',
								help="""
									L - No corresponde aportar debido a licencia sin renumeracion. \n
									U - No corresponde aportar porque existe un subsidio pagado directamente por essalud y en el mes, no hubo remuneracion pagada por el empleador. \n
									J - No corresponde aportar porque el trabajador se encuentra jubilado. \n
									I - No corresponde aportar porque el trabajador pensionado por invalidez en el mes. \n
									P - No corresponde aportar debido a que la relacion laboral se inicio en el mes despues del cierre de planillas , el aporte del mes se incluira en el mes siguiente. \n
									O - No corresponde aportar debido a otro motivo , no hubo remuneracion en el mes.
								""")
	work_type = fields.Selection([('N', 'Dependiente Normal'),
								  ('C', 'Dependiente Construccion'),
								  ('M', 'Dependiente Mineria'),
								  ('P', 'Dependiente Pesqueria')
								], string='Tipo de Trabajo')

	is_older = fields.Boolean(string='Es Mayor a 65 Años', default=False, help="Resolución SBS N° 938-2001 Trabajadores jubilados y mayores a 65 años")

	hr_responsible_id = fields.Many2one(default=lambda self: self.env.user)

	def _generate_work_entries(self, date_start, date_stop, force=False):
		vals_list = []

		date_start = fields.Datetime.to_datetime(date_start)
		date_stop = datetime.combine(fields.Datetime.to_datetime(date_stop), datetime.max.time())

		for contract in self:
			# For each contract, we found each interval we must generate
			contract_start = fields.Datetime.to_datetime(contract.date_start)
			contract_stop = datetime.combine(fields.Datetime.to_datetime(contract.date_end or datetime.max.date()), datetime.max.time())
			last_generated_from = min(contract.date_generated_from, contract_stop)
			date_start_work_entries = max(date_start, contract_start)

			if last_generated_from > date_start_work_entries:
				contract.date_generated_from = date_start_work_entries
				vals_list.extend(contract._get_work_entries_values(date_start_work_entries, last_generated_from))

			last_generated_to = max(contract.date_generated_to, contract_start)
			date_stop_work_entries = min(date_stop, contract_stop)
			if last_generated_to < date_stop_work_entries:
				contract.date_generated_to = date_stop_work_entries
				vals_list.extend(contract._get_work_entries_values(last_generated_to, date_stop_work_entries))

		if not vals_list:
			return self.env['hr.work.entry']

		return True

	####Esta función ayuda a obtener el contrato del primer empleado utilizando la situación como condicional para obtenerlo.
	def get_first_contract(self, employee, last_contract=False):
		domain = [('employee_id', '=', employee.id), ('date_start', '<=', last_contract.date_start)] if last_contract else [('employee_id', '=', employee.id)]
		Contracts = self.search(domain, order='date_start desc')
		aux, roll_back = None, None
		delimiter = len(Contracts)
		if delimiter > 1:
			for c, Contract in enumerate(Contracts):
				if Contract.situation_id.code == '0' and c == 0:
					aux = [Contract, c]
					continue
				if Contract.situation_id.code == '0' and aux and c - aux[1] == 1:
					return aux[0]
				if Contract.situation_id.code == '0' and aux and not c - aux[1] == 1:
					return roll_back
				if Contract.situation_id.code == '0' and not aux:
					return roll_back
				if Contract.situation_id.code != '0' and delimiter - 1 == c:
					return Contract
				roll_back = Contract
		else:
			return Contracts

class HrWorkSuspension(models.Model):
	_name = 'hr.work.suspension'
	_description = 'Hr Work Suspension'

	contract_id = fields.Many2one('hr.contract')
	suspension_type_id = fields.Many2one('hr.suspension.type', string='Tipo de Suspension', required=True, help='TABLA 21 SUNAT')
	reason = fields.Char(string='Motivo')
	days = fields.Integer(string='Nro. Dias')
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True)