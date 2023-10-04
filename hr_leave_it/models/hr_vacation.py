# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
from calendar import *
from dateutil.relativedelta import relativedelta

class HrVacation(models.Model):
	_name = 'hr.vacation'
	_description = 'Hr Vacation'

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'exported': [('readonly', True)]})
	fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año Fiscal', required=True, states={'exported': [('readonly', True)]})
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True, states={'exported': [('readonly', True)]})
	line_ids = fields.One2many('hr.vacation.line', 'vacation_id', states={'exported': [('readonly', True)]}, string='Calculo de Vacaciones')
	state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], default='draft', string='Estado')

	def compute_vaca_line_all(self):
		self.line_ids.compute_vacation_line()
		return self.env['popup.it'].get_message('Se Recalculo exitosamente')

	@api.onchange('fiscal_year_id', 'payslip_run_id')
	def _get_period(self):
		for record in self:
			if record.payslip_run_id.id and record.fiscal_year_id.name:
				periodo = str(record.payslip_run_id.name.name)
				record.name = 'Vacaciones %s' % (periodo)

	def turn_draft(self):
		self.state = 'draft'

	def set_amounts(self, line_ids, Lot, MainParameter):
		inp_vacation = MainParameter.vaca_input_id
		inp_ade_vacation = self.env['hr.payslip.input.type'].search([('company_id', '=', self.env.company.id),('code', '=', 'ADE_VAC')], limit=1)
		inp_fifth = MainParameter.fifth_category_input_id
		for line in line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			vacation_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_vacation)
			ade_vacation_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_ade_vacation)
			fifth_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_fifth)
			vacation_line.amount = line.total_vacation
			ade_vacation_line.amount = line.total
			fifth_line.amount = line.quinta

	def export_vacation(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_vacation_values()
		Lot = self.payslip_run_id
		self.set_amounts(self.line_ids, Lot, MainParameter)
		self.state = 'exported'
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def get_date_limit_from(self, date_limit_to):
		#####Logic to get the last 6 months from cessation_date 'cause all bonifications need this months to average the amount#####
		last_day = monthrange(date_limit_to.year, date_limit_to.month)[1]
		if last_day == date_limit_to.day:
			date_limit_from = date_limit_to - relativedelta(months=+6)
			limit_last_day = monthrange(date_limit_from.year, date_limit_from.month)[1]
			if limit_last_day == date_limit_from.day:
				date_limit_from += timedelta(days=1)
			else:
				result = limit_last_day - date_limit_from.day + 1
				date_limit_from += timedelta(days=result)
		else:
			date_limit_from = date_limit_to - relativedelta(months=+6)
			date_limit_from = date(date_limit_from.year, date_limit_from.month, 1)
		return date_limit_from

	def get_vacation(self):
		# self.line_ids.vacation_line_ids.unlink()
		# self.line_ids.unlink()
		self.env['hr.vacation.line'].search([('vacation_id','=',self.id),('preserve_record','=',False)]).unlink()
		year = int(self.fiscal_year_id.name)
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		MonthLot = self.payslip_run_id

		Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small','micro'] and
															not slip.contract_id.less_than_four).mapped('employee_id')

		# print("Employees",Employees)
		for Employee in Employees:
			if Employee.contract_id.situation_id.code == '0':
				continue
			else:
				MonthSlip = MonthLot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
				# print('MonthSlip',MonthSlip)
				Contract = self.env['hr.contract'].get_first_contract(Employee, MonthSlip.contract_id)
				# print('Contract',Contract)
				leave_vacations = self.env['hr.leave.it'].search([('payslip_run_id', '=', MonthLot.id),
																  ('employee_id', '=', Employee.id),
																  ('work_suspension_id', '=', MainParameter.suspension_type_id.id)], limit=1)

				number_of_days = self.env['hr.leave.it'].search([('payslip_run_id', '=', MonthLot.id),
																  ('employee_id', '=', Employee.id),
																  ('work_suspension_id', '=', MainParameter.suspension_type_id.id)]).mapped('number_of_days')

				# print("leave_vacations",leave_vacations)
				if leave_vacations.payslip_run_id.name.id == MonthLot.name.id:
					bonus_months = months = days = lacks = 0
					Commissions = Bonus = ExtraHours = self.env['hr.payslip.line']
					# print('comisiones',Commissions)
					admission_date = Contract.date_start
					# print('admission_date',admission_date)
					compute_date = date(year-1, admission_date.month, admission_date.day)
					compute_date_final = date(year, admission_date.month, admission_date.day)
					# print('compute_date',compute_date)
					wage= MonthSlip.wage
					# print('wage',wage)
					# household_allowance = MonthSlip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.household_allowance_sr_id).total
					household_allowance = MonthSlip.rmv*0.1 if sum(number_of_days) == 30 and Employee.children>0 else 0
					# print('household_allowance',household_allowance)
					compute_payslip_date = date(compute_date.year, compute_date.month, 1)
					# print('compute_payslip_date',compute_payslip_date)
					Lots = self.env['hr.payslip.run'].search([('date_start', '>=', (compute_payslip_date+relativedelta(months=1))),
															  ('date_end', '<=', (MonthSlip.date_to - relativedelta(months=1)))])
					# print('Lots primero',Lots)
					total_dias=0
					for Lot in Lots:
						# print('Lot',Lot.name)
						EmployeeSlips = Lot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
						SalaryRules = EmployeeSlips.mapped('line_ids')
						WorkedDays = EmployeeSlips.mapped('worked_days_line_ids')
						WorkingWD =	sum(WorkedDays.filtered(lambda line: line.wd_type_id in MainParameter.working_wd_ids).mapped('number_of_days'))
						if WorkingWD >= 30:
							months += 1
							total_dias += WorkingWD
						else:
							days += WorkingWD

						LackWD = sum(WorkedDays.filtered(lambda line: line.wd_type_id == MainParameter.lack_wd_id).mapped('number_of_days'))
						lacks += LackWD
					# print("lacks",lacks)
					# print("total_dias",total_dias)
					date_limit_to = compute_date_final
					# print('date_limit_to',date_limit_to)
					date_limit_from = self.get_date_limit_from(date_limit_to)
					# print('date_limit_from',date_limit_from)
					Lots = self.env['hr.payslip.run'].search([('date_start', '>=', date_limit_from),
															  ('date_end', '<=', date_limit_to)])
					# print('Lots',Lots)
					bonus_months = len(Lots.mapped('slip_ids').filtered(lambda slip: slip.employee_id == Employee))
					for Lot in Lots:
						# print('Lot',Lot.name)
						EmployeeSlips = Lot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
						SalaryRules = EmployeeSlips.mapped('line_ids')
						Commissions += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.commission_sr_ids and line.total > 0)
						Bonus += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.bonus_sr_ids and line.total > 0)
						ExtraHours += SalaryRules.filtered(lambda line: line.salary_rule_id == MainParameter.extra_hours_sr_id and line.total > 0)

					commission = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, Commissions)
					bonus = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, Bonus)
					extra_hours = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, ExtraHours)
					computable_remuneration = wage + household_allowance + commission + bonus + extra_hours
					medical_days, excess_medical_rest = MainParameter.calculate_excess_medical_rest(year, Employee)
					# print('computable_remuneration',computable_remuneration)
					last_day = monthrange(compute_date_final.year,compute_date_final.month)[1]
					days = days + medical_days + (last_day-compute_date.day+1) + date_limit_to.day
					total_dias+=days
					# print('days',days)
					if days >= 30:
						days, months = MainParameter.get_months_of_30_days(days, months)
					# print('days: ',days,'    months:',months)
					amount_per_month = computable_remuneration if MonthSlip.contract_id.labor_regime == 'general' else computable_remuneration/2
					amount_per_day = amount_per_month/30
					amount_per_lack = amount_per_day * lacks
					advanced_vacation = computable_remuneration/30*sum(number_of_days)
					total_vacation = ReportBase.custom_round(advanced_vacation - amount_per_lack, 2)
					membership = MonthSlip.contract_id.membership_id
					onp = afp_jub = afp_si = afp_mixed_com = afp_fixed_com = 0
					if membership.is_afp:
						afp_jub = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
						afp_si = ReportBase.custom_round(membership.prima_insurance/100 * total_vacation, 2)
						if MonthSlip.contract_id.commision_type == 'mixed':
							afp_mixed_com = ReportBase.custom_round(membership.mixed_commision/100 * total_vacation, 2)
							afp_fixed_com =0
						elif MonthSlip.contract_id.commision_type == 'flow':
							afp_fixed_com = ReportBase.custom_round(membership.fixed_commision /100 * total_vacation, 2)
							afp_mixed_com =0
					else:
						onp = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
					neto_total = ReportBase.custom_round(total_vacation - afp_jub - afp_si - afp_mixed_com - afp_fixed_com - onp, 2)

					# quinta = self.compute_fifth_line(MonthSlip)/30*sum(number_of_days)
					# print("quinta",quinta)
					vals = {
						'vacation_id': self.id,
						'employee_id': Employee.id,
						'contract_id': MonthSlip.contract_id.id,
						'workday_id': MonthSlip.contract_id.workday_id.id,
						'distribution_id': MonthSlip.contract_id.distribution_id.name,
						'admission_date': admission_date,
						'compute_date_ini': compute_date,
						'compute_date_fin': compute_date_final,
						'membership_id': membership.id,
						'months': months,
						'days': days,
						'lacks': lacks,
						'record_days': MonthSlip.contract_id.workday_id.record_days,
						'total_days': total_dias,
						'wage': wage,
						'household_allowance': household_allowance,
						'commission': commission,
						'bonus': bonus,
						'extra_hours': extra_hours,
						'computable_remuneration': computable_remuneration,
						'accrued_vacation': sum(number_of_days),
						# 'advanced_vacation': advanced_vacation,
						'total_vacation': total_vacation,
						'onp': onp,
						'afp_jub': afp_jub,
						'afp_si': afp_si,
						'afp_mixed_com': afp_mixed_com,
						'afp_fixed_com': afp_fixed_com,
						'neto_total': neto_total,
						# 'quinta': quinta,
						'total': neto_total,
						# 'preserve_record': True,
					}
					self.env['hr.vacation.line'].create(vals)

		preservados = self.env['hr.vacation.line'].search([('vacation_id', '=', self.id), ('preserve_record', '=', True)])
		empleados_pre = []
		# print("preservados",preservados)
		for j in preservados:
			if j.employee_id.id not in empleados_pre:
				empleados_pre.append(j.employee_id.id)
		eliminar = []
		for l in self.line_ids:
			if l.employee_id.id in empleados_pre:
				if l.preserve_record == False:
					eliminar.append(l)
		for l in eliminar:
			l.unlink()
		return self.env['popup.it'].get_message('Se calculo exitosamente')

	# CALCULO PROPORCIONAL DE QUINTA
	def compute_fifth(self):
		return self.line_ids.compute_quinta_line(self.payslip_run_id)

