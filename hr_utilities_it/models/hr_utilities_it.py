# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

from datetime import *
import base64

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
import subprocess
import sys

class HrUtilitiesIt(models.Model):
	_name = 'hr.utilities.it'
	_description = 'Hr Utilities It'

	@api.depends('fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = i.fiscal_year_id.name

	name = fields.Char(compute=_get_name,store=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal')
	annual_rent = fields.Float(string=u'Renta Anual antes de Impuestos',digits=(64,2))
	percentage = fields.Float(string='Porcentaje',digits=(12,2))
	distribution = fields.Float(string=u'Distribución',digits=(64,2))
	utilities_line_ids = fields.One2many('hr.utilities.it.line','main_id',string='Lineas')
	sum_salary_year = fields.Float(string=u'Total Sueldos de Todo el Año',digits=(12,2),readonly=True)
	sum_number_of_days_year = fields.Float(string=u'Total Días de Laborados de Todo el Año',digits=(12,2),readonly=True)
	factor_salary = fields.Float(string=u'Factor Sueldos',digits=(12,18),readonly=True)
	factor_number_of_days = fields.Float(string=u'Factor Días de Trabajos',digits=(12,20),readonly=True)
	state = fields.Selection([('draft','Borrador'),('calculate','Calculado'),('cancel','Cancelado')],string='Estado',default='draft')
	hr_payslip_run_id = fields.Many2one('hr.payslip.run',string=u'Nómina',required=True)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.onchange('annual_rent','percentage')
	def _change_percentage_rent(self):
		for i in self:
			i.distribution = i.annual_rent * (i.percentage/100)

	def calculate(self):
		self._change_percentage_rent()
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_utility_values()
		self.env.cr.execute(self._get_sql_utlities(MainParameter.rule_total_income,MainParameter.wd_dtrab,MainParameter.wd_falt))
		res = self.env.cr.dictfetchall()
		for elem in res:
			self.env['hr.utilities.it.line'].create({
				'main_id': self.id,
				'employee_document': elem['employee_document'],
				'employee': elem['employee'],
				'employee_id': elem['employee_id'],
				'distribution_id': elem['distribution_id'],
				# 'contract_id' : elem['contract_id'],
				'salary': elem['sueldos'],
				'number_of_days': elem['dias'],
			})

		for j in self.utilities_line_ids:
			self.sum_salary_year += j.salary
			self.sum_number_of_days_year += j.number_of_days
		self.factor_salary = (self.distribution * 0.50) / self.sum_salary_year
		self.factor_number_of_days = (self.distribution * 0.50) / self.sum_number_of_days_year
		tot_salary, tot_days = 0, 0
		for i in self.utilities_line_ids:
			i.for_salary = round(i.salary * self.factor_salary,2)
			tot_salary += i.for_salary
			i.for_number_of_days = round(i.number_of_days * self.factor_number_of_days,2)
			tot_days += i.for_number_of_days

		#ROUND SALARY
		diff = 0
		if tot_salary < (self.distribution * 0.50):
			diff = (self.distribution * 0.50) - tot_salary
			self.utilities_line_ids[len(self.utilities_line_ids)-1].for_salary = self.utilities_line_ids[len(self.utilities_line_ids)-1].for_salary + diff
		if tot_salary > (self.distribution * 0.50):
			diff = tot_salary - (self.distribution * 0.50)
			self.utilities_line_ids[len(self.utilities_line_ids)-1].for_salary = self.utilities_line_ids[len(self.utilities_line_ids)-1].for_salary - diff
		
		#ROUND NUMBER OF DAYS
		diff = 0
		if tot_days < (self.distribution * 0.50):
			diff = (self.distribution * 0.50) - tot_days
			self.utilities_line_ids[len(self.utilities_line_ids)-1].for_number_of_days = self.utilities_line_ids[len(self.utilities_line_ids)-1].for_number_of_days + diff
		if tot_days > (self.distribution * 0.50):
			diff = tot_days - (self.distribution * 0.50)
			self.utilities_line_ids[len(self.utilities_line_ids)-1].for_number_of_days = self.utilities_line_ids[len(self.utilities_line_ids)-1].for_number_of_days - diff

		for i in self.utilities_line_ids:
			if i.for_number_of_days and i.for_salary:
				i.total_utilities = i.for_number_of_days + i.for_salary
		self.state = 'calculate'

	def cancel(self):
		for i in self:
			i.state = 'cancel'

	def change_draft(self):
		for i in self:
			for j in i.utilities_line_ids:
				j.unlink()
			i.sum_salary_year = 0
			i.sum_number_of_days_year = 0
			i.factor_salary = 0
			i.factor_number_of_days = 0
			i.state = 'draft'

	def action_print(self):
		for i in self:
			wizard = self.env['hr.utilities.print.wizard'].create({
				'hr_utilities_id': i.id
			})
			module = __name__.split('addons.')[1].split('.')[0]
			view = self.env.ref('%s.view_hr_utilities_print_wizard_form' % module)
			return {
				'name':u'Imprimir',
				'res_id':wizard.id,
				'view_mode': 'form',
				'res_model': 'hr.utilities.print.wizard',
				'view_id': view.id,
				'context': self.env.context,
				'target': 'new',
				'type': 'ir.actions.act_window',
			}

	def export_utilities(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_utility_values()
		Lot = self.hr_payslip_run_id
		inp_utility = MainParameter.hr_input_for_results
		for line in self.utilities_line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			utility_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_utility)
			utility_line.amount = line.total_utilities

		return self.env['popup.it'].get_message(u'Se mandó al Lote de Nóminas exitosamente.')

	def _get_sql_utlities(self,rule_total_income,wd_dtrab,wd_falt):
		sql = """
			
		SELECT coalesce(he.identification_id, '') as employee_document, he.name as employee,
        hp.employee_id,coalesce(T1.distribution_id,'') as distribution_id, sum(hpl.total) as sueldos , T2.dias 
        FROM hr_payslip_line hpl
        LEFT JOIN hr_payslip hp ON hp.id = hpl.slip_id
        LEFT JOIN hr_employee he ON he.id = hp.employee_id
        LEFT JOIN (
                SELECT hc.employee_id,had.name as distribution_id
                FROM hr_contract hc
                LEFT JOIN hr_analytic_distribution had on had.id = hc.distribution_id
                WHERE hc.state in('open')
                )T1 ON T1.employee_id = hp.employee_id
        LEFT JOIN (
			SELECT t5.employee_id,t5.dias -t6.dias as dias 
			    FROM(
                SELECT t1.employee_id,t1.dias - t2.dias as dias  
                FROM(
                    SELECT hp.employee_id,sum(coalesce(hpwd.number_of_days,0)) as dias 
                    FROM hr_payslip_worked_days hpwd
                    LEFT JOIN hr_payslip hp ON hp.id = hpwd.payslip_id
                    WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}' AND
                        to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' AND 
                        hpwd.wd_type_id in ({wd_dtrab}) AND
                        hp.company_id = {company_id}
                    group by hp.employee_id)t1
                LEFT JOIN(
                    SELECT hp.employee_id,sum(coalesce(hpwd.number_of_days,0)) as dias 
                    FROM hr_payslip_worked_days hpwd
                    LEFT JOIN hr_payslip hp ON hp.id = hpwd.payslip_id
                    WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}' AND
                        to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' AND 
                        hpwd.wd_type_id in ({wd_falt}) AND
                        hp.company_id = {company_id}
                    group by hp.employee_id)t2 ON t1.employee_id = t2.employee_id
			    )t5
			LEFT JOIN(
			SELECT hp.employee_id,coalesce(sum(hp.holidays),0) as dias FROM hr_payslip hp
			WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}' AND
				to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' AND
				hp.company_id = {company_id}
			group by hp.employee_id)t6 ON t5.employee_id = t6.employee_id
			
			) T2 ON T2.employee_id = hp.employee_id
        
        WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}'
        AND to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' 
        AND hpl.salary_rule_id = {salary_rule_id} 
        AND hp.company_id = {company_id}
        GROUP BY he.identification_id, he.name, hp.employee_id,T1.distribution_id, T2.dias
		""".format(
				year = self.fiscal_year_id.name,
				salary_rule_id = str(rule_total_income.id),
				wd_dtrab = ','.join(str(i) for i in wd_dtrab.ids),
				wd_falt = ','.join(str(i) for i in wd_falt.ids),
				company_id = str(self.company_id.id)
			)
		return sql

	def get_excel_utilidades(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Utilidades.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########UTILIDADES############
		worksheet = workbook.add_worksheet("UTILIDADES")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,7, "UTILIDADES", formats['especial3'])
		# worksheet.write(3,0,"Periodo",formats['boldbord'])
		# worksheet.write(3,1,self.payslip_run_id.name,formats['especial1'])

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",formats['boldbord'])
		worksheet.write(x,1,"EMPLEADO",formats['boldbord'])
		worksheet.write(x,2,"DISTRIBUCION ANALITICA",formats['boldbord'])
		worksheet.write(x,3,"SUELDOS",formats['boldbord'])
		worksheet.write(x,4,"DIAS LABORADOS",formats['boldbord'])
		worksheet.write(x,5,"POR SUELDOS",formats['boldbord'])
		worksheet.write(x,6,"POR DIAS LABORADOS",formats['boldbord'])
		worksheet.write(x,7,"TOTAL UTILIDADES",formats['boldbord'])
		x=6

		for line in self.utilities_line_ids:
			worksheet.write(x,0,line.employee_document if line.employee_document else '',formats['especial1'])
			worksheet.write(x,1,line.employee if line.employee else '',formats['especial1'])
			worksheet.write(x,2,line.distribution_id or '', formats['especial1'])
			worksheet.write(x,3,line.salary if line.salary else 0,formats['numberdos'])
			worksheet.write(x,4,line.number_of_days if line.number_of_days else 0,formats['numberdos'])
			worksheet.write(x,5,line.for_salary if line.for_salary else 0,formats['numberdos'])
			worksheet.write(x,6,line.for_number_of_days if line.for_number_of_days else 0,formats['numberdos'])
			worksheet.write(x,7,line.total_utilities if line.total_utilities else 0,formats['numberdos'])
			x += 1

		widths = [12,38,13,16,13,15,13,11]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()
		f = open(route + 'Utilidades.xlsx', 'rb')
		return self.env['popup.it'].get_file('Utilidades -.xlsx',base64.encodebytes(b''.join(f.readlines())))


class HrUtilitiesItLine(models.Model):
	_name = 'hr.utilities.it.line'
	_description = 'Hr Utilities It Line'

	main_id = fields.Many2one('hr.utilities.it',string='Utilidad')
	employee_document = fields.Char(string='N° Documento')
	employee = fields.Char(string='Empleado')
	employee_id = fields.Many2one('hr.employee','Empleado')
	contract_id = fields.Many2one('hr.contract','Contrato')
	distribution_id = fields.Char(string='Distribucion Analitica')
	salary = fields.Float(string='Sueldos',digits=(12,2))
	number_of_days = fields.Float(string=u'Días Laborados',digits=(12,2))
	for_salary = fields.Float(string='Por Sueldos',digits=(12,2),readonly=True)
	for_number_of_days = fields.Float(string=u'Por Días Laborados',digits=(12,2),readonly=True)
	total_utilities = fields.Float(string='Total Utilidades',digits=(12,2),readonly=True)

	def name_get(self):
		result = []
		for line in self:
			name = line.employee
			result.append((line.id, name))
		return result

	
	def _get_print(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_utility_values()
		ReportBase = self.env['report.base']

		if not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9, fontName="times-roman")

		bg_color = colors.HexColor("#f2f2f2")
		spacer = Spacer(10, 20)

		data_title = [[Paragraph('<strong>LIQUIDACIÓN DE DISTRIBUCIÓN DE UTILIDADES DEL EJERCICIO %s</strong>' % (self.main_id.fiscal_year_id.name if self.main_id.fiscal_year_id else ''),style_title)],
						[Paragraph('%s IDENTIFICADA CON RUC NRO %s  DEBIDAMENTE REPRESENTADA POR %s IDENTIFICADO CON DNI %s, EN SU CALIDAD DE EMPLEADOR Y EN CUMPLIMIENTO DE LO DISPUESTO POR EL D.L. 892 Y EL D.S. \
							NRO. 009-98-TR, DEJA CONSTANCIA DE LA DETERMINACION, DISTRIBUCION Y PAGO DE LA PARTICIPACION EN LAS UTILIDADES DEL TRABAJADOR %s' % (
								self.main_id.company_id.name.upper(),
								self.main_id.company_id.vat if self.main_id.company_id.vat else '',
								MainParameter.employee_in_charge_id.name.upper() if MainParameter.employee_in_charge_id else '',
								MainParameter.employee_in_charge_id.identification_id if MainParameter.employee_in_charge_id.identification_id else '',
								self.employee.upper() if self.employee else ''
							),
						style_cell)],
						[Paragraph('<strong>CALCULO DE LA PARTICIPACION DE LAS UTILIDADES</strong>',style_title)]]
		
		tt = Table(data_title, [18*cm],[1.5*cm,4*cm,1.2*cm])

		tt.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('BACKGROUND', (0, 0), (0, 0),bg_color),
						('BACKGROUND', (0, 2), (0, 2),bg_color),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))

		elements.append(tt)
		elements.append(spacer)

		data_distribution = [[Paragraph('<strong>1. Utilidad por distribuir</strong>',style_left),''],
							[Paragraph('- Renta anual de la empresa antes de impuestos:',style_left),Paragraph('S./%s'%(str(self.main_id.annual_rent)),style_right)],
							[Paragraph('- Porcentaje a distribuir:',style_left),Paragraph('%s %%\n'%(str(self.main_id.percentage)),style_right)],
							[Paragraph('- Monto a distribuir:',style_left),Paragraph('S./%s'%(str(self.main_id.distribution)),style_right)]]
		td = Table(data_distribution, [11*cm,7*cm],[1*cm,0.8*cm,0.8*cm,0.8*cm])

		td.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('SPAN',(0,0),(1,0)),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))

		elements.append(td)

		elements.append(spacer)

		data_calculate = [[Paragraph('<strong>2. Cálculo de la participación </strong>',style_left),''],
						[Paragraph('<strong>2.1 Según el tiempo laborado: </strong>',style_left),''],
						[Paragraph('- Número total de días laborados durante el ejericio por todos los trabajadores:',style_left),Paragraph('%s'%(str(self.main_id.sum_number_of_days_year)),style_right)],
						[Paragraph('- Numero de días laborados por el trabajador durante el ejercicio:',style_left),Paragraph('%s'%(str(self.number_of_days)),style_right)],
						[Paragraph('- Participación del trabajador por los días laborados:',style_left),Paragraph('<strong>S./%s</strong>'%(str(self.for_number_of_days)),style_right)],
						['',''],
						[Paragraph('<strong>2.2 Según las remuneraciones percibidas:</strong>',style_left),''],
						[Paragraph('- Remuneración computable total pagada  a todos los trabajadores durante el ejercicio:',style_left),Paragraph('%s'%(str(self.main_id.sum_salary_year)),style_right)],
						[Paragraph('- Remuneracion conputable total percibida por el trabajador durante el ejercicio:',style_left),Paragraph('%s'%(str(self.salary)),style_right)],
						[Paragraph('- Participacion del trabajador por el total de remuneracion percibida:',style_left),Paragraph('<strong>S./%s</strong>'%(str(self.for_salary)),style_right)],
						['',''],
						[Paragraph('- Total de la participación del trabajador en las utilidades:',style_left),Paragraph('<strong>S./%s</strong>'%(str(self.total_utilities)),style_right)]]
		
		tc = Table(data_calculate, [14*cm,4*cm],[1*cm,0.9*cm,0.8*cm,0.8*cm,0.8*cm,0.4*cm,0.9*cm,0.8*cm,0.8*cm,0.8*cm,0.8*cm,0.8*cm])

		tc.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('SPAN',(0,0),(1,0)),
						('SPAN',(0,1),(1,1)),
						('SPAN',(0,6),(1,6)),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))

		elements.append(tc)
		elements.append(spacer)
		elements.append(spacer)
		elements.append(spacer)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 150.0,
									45.0)
		data = [
			['', I if I else ''],
			[Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Trabajador(a)</strong>' % (
				self.employee_id.name or '', self.employee_id.type_document_id.name or '',
				self.employee_id.identification_id or ''), style_center),
			 Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Empleador</strong>' % (
				 MainParameter.reprentante_legal_id.name or '',
				 MainParameter.reprentante_legal_id.l10n_latam_identification_type_id.name or '',
				 MainParameter.reprentante_legal_id.vat or ''), style_center)],
		]
		t = Table(data, [10 * cm, 10 * cm], len(data) * [0.9 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)

		elements.append(PageBreak())
		return elements