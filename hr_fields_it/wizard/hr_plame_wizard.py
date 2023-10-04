# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
from math import modf
import base64

class HrPlameWizard(models.TransientModel):
	_name = 'hr.plame.wizard'
	_description = 'Hr Plame Wizard'
	_rec_name = 'payslip_run_id'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo')
	type = fields.Selection([('rem','TXT .REM'),('jor','TXT .JOR'),('snl','TXT .SNL')],
						   string=u'Tipo de Archivo PLAME',default='rem', required=True)

	@api.model
	def default_get(self, fields):
		self._cr.execute('truncate table hr_plame_wizard restart identity')
		res = super(HrPlameWizard, self).default_get(fields)
		payslip_run_id = res.get('payslip_run_id')
		res.update({'payslip_run_id': payslip_run_id})
		return res

	def generate_plame_rem(self):
		if len(self.payslip_run_id.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.payslip_run_id.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.payslip_run_id.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.rem' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.payslip_run_id.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					sql = """
						select min(a1.doc_type) as doc_type,
                            a1.dni,
                            a1.sunat,
                            sum(a1.amount_earn) as amount_earn,
                            sum(a1.amount_paid) as amount_paid
                        from (
                        select
						htd.sunat_code as doc_type,
						he.identification_id as dni,
						sr.sunat_code as sunat,
						hpl.total as amount_earn,
						hpl.total as amount_paid
						from hr_payslip_run hpr
						inner join hr_payslip hp on hpr.id = hp.payslip_run_id
						inner join hr_payslip_line hpl on hp.id = hpl.slip_id
						inner join (select * from hr_salary_rule where company_id= %d) as sr on sr.code = hpl.code
						inner join hr_employee he on he.id = hpl.employee_id
						inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where  hpr.id =  %d
						and he.id =  %d
						and sr.sunat_code != ''
						and sr.sunat_code not in ('0804','0607','0605','0601')
						and hpl.total != 0
                        union all
                        select
						htd.sunat_code as doc_type,
						he.identification_id as dni,
						sr.sunat_code as sunat,
						hpl.total as amount_earn,
						hpl.total as amount_paid
						from hr_payslip_run hpr
						inner join hr_payslip hp on hpr.id = hp.payslip_run_id
						inner join hr_payslip_line hpl on hp.id = hpl.slip_id
						inner join (select * from hr_salary_rule where company_id= %d) as sr on sr.code = hpl.code
						inner join hr_employee he on he.id = hpl.employee_id
						inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where  hpr.id =  %d
						and he.id =  %d
						and sr.sunat_code in ('0605','0601')) a1
					    group by a1.sunat, a1.dni
						order by a1.sunat
						""" % (self.company_id.id,payslip_run.id, payslip.employee_id.id,
							   self.company_id.id,payslip_run.id, payslip.employee_id.id)
					self._cr.execute(sql)
					data = self._cr.dictfetchall()
					for line in data:
						f.write("%s|%s|%s|%s|%s|\r\n" % (
									line['doc_type'],
									line['dni'],
									line['sunat'],
									line['amount_earn'],
									line['amount_paid']
								))
				employees.append(payslip.employee_id.id)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.rem' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))

	def generate_plame_jor(self):
		if len(self.payslip_run_id.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.payslip_run_id.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.payslip_run_id.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.jor' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.payslip_run_id.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					sql = """
						select
						min(htd.sunat_code) as doc_type,
						he.identification_id as dni,
						sum(case when hpwd.wd_type_id in ({fal}) then hpwd.number_of_days else 0 end) as fal,
						sum(case when hpwd.wd_type_id in ({hext}) then hpwd.number_of_hours else 0 end) as hext,
						sum(case when hpwd.wd_type_id in ({dvac}) then hpwd.number_of_days else 0 end) as dvac,
						min(rc.hours_per_day) as hours_per_day
						from hr_payslip hp
						inner join hr_employee he on he.id = hp.employee_id
						inner join hr_contract hc on hc.id = hp.contract_id
						inner join resource_calendar rc on rc.id = hc.resource_calendar_id
						inner join hr_payslip_worked_days hpwd on hpwd.payslip_id = hp.id
						inner join hr_payslip_worked_days_type hpwdt on hpwdt.id = hpwd.wd_type_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where hp.payslip_run_id = {pr_id}
						and hp.employee_id = {emp_id}
						and hpwd.wd_type_id in ({fal},{hext},{dvac})
						group by htd.sunat_code, he.identification_id
						""".format(
								pr_id = payslip_run.id,
								emp_id = payslip.employee_id.id,
								fal = ','.join(str(id) for id in MainParameter.wd_dnlab.ids),
								hext = ','.join(str(id) for id in MainParameter.wd_ext.ids),
								dvac = ','.join(str(id) for id in MainParameter.wd_dvac.ids)
								)
					self._cr.execute(sql)
					data = self._cr.dictfetchall()
					for line in data:
						dlab = payslip.get_dlabs()
						hlab = modf(dlab * line['hours_per_day'])
						f.write("%s|%s|%d|0|%d|0|\r\n" % (
									line['doc_type'],
									line['dni'],
									hlab[1],
									line['hext']
								))
				employees.append(payslip.employee_id.id)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.jor' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))

	def generate_plame_snl(self):
		if len(self.payslip_run_id.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.payslip_run_id.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.payslip_run_id.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.snl' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')

		for payslip_run in self.payslip_run_id.browse(self.ids):
			for payslip in payslip_run.slip_ids:
				tdoc = payslip.contract_id.employee_id.type_document_id.sunat_code.rjust(2,'0') if payslip.contract_id.employee_id.type_document_id.sunat_code else ''
				ndoc = payslip.contract_id.employee_id.identification_id
				ndias = 0
				lineas = payslip.contract_id.work_suspension_ids.filtered(lambda linea: linea.payslip_run_id.id == self.payslip_run_id.id)

				memoria=[]
				for line in lineas:
					# print("line",line.suspension_type_id)
					if line.suspension_type_id.code in memoria:
						continue
					total_dias = self.env['hr.work.suspension'].search([('payslip_run_id', '=', self.payslip_run_id.id),('contract_id', '=',payslip.contract_id.id),
																		('suspension_type_id', '=',line.suspension_type_id.id)]).mapped('days')
					# print("total_dias",sum(total_dias))

					f.write("%s|%s|%s|%s|\r\n" % (
						tdoc,
						ndoc,
						line.suspension_type_id.code,
						sum(total_dias)
					))
					memoria.append(line.suspension_type_id.code)
					# print("memoria",memoria)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.snl' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))