class HrVacationLine(models.Model):
	_name = 'hr.vacation.line'
	_description = 'Vacation Line'

	vacation_id = fields.Many2one('hr.vacation', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	contract_id = fields.Many2one('hr.contract', string='Contrato')
	identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
	last_name = fields.Char(related='employee_id.last_name', string='Apellido Paterno')
	m_last_name = fields.Char(related='employee_id.m_last_name', string='Apellido Materno')
	names = fields.Char(related='employee_id.names', string='Nombres')
	admission_date = fields.Date(string='Fecha de Ingreso')
	compute_date_ini = fields.Date(string='Fecha Comp Inicial')
	compute_date_fin = fields.Date(string='Fecha Comp Final')
	membership_id = fields.Many2one(related='contract_id.membership_id', string='Afiliacion')
	workday_id = fields.Many2one('hr.workday', string='Jornada Laboral')
	distribution_id = fields.Char(string='Distribucion Analitica')
	months = fields.Integer(string='Meses')
	days = fields.Integer(string='Dias')
	lacks = fields.Integer(string='Faltas')
	record_days = fields.Integer(string='Record Vacacional')
	total_days = fields.Integer(string='Total Dias')
	wage = fields.Float(string='Sueldo')
	household_allowance = fields.Float(string='Asignacion Familiar')
	commission = fields.Float(string='Prom. Comision')
	bonus = fields.Float(string='Prom. Bonificacion')
	extra_hours = fields.Float(string='Prom. Horas Extras')
	computable_remuneration = fields.Float(string='Remuneracion Computable')
	accrued_vacation = fields.Integer(string='Dias Vac. Devengadas')
	# advanced_vacation = fields.Float(string='Monto Vac. Devengadas')
	total_vacation = fields.Float(string='Total Vacaciones')
	onp = fields.Float(string='(-) ONP')
	afp_jub = fields.Float(string='(-) AFP JUB')
	afp_si = fields.Float(string='(-) AFP SI')
	afp_mixed_com = fields.Float(string='(-) AFP COM. MIXTA')
	afp_fixed_com = fields.Float(string='(-) AFP COM. FIJA')

	neto_total = fields.Float(string='Neto Vacaciones')
	quinta = fields.Float(string='(-) Retencion Quinta', default=0)
	total = fields.Float(string='Total a pagar')

	vacation_line_ids = fields.One2many('hr.leave.vacation.line', 'leave_vacation_id')

	preserve_record = fields.Boolean('No Recalcular')

	def compute_quinta_line(self,MonthLot):
		# MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		# MainParameter.check_fifth_values()
		date_start = MonthLot.date_start
		date_from = date_start - relativedelta(months=1)
		date_to="%s-%s-%s" % (date_from.year, str(date_from.month).rjust(2,'0'), monthrange(date_from.year, date_from.month)[1])
		for line in self:
			# print("date_from",date_from)
			# print("date_to",date_to)
			past_ret = self.env['hr.payslip.line'].search([
				('date_from', '=', date_from),
				('date_to', '=', date_to),
				('employee_id', '=', line.employee_id.id)
			])
			# print("past_ret",past_ret)
			ret_quinta = sum(past_ret.filtered(lambda line: line.salary_rule_id.code == 'QUINTA').mapped('total'))
			# print("ret_quinta",ret_quinta)
			line.quinta = ret_quinta/30*line.accrued_vacation
			line.total = line.neto_total - line.quinta
		return self.env['popup.it'].get_message('Se importo exitosamente')

	def compute_vacation_line(self):
		ReportBase = self.env['report.base']

		for record in self:
			record.total_days = (record.months*30)+record.days-record.lacks
			record.computable_remuneration = record.wage + record.household_allowance + record.commission + record.bonus + record.extra_hours
			amount_per_month = record.computable_remuneration if record.contract_id.labor_regime == 'general' else record.computable_remuneration/2
			amount_per_day = amount_per_month/30
			amount_per_lack = amount_per_day * record.lacks
			vacation = ReportBase.custom_round(amount_per_month - amount_per_lack, 2)
			advanced_vacation = vacation/30*int(record.accrued_vacation)
			record.total_vacation = ReportBase.custom_round(advanced_vacation - amount_per_lack, 2)
			# record.total_vacation = record.accrued_vacation + vacation - record.advanced_vacation
			membership = record.contract_id.membership_id
			onp = afp_jub = afp_si = afp_mixed_com= afp_fixed_com= 0
			if membership.is_afp:
				afp_jub = ReportBase.custom_round(membership.retirement_fund/100 * record.total_vacation, 2)
				if record.accrued_vacation>=membership.insurable_remuneration:
					afp_si = ReportBase.custom_round(membership.prima_insurance/100 * membership.insurable_remuneration, 2)
				else:
					afp_si = ReportBase.custom_round(membership.prima_insurance/100 * record.total_vacation, 2)
				if record.contract_id.commision_type == 'mixed':
					afp_mixed_com = ReportBase.custom_round(membership.mixed_commision/100 * record.total_vacation, 2)
					afp_fixed_com =0
				elif record.contract_id.commision_type == 'flow':
					afp_fixed_com = ReportBase.custom_round(membership.fixed_commision /100 * record.total_vacation, 2)
					afp_mixed_com =0
			else:
				onp = ReportBase.custom_round(membership.retirement_fund/100 * record.total_vacation, 2)
			record.afp_jub = afp_jub
			record.afp_si = afp_si
			record.afp_mixed_com = afp_mixed_com
			record.afp_fixed_com = afp_fixed_com
			record.onp = onp
			record.neto_total = ReportBase.custom_round(record.total_vacation - afp_jub - afp_si - afp_mixed_com - afp_fixed_com - onp, 2)
			record.total = record.neto_total - record.quinta
			if not record.total > 0 and not self._context.get('line_form', False):
				record.unlink()

	# Generacion de calculo de vacaciones
	def _get_sql_salary(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_vacation_values()
		sql_comi = "case when T.salary_rule_id in (%s) then sum(T.total) else 0 end  as comi, " % (','.join(str(i) for i in MainParameter.commission_sr_ids.ids))
		sql_bonus = "case when T.salary_rule_id in (%s) then sum(T.total) else 0 end  as o_ing " % (','.join(str(i) for i in MainParameter.bonus_sr_ids.ids))
		struct_id=self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id
		date_calculate = self.vacation_id.payslip_run_id.date_start
		sql = """
				select      
				T.employee_id,
				T.periodo,
				T.code,
				sum(T.bas) AS bas,
				sum(T.af) AS af,
				sum(T.comi) AS comi,
				sum(T.hext) AS hext,
				sum(T.o_ing) AS o_ing,
				sum(T.bas)+sum(T.af)+sum(T.comi)+sum(T.hext)+sum(T.o_ing) AS total
				FROM 
					(
					select      
					T.employee_id,
					T.periodo,
					T.code,
					T.salary_rule_id,
					case when T.salary_rule_id in ({basic_sr_id}) then sum(T.total) else 0 end  as bas,
					case when T.salary_rule_id in ({household_allowance_sr_id}) then sum(T.total) else 0 end  as af,
					{sql_comi}
					case when T.salary_rule_id in ({extra_hours_sr_id}) then sum(T.total) else 0 end  as hext,
					{sql_bonus}
					from (	SELECT	
							he.id as employee_id,
							he.name,
							hpr.name as periodo,
							hper.code,
							hp.date_from,
							hp.date_to,
							hsr.id as salary_rule_id,
							sum(hpl.total) as total
							from hr_payslip hp 
							inner join hr_payslip_line hpl on hpl.slip_id = hp.id
							inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
							inner join hr_employee he on he.id = hp.employee_id
							inner join hr_payslip_run hpr on hpr.id = hp.payslip_run_id
							inner join hr_period hper on hper.id = hpr.name
							where hsr.active = true
							and hpl.total <> 0
							and hsr.company_id = {company}
							and hsr.struct_id = {struct_id}
							and he.id = {employee_id}
							and (hp.date_from between '{date_from}' and '{date_to}')
							group by he.id,he.name,hpr.name,hper.code,hp.date_from,hp.date_to,hsr.id,hsr.sequence
							order by hp.date_from, hsr.sequence
					)T
					group by T.employee_id, T.periodo,T.code, T.salary_rule_id
				)T
				group by T.employee_id, T.periodo, T.code
				order by T.code
				""".format(
			basic_sr_id = MainParameter.basic_sr_id.id,
			household_allowance_sr_id = MainParameter.household_allowance_sr_id.id,
			sql_comi = sql_comi,
			extra_hours_sr_id = MainParameter.extra_hours_sr_id.id,
			sql_bonus = sql_bonus,
			company = self.env.company.id,
			struct_id = struct_id,
			employee_id = self.employee_id.id,
			date_from = "%s/%s/01" % ((date_calculate - relativedelta(months=6)).year, (date_calculate - relativedelta(months=6)).month),
			date_to = (date_calculate - relativedelta(months=1)).strftime('%Y/%m/%d')
		)
		return sql

	def view_detail(self):
		self.vacation_line_ids.unlink()
		self.env.cr.execute(self._get_sql_salary())
		record = self.env.cr.dictfetchall()
		# print("record",record)
		for res in record:
			data = {
				'leave_vacation_id': self.id,
				'periodo_id': res['periodo'],
				'wage': res['bas'],
				'household_allowance': res['af'],
				'commission': res['comi'],
				'extra_hours': res['hext'],
				'others_income': res['o_ing'],
				'total': res['total'],
			}
			self.env['hr.leave.vacation.line'].create(data)

		return {
			'name': 'Detalle',
			'domain' : [('leave_vacation_id','=',self.id)],
			'type': 'ir.actions.act_window',
			'res_model': 'hr.leave.vacation.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': 'new',
		}

class HrLeaveVacationLine(models.Model):
	_name = 'hr.leave.vacation.line'
	_description = 'Leave Vacation Line'

	leave_vacation_id = fields.Many2one('hr.vacation.line', ondelete='cascade')
	periodo_id = fields.Many2one('hr.period', string='Periodo')
	wage = fields.Float(string='Basico')
	household_allowance = fields.Float(string='Asignacion Familiar')
	commission = fields.Float(string='Comisiones')
	extra_hours = fields.Float(string='Horas Extras')
	others_income = fields.Float(string='Bonificaciones')
	total = fields.Float(string='Base Imponible', digits=(12, 2), compute="get_total", store=True)

	@api.depends('wage', 'household_allowance','commission','extra_hours','others_income')
	def get_total(self):
		for i in self:
			i.total = i.wage + i.household_allowance + i.commission + i.extra_hours + i.others_income
