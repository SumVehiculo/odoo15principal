# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

class HrVacationRest(models.Model):
	_name='hr.vacation.rest'
	_description='Saldos de Vacaciones'
	_order ='employee_id,date_aplication'

	employee_id=fields.Many2one('hr.employee','Empleado')
	identification_id = fields.Char(related='employee_id.identification_id', string='Nro Doc')
	date_aplication = fields.Date('Fecha de Aplicacion')
	date_from= fields.Date('Periodo Inicio')
	date_end= fields.Date('Periodo fin')
	internal_motive= fields.Selection([('rest','Saldo anterior'),('normal','Vacaciones')],'Motivo Interno',default='normal')
	motive = fields.Char('Motivo')
	days = fields.Integer(u'Días')
	days_rest = fields.Integer(u'Saldo en días')
	year = fields.Char(u'Año')
	amount = fields.Float(string="Importe")
	amount_rest = fields.Float(string="Saldo Importe")
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	def get_vacation_employee(self,employee,show_all):
		self.search([('internal_motive','=','normal')]).unlink()
		if show_all:
			employes = self.env['hr.employee'].search([('company_id','=',self.env.company.id)])
		else:
			employes = [employee]
		for employee in employes:
			last_contract = self.env['hr.contract'].search([('employee_id','=',employee.id),
						('labor_regime','in',['general','small']),('state', 'in', ['open'])])
			if len(last_contract)>1:
				name=employee.names+' '+employee.last_name+' '+employee.m_last_name
				raise ValidationError('El empleado %s tiene dos contratos activos' % name)

			# contratos = self.env['hr.contract'].search([('employee_id','=',employee.id),('state', 'in', ['open'])]).sorted(key=lambda ac:ac.date_end)
			contratos = self.env['hr.contract'].get_first_contract(employee, last_contract)
			date_end_v = None
			contrato_v=None
			for k in contratos:
				if date_end_v==None:
					date_end_v=k.date_end
					contrato_v=k
					continue
				else:
					if date_end_v+ timedelta(days=1)==k.date_start:
						continue
					else:
						contrato_v=k
						date_end_v=k.date_end
			if contrato_v==None:
				continue
			saldos = self.env['hr.vacation.rest'].search([('employee_id','=',employee.id),('internal_motive','=','rest'),('company_id', '=', self.env.company.id)],limit=1)
			if saldos:
				fecha_saldo = saldos.date_aplication - relativedelta(months=12)
				date_time_obj = "%s-%s-%s 00:00:00" % (fecha_saldo.year, str(contrato_v.date_start.month).rjust(2,'0'), str(contrato_v.date_start.day).rjust(2,'0'))
				date_time_obj = datetime.strptime(date_time_obj, '%Y-%m-%d %H:%M:%S')
				date_time_actual = "%s-%s-%s" % (saldos.date_aplication.year, str(contrato_v.date_start.month).rjust(2,'0'), str(contrato_v.date_start.day).rjust(2,'0'))
				date_time_actual = datetime.strptime(date_time_actual, '%Y-%m-%d').date()
			else:
				fecha_saldo = contrato_v.date_start
				date_time_actual = date_time_obj = contrato_v.date_start
			# print("fecha_saldo",fecha_saldo)
			# print("fecha contrato date_time_obj",date_time_obj)

			act_date = date.today()
			# print("fecha hoy act_date",act_date)
			# date_time_str = year+'-'+str(contrato_v.date_start.month).rjust(2,'0')+'-'+str(contrato_v.date_start.day).rjust(2,'0') +' 00:00:00'
			# print("date_time_str",date_time_str)
			# date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
			af = 102.5 if contrato_v.employee_id.children > 0 else 0
			amount_contrato = contrato_v.wage + af

			conteo= int(act_date.year - fecha_saldo.year)
			for cuenta in range(conteo):
				# print("cuenta",cuenta)
				if act_date>=fecha_saldo:
					date_time_end_obj = date_time_obj + relativedelta(months=12*(cuenta))
					if (act_date + relativedelta(months=12)).year==date_time_end_obj.year:
						continue
					else:
						# print("date_time_end_obj",date_time_end_obj)
						if act_date >= date_time_actual:
							vals={
								'employee_id':employee.id,
								'date_aplication':date_time_end_obj + relativedelta(months=12),
								'date_from':date_time_end_obj,
								'date_end':date_time_end_obj + relativedelta(months=12) - timedelta(days=1),
								'internal_motive':'normal',
								'motive':'Vacaciones Devengadas %s'%(date_time_end_obj.year),
								'days':30,
								'days_rest':30,
								'year':str((date_time_end_obj + relativedelta(months=12)).year),
								'amount':amount_contrato,
								'amount_rest':amount_contrato,
								'company_id':self.env.company.id

							}
							self.create(vals)
			AccrualVacations = self.env['hr.accrual.vacation'].search([('employee_id', '=', employee.id)]) 
			if AccrualVacations:
				AccrualVacations = AccrualVacations.sorted(key=lambda a_vacation: a_vacation.accrued_period.date_start)
				for a_vacation in AccrualVacations:
					# if a_vacation.accrued_period.date_start.year==int(year):
					SalaryRules = a_vacation.slip_id
					# print("SalaryRules",SalaryRules)
					amount = SalaryRules.line_ids.filtered(lambda line: line.salary_rule_id.code in ('VAC') and line.total > 0).total
					# print("a_vacation.request_date_from.year",a_vacation.slip_id.date_from.year)
					vals={
						'employee_id':employee.id,
						'date_aplication':a_vacation.date_aplication if a_vacation.date_aplication else a_vacation.slip_id.date_from,
						'date_from':a_vacation.request_date_from if a_vacation.request_date_from else a_vacation.slip_id.date_from,
						'date_end':a_vacation.request_date_to if a_vacation.request_date_to else a_vacation.slip_id.date_to,
						'internal_motive':'normal',
						'motive':a_vacation.motive,
						'days':a_vacation.days*-1,
						'days_rest':a_vacation.days*-1,
						'year':a_vacation.date_aplication.year,
						'amount':amount*-1,
						'amount_rest':amount*-1,
						'company_id':self.env.company.id
					}
					self.create(vals)

			vacas = self.search([('employee_id','=',employee.id)])
			vacas_sorted=vacas.sorted(key=lambda avacas:avacas.date_aplication)
			saldo_dias = 0
			saldo_amount = 0
			for vaca in vacas_sorted:
				if saldo_dias==0:
					if vaca.internal_motive=='normal':
						saldo_dias = vaca.days
						saldo_amount = vaca.amount
					else:
						if vaca.internal_motive=='rest':
							saldo_dias = vaca.days_rest
							saldo_amount = vaca.amount_rest
					continue
				else:
					if vaca.internal_motive=='normal':
						saldo_dias = saldo_dias + vaca.days
						saldo_amount = saldo_amount + vaca.amount
					else:
						if vaca.internal_motive=='rest':
							saldo_dias = saldo_dias + vaca.days
							saldo_amount = saldo_amount + vaca.amount
				vaca.days_rest = saldo_dias
				vaca.amount_rest = saldo_amount