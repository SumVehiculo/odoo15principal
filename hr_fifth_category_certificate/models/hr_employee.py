# -*- coding:utf-8 -*-
from odoo import api, fields, models

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from odoo.exceptions import UserError
from datetime import *
import base64

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	def get_fifth_wizard(self):
		wizard = self.env['hr.fifth.category.wizard'].create({'name': 'Certificado Quinta'})
		return {
			'type': 'ir.actions.act_window',
			'res_id': wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.fifth.category.wizard',
			'views': [[False, 'form']],
			'target': 'new',
			'context': {'employee_ids': self.ids}
		}

	def get_past_rem(self, date_from):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		sql = """
select T.employee_id,
       sum(T.total) as total
from (select hpl.employee_id,
             hpl.total
      from hr_payslip_line hpl
               inner join hr_payslip hp on hp.id = hpl.slip_id
      where hpl.date_from >= '{0}'
--        and hpl.date_from < '{1}'
        and hpl.employee_id = {1}
        and hpl.salary_rule_id in ({2},{3})
		and hp.company_id < {4}
        and hp.payslip_run_id is not null)T
group by T.employee_id
				""".format(date_from, self.id,
						   MainParameter.fifth_afect_sr_id.id,
						   MainParameter.fifth_extr_sr_id.id,
						   self.env.company.id)
		self._cr.execute(sql)
		past_lines = self._cr.dictfetchall()
		rem_ant = past_lines[0]['total'] if past_lines else 0

		grat_july = self.env['hr.gratification.line'].search([
				('gratification_id.type', '=', '07'),
				('employee_id', '=', self.id),
				('gratification_id.fiscal_year_id', '=', MainParameter.fiscal_year_id.id)
			], limit=1)
		if grat_july:
			grat_july_total=(grat_july.total_grat+grat_july.bonus_essalud)
		else:
			# grat_july=last_contract.grat_july_proyected
			grat_july_total=0

		grat_december = self.env['hr.gratification.line'].search([
				('gratification_id.type', '=', '12'),
				('employee_id', '=', self.id),
				('gratification_id.fiscal_year_id', '=', MainParameter.fiscal_year_id.id)
			], limit=1)
		if grat_december:
			grat_december_total=(grat_december.total_grat+grat_december.bonus_essalud)
		else:
			# grat_december=last_contract.grat_december_proyected
			grat_december_total=0
		# print("grat_july",grat_july)
		# print("grat_december",grat_december)
		return rem_ant + grat_july_total + grat_december_total

	def get_past_months_ret(self, date_from):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		sr_quinta_id = self.env['hr.salary.rule'].search([('company_id', '=', self.env.company.id),('code', '=', 'QUINTA')], limit=1)
		sql = """
select T.employee_id,
       sum(T.total) as total
from (select hpl.employee_id,
             hpl.total
      from hr_payslip_line hpl
               inner join hr_payslip hp on hp.id = hpl.slip_id
      where hpl.date_from >= '{0}'
--        and hpl.date_from < '{1}'
        and hpl.employee_id = {1}
        and hpl.salary_rule_id = {2}
        and hp.company_id < {3}
        and hp.payslip_run_id is not null)T
group by T.employee_id
				""".format(date_from, self.id, sr_quinta_id.id,  self.env.company.id)
		self._cr.execute(sql)
		past_lines = self._cr.dictfetchall()
		ret_ant = past_lines[0]['total'] if past_lines else 0
		return ret_ant

	def get_pdf_fifth_certificate(self, date):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		ReportBase = self.env['report.base']
		Company = self.env.company
		FiscalYear = MainParameter.fiscal_year_id
		year = int(FiscalYear.name)
		sql = """
			select hp.employee_id,
				coalesce(sum(hfcl.monthly_rem),0) as monthly_rem,
				coalesce(sum(hfcl.ext_rem),0) as ext_rem,
				coalesce(sum(hfcl.monthly_ret),0) as monthly_ret,
				coalesce(sum(hfcl.real_other_emp_rem),0) as real_other_emp_rem
			from hr_fifth_category_line hfcl 
			left join hr_payslip hp on hp.id=hfcl.slip_id
			where extract(year from hp.date_from) = %d
			and hp.employee_id= %d
			and hp.company_id= %d
			group by hp.employee_id
			"""%(year, self.id, Company.id)
		self._cr.execute(sql)
		datos = self._cr.dictfetchall()
		# print("datos",datos)
		if len(datos)==0:
			# raise UserError('Este Trabajador no tiene Quintas generadas para este ejercicio')
			real_other_emp_rem=0
		else:
			# print("REQ_ROQ",REQ_ROQ)
			real_other_emp_rem= datos[0]['real_other_emp_rem']

		REQ_ROQ = self.get_past_rem(FiscalYear.date_from)
		Net_Rent = real_other_emp_rem + REQ_ROQ

		Seven_Uit = 7 * FiscalYear.uit
		Total_Rent = Net_Rent - Seven_Uit

		Tax_Rent = self.get_past_months_ret(FiscalYear.date_from)
		Tax_Rent = 0 if Tax_Rent < 0 else Tax_Rent

		elements = []

		style_title = ParagraphStyle(name='Title', alignment=TA_CENTER, fontSize=11, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9, fontName="times-roman")
		style_right = ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10, fontName="times-roman")
		style_left = ParagraphStyle(name='Left', alignment=TA_LEFT, fontSize=10, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Left Tab', alignment=TA_LEFT, fontSize=10, fontName="times-roman", leftIndent=14)
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		spacer = Spacer(5, 20)

		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 150.0, 45.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('<strong>CERTIFICADO DE RENTAS Y RETENCIONES POR RENTAS DE QUINTA CATEGORÍA</strong>', style_title)],
				[Paragraph('<strong>(Art. 45 D.S. Nº 122.94-EF del 21/09/1994) (R.S. Nº 010-2006/SUNAT del 13/01/2006)</strong>', style_title)],
		]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)
		data = [
				[Paragraph('<strong>EJERCICIO GRAVABLE %s</strong>' % year, style_title)],
				[''],
				[Paragraph('{0} RUC Nro. {1} con domicilio fiscal en \
							{2} debidamente representada por el Sr./Sra./Srta. {3} en calidad\
							de Gerente General, identificado con DNI Nro. {4}'.format(Company.name or '',
																					  Company.vat or '',
																					  Company.street or '',
																					  MainParameter.employee_in_charge_id.name or '',
																					  MainParameter.employee_in_charge_id.identification_id or ''), style_left)],
				[''],
				[Paragraph('<strong>CERTIFICA:</strong>', style_left)],
				[''],
				[Paragraph(u'Que el Sr./Sra./Srta. {0} con Documento de identidad Nro. {1} \
							con domicilio en {2}, se le ha retenido por Impuesto a la Renta de Quinta \
							Categoría por sus funciones en el cargo de {3} correspondiente al ejercicio {4} \
							el importe de:'.format(self.name or '',
												   self.identification_id or '',
												   self.address or '',
												   self.job_title or '',
												   FiscalYear.name or ''), style_left)],
			]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)

		data = [
			[Paragraph('<strong>1. Renta Bruta:</strong>', style_left)],
			[Paragraph('1.1. Sueldo, asignaciones, gratificaciones, bonificaciones, comisiones, etc.', style_left_tab),
			 Paragraph('S/ {:,.2f}'.format(REQ_ROQ), style_left)],
			[Paragraph('1.2. Ingresos percibidos en otros empleadores', style_left_tab),
			 Paragraph('S/ {:,.2f}'.format(real_other_emp_rem), style_left)],
			[Paragraph(u'Remuneración Bruta Total', style_left_tab), Paragraph('S/ {:,.2f}'.format(Net_Rent), style_left)],
			[''],
			[Paragraph(u'<strong>2. Deducción sobre renta de quinta categoría:</strong>', style_left)],
			[Paragraph('Menos: 7UIT', style_left_tab), Paragraph('S/ {:,.2f}'.format(Seven_Uit), style_left)],
			[Paragraph('Total renta imponible ', style_left_tab), Paragraph('S/ {:,.2f}'.format(Total_Rent), style_left)],
			[''],
			[Paragraph('<strong>3.	Impuesto a la renta:</strong>', style_left),
			 Paragraph('S/ {:,.2f}'.format(Tax_Rent), style_left)],
			[''],
			[Paragraph(u'<strong>4.	Total retención efectuada:</strong>', style_left),
			 Paragraph('S/ {:,.2f}'.format(Tax_Rent), style_left)],
			[''],
			[Paragraph('<strong>Saldo por regularizar:</strong>', style_left),
			 Paragraph('S/ {:,.2f}'.format(Tax_Rent - Tax_Rent), style_left)],
			[''],
			[Paragraph('{0} {1} de {2} del {3}'.format(Company.city or '',
													   date.day,
													   MainParameter.get_month_name(date.month),
													   date.year), style_left)],
			[''], [''],
		]
		t = Table(data, [10 * cm, 10 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]))
		elements.append(t)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 45.0)
		data = [
			['', I if I else ''],
			[Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Trabajador(a)</strong>' % (
				self.name or '', self.type_document_id.name or '', self.identification_id or ''), style_center),
			 Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Empleador</strong>' % (
				 MainParameter.reprentante_legal_id.name or '',
				 MainParameter.reprentante_legal_id.l10n_latam_identification_type_id.name or '',
				 MainParameter.reprentante_legal_id.vat or ''), style_center)],
		]
		t = Table(data, [10 * cm, 10 * cm], len(data) * [0.9 * cm])
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(PageBreak())

		return elements