# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from datetime import *
from math import modf

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	name = fields.Many2one('hr.period',string=u'Periodo',required=True, readonly=True, states={'draft': [('readonly', False)]})
	slip_ids = fields.One2many(states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

	@api.onchange('name')
	def onchange_periodo(self):
		for rec in self:
			rec.date_start = rec.name.date_start
			rec.date_end = rec.name.date_end

	def action_open_payslips(self):
		rec = super(HrPayslipRun, self).action_open_payslips()
		rec['context'] = {'default_payslip_run_id': self.id}
		return rec

	def set_draft(self):
		self.slip_ids.action_payslip_cancel()
		self.slip_ids.unlink()
		self.state = 'draft'

	def compute_wds_by_lot(self):
		self.slip_ids.compute_wds()

	def recompute_payslips(self):
		self.slip_ids.generate_inputs_and_wd_lines(True)
		self.slip_ids.compute_sheet()

	def close_payroll(self):
		self.state = 'close'
		self.slip_ids.action_payslip_hecho()

	def reopen_payroll(self):
		self.state = 'verify'
		self.slip_ids.action_payslip_verify()

	def get_employees_news(self):
		wizard = self.env['hr.employee.news.wizard'].create({
			'payslip_run_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_hr_employee_news_wizard' % module)
		return {
			'name':u'Seleccionar Empleados',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.employee.news.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def tab_payroll(self):
		return {
			'name': 'Planilla Tabular',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'hr.planilla.tabular.salary.wizard',
			'context': {'default_payslip_run_id': self.id},
			'target': 'new',
		}

	# def generate_plame_wizard(self):
	# 	if len(self.ids) > 1:
	# 		raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
	# 	return {
	# 		'name': 'Generacion Archivos PLAME',
	# 		'type': 'ir.actions.act_window',
	# 		'view_mode': 'form',
	# 		'res_model': 'hr.plame.wizard',
	# 		'context': {'default_payslip_run_id': self.id},
	# 		'target': 'new',
	# 	}

	def afp_net(self):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file
		insurable_remuneration = MainParameter.insurable_remuneration
		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'AFP_NET.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("AFP NET")
		worksheet.set_tab_color('blue')
		x = 0
		for c, slip in enumerate(self.slip_ids):
			if slip.contract_id.membership_id.is_afp:
				Contract = slip.contract_id
				Employee = slip.contract_id.employee_id
				FirstContract = self.env['hr.contract'].get_first_contract(Employee, Contract)
				ir_line = self.env['hr.payslip.line'].search([('salary_rule_id', '=', insurable_remuneration.id),('slip_id', '=', slip.id)])
				resul = ''
				if Contract.date_end:
					if Contract.date_end >= self.date_end:
						resul = 'S'
					else:
						if Contract.date_end <= self.date_end and Contract.date_end >= self.date_start:
							resul = 'S'
						else:
							resul = 'N'
				else:
					if Contract.situation_id.code == '0':
						resul = 'N'
					else:
						resul = 'S'

				worksheet.write(x, 0, c)
				worksheet.write(x, 1, Contract.cuspp if Contract.cuspp else '')
				worksheet.write(x, 2, Employee.type_document_id.afp_code if Employee.type_document_id.afp_code else '')
				worksheet.write(x, 3, Employee.identification_id if Employee.identification_id else '')
				worksheet.write(x, 4, Employee.last_name if Employee.last_name else '')
				worksheet.write(x, 5, Employee.m_last_name if Employee.m_last_name else '')
				worksheet.write(x, 6, Employee.names if Employee.names else '')
				worksheet.write(x, 7, resul)
				worksheet.write(x, 8, 'S' if FirstContract.date_start >= self.date_start and FirstContract.date_start <= self.date_end and Contract.situation_id.code != '0' else 'N')
				worksheet.write(x, 9, 'S' if Contract.situation_id.code == '0' and Contract.date_end and Contract.date_end >= self.date_start and Contract.date_end <= self.date_end else 'N')
				worksheet.write(x, 10, Contract.exception if Contract.exception else '')
				worksheet.write(x, 11, ir_line.total if ir_line.total else 0.00, formats['numberdosespecial'])
				worksheet.write(x, 12, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 13, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 14, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 15, Contract.work_type if Contract.work_type else 'N')
				x += 1

		widths = [2, 15, 2, 12, 20, 20, 20, 2, 2, 2, 2, 8, 8, 8, 8, 2]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'AFP_NET.xlsx', 'rb')
		return self.env['popup.it'].get_file('AFP_NET.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def export_plame(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.rem' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
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
						inner join hr_salary_rule sr on sr.id = hpl.salary_rule_id
						inner join hr_employee he on he.id = hpl.employee_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where  hpr.id =  {payslip_run_id}
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
						inner join hr_salary_rule sr on sr.id = hpl.salary_rule_id
						inner join hr_employee he on he.id = hpl.employee_id
						inner join hr_contract hc on hc.id = hpl.contract_id
						inner join hr_membership hm on hm.id = hc.membership_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where  hpr.id = {payslip_run_id}
						and CASE WHEN hm.name <> 'ONP' THEN sr.sunat_code in ('0605','0601') ELSE sr.sunat_code in ('0605') END
						) a1
					    group by a1.sunat, a1.dni
						order by a1.dni,a1.sunat
						""".format(payslip_run_id = self.id	)
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
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.rem' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))

	def export_plame_hours(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.jor' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		# for payslip_run in self.browse(self.ids):
		# 	employees = []
		# 	for payslip in payslip_run.slip_ids:
		# 		if payslip.employee_id.id not in employees:
		sql = """
						select
						hp.id as slip_id,
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
						left join hr_type_document htd on htd.id = he.type_document_id
						where hp.payslip_run_id = {pr_id}
						and hpwd.wd_type_id in ({fal},{hext},{dvac})
						group by hp.id, htd.sunat_code, he.identification_id
						order by he.identification_id
						""".format(
									pr_id = self.id,
									fal = ','.join(str(id) for id in MainParameter.wd_dnlab.ids),
									hext = ','.join(str(id) for id in MainParameter.wd_ext.ids),
									dvac = ','.join(str(id) for id in MainParameter.wd_dvac.ids)
								)
		self._cr.execute(sql)
		data = self._cr.dictfetchall()
		for line in data:
			payslip = self.env['hr.payslip'].search([('id','=',line['slip_id'])],limit=1)
			dlab = payslip.get_dlabs()
			hlab = modf(dlab * line['hours_per_day'])
			f.write("%s|%s|%d|0|%d|0|\r\n" % (
				line['doc_type'],
				line['dni'],
				hlab[1],
				line['hext']
			))
				# employees.append(payslip.employee_id.id)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.jor' % (first, second, self.company_id.vat),base64.encodebytes(b''.join(f.readlines())))

	def export_plame_suspencion(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.snl' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.browse(self.ids):
			for payslip in payslip_run.slip_ids:
				tdoc = payslip.contract_id.employee_id.type_document_id.sunat_code.rjust(2,'0') if payslip.contract_id.employee_id.type_document_id.sunat_code else ''
				ndoc = payslip.contract_id.employee_id.identification_id
				ndias = 0
				lineas = payslip.contract_id.work_suspension_ids.filtered(lambda linea: linea.payslip_run_id.id == self.id)

				memoria=[]
				for line in lineas:
					# print("line",line.suspension_type_id)
					if line.suspension_type_id.code in memoria:
						continue
					total_dias = self.env['hr.work.suspension'].search([('payslip_run_id', '=', self.id),('contract_id', '=',payslip.contract_id.id),
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
