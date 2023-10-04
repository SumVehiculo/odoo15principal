# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from lxml import etree
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
import decimal

class AccountSunatRep(models.TransientModel):
	_inherit = 'account.sunat.wizard'

	#SOLO SIRVE PARA LOS ANEXOS DE INVENTARIOS Y BALANCES
	#_______________________________________________________________________________________________________________________________________________________________
	type_show_inventory_balance  =  fields.Selection([('excel','Excel'),('pdf','PDF')],default='pdf',string=u'Mostrar en', required=True) #|
	#_______________________________________________________________________________________________________________________________________________________________


	def get_report_3_1(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_1()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_financial_situation()	
	
	def get_excel_3_1(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Situacion_Financiera.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.1 Balance General")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		finan_sit = self.env['financial.situation.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		finan_sit._get_financial_situation_sql()
		currents_B1 = self.env['financial.situation'].search([('group_balance','=','B1')])
		currents_B2 = self.env['financial.situation'].search([('group_balance','=','B2')])
		currents_B3 = self.env['financial.situation'].search([('group_balance','=','B3')])
		currents_B4 = self.env['financial.situation'].search([('group_balance','=','B4')])
		currents_B5 = self.env['financial.situation'].search([('group_balance','=','B5')])
		worksheet.merge_range(2,0,2,8, "LIBRO DE INVENTARIOS Y BALANCES - BALANCE GENERAL", formats['especial5'] )
		
		worksheet.write(4,1,"EJERCICIO",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])

		x=8
		worksheet.write(x,2,"ACTIVO",formats['especial2'])
		worksheet.write(x,5,"PASIVO Y PATRIMONIO",formats['especial2'])
		x+=2
		worksheet.write(x,2,"ACTIVO CORRIENTE",formats['especial2'])
		worksheet.write(x,5,"PASIVO CORRIENTE",formats['especial2'])
		x+=1
		total_B1 = 0
		aux=x
		
		for current in currents_B1:
			worksheet.merge_range(x,2,x,3,current.name,formats['especial1'])
			worksheet.write(x,4,str(decimal_rounding % current.total),formats['numberdos'])
			total_B1 += current.total
			x+=1
		worksheet.merge_range(x,2,x,3,"TOTAL ACTIVO CORRIENTE",formats['especial2'])
		worksheet.write(x,4,str(decimal_rounding % total_B1),formats['numbertotal'])
		pos_total = x
		total_B3 = 0
		for current in currents_B3:
			worksheet.merge_range(aux,5,aux,6,current.name,formats['especial1'])
			worksheet.write(aux,7,str(decimal_rounding % current.total),formats['numberdos'])
			total_B3 += current.total
			aux+=1
		worksheet.merge_range(pos_total,5,pos_total,6,"TOTAL ACTIVO CORRIENTE",formats['especial2'])
		worksheet.write(pos_total,7,str(decimal_rounding % total_B3),formats['numbertotal'])
		if aux > x:
			x=aux
		else:
			aux=x
		x+=3
		worksheet.write(x,2,"ACTIVO NO CORRIENTE",formats['especial2'])
		worksheet.write(x,5,"PASIVO NO CORRIENTE",formats['especial2'])
		x+=1
		aux=x
		total_B2 = 0		
		for current in currents_B2:
			worksheet.merge_range(x,2,x,3,current.name,formats['especial1'])
			worksheet.write(x,4,str(decimal_rounding % current.total),formats['numberdos'])
			total_B2 += current.total
			x+=1
		worksheet.merge_range(x,2,x,3,"TOTAL ACTIVO NO CORRIENTE",formats['especial2'])
		worksheet.write(x,4,str(decimal_rounding % total_B2),formats['numbertotal'])
		pos_total = x
		total_B4 = 0
		for current in currents_B4:
			worksheet.merge_range(aux,5,aux,6,current.name,formats['especial1'])
			worksheet.write(aux,4,str(decimal_rounding % current.total),formats['numberdos'])
			total_B4 += current.total
			aux+=1
		worksheet.merge_range(pos_total,5,pos_total,6,"TOTAL PASIVO NO CORRIENTE",formats['especial2'])
		worksheet.write(pos_total,7,str(decimal_rounding % total_B4),formats['numbertotal'])
		if aux > x:
			x=aux
		else:
			aux=x

		x+=3
		worksheet.write(x,5,"PATRIMONIO",formats['especial2'])
		x+=1
		
		total_B5 = 0
		for current in currents_B5:
			worksheet.merge_range(x,5,x,6,current.name,formats['especial1'])
			worksheet.write(x,7,str(decimal_rounding % current.total),formats['numberdos'])
			total_B5 += current.total
			x+=1
		worksheet.merge_range(x,5,x,6,"TOTAL PATRIMONIO",formats['especial2'])
		worksheet.write(x,7,str(decimal_rounding % total_B5),formats['numbertotal'])
		x+=2
		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		worksheet.merge_range(x,5,x,6,"RESULTADO DEL PERIODO",formats['especial2'])
		worksheet.write(x,7,str(decimal_rounding % period_result),formats['numbertotal'])
		x+=1
		worksheet.merge_range(x,2,x,3,"TOTAL ACTIVO ",formats['especial2'])
		worksheet.merge_range(x,5,x,6,"TOTAL PASIVO Y PATRIMONIO",formats['especial2'])
		worksheet.write(x,4,str(decimal_rounding % (total_B1 + total_B2)),formats['numbertotal'])
		worksheet.write(x,7,str(decimal_rounding % (total_B3 + total_B4 + total_B5 + period_result)),formats['numbertotal'])
		
		widths = [8,9,27,17,10,27,17,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Situacion_Financiera.xlsx', 'rb')
		return self.env['popup.it'].get_file('Situacion Financiera.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_financial_situation(self):
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Situacion_Financiera.pdf',pagesize=landscape(letter))
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [7.5*cm,2.5*cm]
		internal_height = [0.5*cm]
		external_width = [10*cm,10*cm]
		spacer = Spacer(10, 20)
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)

		finan_sit = self.env['financial.situation.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		finan_sit._get_financial_situation_sql()
		currents_B1 = self.env['financial.situation'].search([('group_balance','=','B1')])
		currents_B2 = self.env['financial.situation'].search([('group_balance','=','B2')])
		currents_B3 = self.env['financial.situation'].search([('group_balance','=','B3')])
		currents_B4 = self.env['financial.situation'].search([('group_balance','=','B4')])
		currents_B5 = self.env['financial.situation'].search([('group_balance','=','B5')])

		elements.append(Paragraph('<strong>FORMATO 3.1 : "LIBRO DE INVENTARIOS Y BALANCES - BALANCE GENERAL"</strong>', style_title))
		elements.append(Spacer(20, 10))
		elements.append(Paragraph('<strong>           EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 10))
		period_c = self.period_id.code
		data = [
			 ['',Paragraph('<strong>%s</strong>'%(period_c[4:]+'-'+period_c[:4]),style_right),'',
			  Paragraph('<strong>%s</strong>'%(period_c[4:]+'-'+period_c[:4]),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
			 [Paragraph('<strong>ACTIVO</strong>',style_left),'',
			  Paragraph('<strong>PASIVO Y PATRIMONIO</strong>',style_left),'']
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>ACTIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B1 = 0
		for current in currents_B1:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B1 += current.total
		t1 = Table(data,internal_width,y*internal_height)
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B3 = 0
		for current in currents_B3:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B3 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B1),style_right),
			 Paragraph('<strong>TOTAL PASIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B3),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)
		
		data = [
				[Paragraph('<strong>ACTIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B2 = 0
		for current in currents_B2:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B2 += current.total
		t1 = Table(data,internal_width,y*[0.8*cm])
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B4 = 0
		for current in currents_B4:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B4 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B2),style_right),
			 Paragraph('<strong>TOTAL PASIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B4),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>PATRIMONIO</strong>',style_left),'']
			   ]
		y = 1
		total_B5 = 0
		for current in currents_B5:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B5 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([['',t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			['','',
			 Paragraph('<strong>TOTAL PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B5),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		data = [
			['','',
			 Paragraph('<strong>RESULTADO DEL PERIODO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % period_result),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		data = [
			[Paragraph('<strong>TOTAL ACTIVO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B1 + total_B2)),style_right),
			 Paragraph('<strong>TOTAL PASIVO Y PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B3 + total_B4 + total_B5 + period_result)),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Situacion_Financiera.pdf', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIOS Y BALANCES - BALANCE GENERAL.pdf',base64.encodestring(b''.join(f.readlines())))


	def get_report_3_2(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_2()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_10_caja_bancos()

	def get_excel_3_2(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_10.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.2 CAJA Y BANCOS")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,8,'LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 10 '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,2,"CUENTA CONTABLE DIVISIONARIA",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x,5,"REFERENCIA DE LA CUENTA ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x,7,"SALDO CONTABLE FINAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"DENOMINACION",formats_custom['especial_2_custom'])
		worksheet.write(x,3,"ENT. FINANCIERA",formats_custom['especial_2_custom'])
		worksheet.write(x,4,"NUMERO DE CTA",formats_custom['especial_2_custom'])
		worksheet.write(x,5,"MONEDA",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,7,"ACREEDOR",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_10_caja_bancos(self.period_id.code,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		#self.env.cr.execute(_get_sql_vst_10_caja_bancos(self))
		#res = self.env.cr.dictfetchall()
		x+=1
		debe, haber = 0, 0
		for i in res:
			worksheet.write(x,1,i['cuenta'] if i['cuenta'] else '',formats['especial1'])
			worksheet.write(x,2,i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1'])
			worksheet.write(x,3,i['code_bank'] if i['code_bank'] else '',formats['especial1'])
			worksheet.write(x,4,i['account_number'] if i['account_number'] else '',formats['especial1'])
			worksheet.write(x,5,i['moneda'] if i['moneda'] else '',formats['especial1'])
			worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdos'])
			debe += i['debe']
			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdos'])
			haber += i['haber']
			x+=1
		worksheet.write(x,5,"TOTALES",formats['especial2'])
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)),formats['numbertotal'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)),formats['numbertotal'])
		widths = [8,9,42,18,17,11,15,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_10.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 10  '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_3(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_3()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_12_cliente()

	def get_excel_3_3(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_12.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.3 CLIENTES")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 12 '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL CLIENTE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO (TABLA2) ",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_12_cliente(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_12.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 12 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))

	
	def get_report_3_4(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_4()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_14_cobrar_acc_personal()

	def get_excel_3_4(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_14.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.4 Accionistas")
		worksheet.set_tab_color('blue')
		

		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 14 - CTAS x COB. A ACCIONISTAS Y PERSONAL DEL MES DE %s'%(self.period_id.name), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACIÓN DEL ACCIONISTA, SOCIO O PERSONAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_14_cobrar_acc_personal(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_14.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - CUENTA 14 - CTAS x COB. A ACCIONISTAS Y PERSONAL DEL MES DE %s'%(self.period_id.name),base64.encodebytes(b''.join(f.readlines())))
		

	def get_report_3_5(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_5()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_16_cobrar_diversas()

	def get_excel_3_5(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_16.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.5 Cuentas por cobrar")
		worksheet.set_tab_color('blue')
		
		
		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 16 - CTAS x COB. DIVERSAS DEL MES DE %s'%(self.period_id.name), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DE TERCEROS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_16_cobrar_diversas(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_16.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - CUENTA 16 - CTAS x COB. DIVERSAS DEL MES DE %s'%(self.period_id.name),base64.encodebytes(b''.join(f.readlines())))
	

	def get_report_3_6(self):
			if self.type_show_inventory_balance == 'excel':
				return self.get_excel_3_6()
			if self.type_show_inventory_balance == "pdf":
				return self.get_pdf_19_cobrar_dudosa()

	def get_excel_3_6(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'caja_19.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.6 Provision")
		worksheet.set_tab_color('blue')
		
		
		x=2
		worksheet.merge_range(x,0,x,7,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 19 - PROVISION PARA CTAS DE COBRANZA DUDOSA DEL MES DE %s'%(self.period_id.name), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DE DEUDORES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])
		
		sql = self.env['account.base.sunat'].pdf_get_sql_vst_19_cobrar_dudosa(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()

		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'caja_19.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - CUENTA 19 - PROVISION PARA CTAS DE COBRANZA DUDOSA DEL MES DE %s'%(self.period_id.name),base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_7(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_7()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_37()	
	
	def get_excel_3_7(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_37.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.7 Mercaderias")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.7: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA "', formats['especial5'] )
		worksheet.merge_range(3,0,3,8, 'CUENTA 20 - MERCADERIAS Y LA CUENTA 21 - PRODUCTOS TERMINADOS"', formats['especial5'] )


		worksheet.write(4,1,"Periodos",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
		worksheet.merge_range(7,1,7,6,u"MÉTODO DE EVALUACIÓN APLICADO: ",formats['especial2'])
		#worksheet.write(7,7,self.company_id.partner_id.name,formats['especial2'])
		
		worksheet.write(8,1,"CODIGO DE LA EXISTENCIA",formats['especial2'])
		worksheet.write(8,2,"TIPO DE EXISTENCIA (TABLA 5)",formats['especial2'])
		worksheet.write(8,3,"DESCRIPCIÓN",formats['especial2'])
		worksheet.write(8,4,u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6)",formats['especial2'])
		worksheet.write(8,5,"CANTIDAD",formats['especial2'])
		worksheet.write(8,6,"COSTO UNITARIO",formats['especial2'])
		worksheet.write(8,7,"COSTO TOTAL",formats['especial2'])
		
		worksheet.write(9,5,"COSTO TOTAL GENERAL",formats['especial2'])
		widths = [10,33,25,68,27,30,21,19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'libro_37.xlsx', 'rb')
		return self.env['popup.it'].get_file('Cuenta 20 - Mercaderias',base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_8(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_8()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_38()	
	
	def get_excel_3_8(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_38.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.8 Valores")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.8: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA LA CUENTA 31 - VALORES"', formats['especial5'] )


		worksheet.write(4,1,"Periodos",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,3,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
	
		#CABECERAS DEL REPORTE
		formats_custom={}
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom
		x=8
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,"TITULO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x,9,"VALOR EN LIBROS",formats_custom['especial_2_custom'])

		x+=1
		worksheet.write(x,1,"TIPO (TABLA 2)",formats_custom['especial_2_custom'])
		worksheet.write(x,2,u"NÚMERO",formats_custom['especial_2_custom'])
		
		worksheet.write(x,4,u"DENOMINACIÓN",formats_custom['especial_2_custom'])
		worksheet.write(x,5,u"VALOR NOMINAL UNITARIO",formats_custom['especial_2_custom'])
		worksheet.write(x,6,u"CANTIDAD",formats_custom['especial_2_custom'])

		worksheet.write(x,7,u"COSTO TOTAL",formats_custom['especial_2_custom'])
		worksheet.write(x,8,u"PROVISIÓN TOTAL",formats_custom['especial_2_custom'])
		worksheet.write(x,9,u"TOTAL NETO",formats_custom['especial_2_custom'])
		detail = self.env['sunat.table.data.38'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])
		prov_total, total = 0, 0
		x+=1
		for i in detail:
		

			worksheet.write(x,1 (i.partner_id.l10n_latam_identification_type_id.code_sunat or ''),formats['especial1'])

			worksheet.write(x,2 (i.partner_id.vat or ''),formats['especial1']) 
			

			worksheet.write(x,3 (i.partner_id.name or ''),formats['especial1']) 
			

			worksheet.write(x,4(i.name or ''),formats['especial1'])
			

			worksheet.write(x,5,'{:,.2f}'.format((i.amount or 0)),formats['numberdos'])
			

			worksheet.write(x,6,'{:,.2f}'.format((i.qty or 0)),formats['numberdos'])
		
			
			worksheet.write(x,7,'{:,.2f}'.format((i.total_cost or 0)),formats['numberdos'])
			
			
			worksheet.write(x,8,'{:,.2f}'.format((i.prov_total or 0)),formats['numberdos'])
		
			prov_total+=(i.prov_total or 0)
			
			worksheet.write(x,9,'{:,.2f}'.format((i.total or 0)),formats['numberdos'])
						
			total+=(i.total or 0)
			x+=1
		worksheet.write(x,7,"TOTALES",formats['especial2'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % prov_total)),formats['numbertotal'])
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['numbertotal'])
		widths = [8,10,20,54,26,16,17,13,13,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'libro_38.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.8: Valores',base64.encodebytes(b''.join(f.readlines())))

	
	def get_report_3_9(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_9()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_libro_39()	
	
	def get_excel_3_9(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'libro_39.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.9 INTANGIBLES")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.9: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA CUENTA 34 - INTANGIBLES""', formats['especial5'] )


		worksheet.write(4,1,"Periodos",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
		#CABECERAS DEL REPORTE
		formats_custom={}
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom
		x=8
		
		worksheet.write(x,1,"FECHA DE INICIO DE LA OPERACIÓN ",formats_custom['especial_2_custom'])
		worksheet.write(x,2,u"DESCRIPCIÓN DEL INTANGIBLE",formats_custom['especial_2_custom'])
		
		worksheet.write(x,3,u"TIPO DE INTANGIBLE (TABLA 7)",formats_custom['especial_2_custom'])
		worksheet.write(x,4,u"VALOR CONTABLE DEL INTANGIBLE",formats_custom['especial_2_custom'])
		worksheet.write(x,5,u"AMORTIZACIÓN CONTABLE ACUMULADA",formats_custom['especial_2_custom'])

		worksheet.write(x,6,u"VALOR NETO CONTABLE DEL INTANGIBLE",formats_custom['especial_2_custom'])
		detail = self.env['sunat.table.data.39'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])

		amount = amort_acum = total = 0
		x+=1
		for i in detail:
		

			worksheet.write(x,1 (i.date.strftime('%Y/%m/%d') or ''),formats['dateformat'])

			worksheet.write(x,2 (i.name or ''),formats['especial1']) 
			

			worksheet.write(x,3 (i.type or ''),formats['especial1']) 
			

			worksheet.write(x,4,'{:,.2f}'.format((i.amount or 0)),formats['numberdos'])
			amount += (i.amount or 0)

			worksheet.write(x,5,'{:,.2f}'.format((i.amort_acum or 0)),formats['numberdos'])
			amort_acum += (i.amort_acum or 0)
			
			worksheet.write(x,6,'{:,.2f}'.format((i.total or 0)),formats['numberdos'])
			total += (i.total or 0)
			
			x+=1
		worksheet.write(x,3,"TOTALES",formats['especial2'])
		worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % amount)),formats['numbertotal'])
		worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % amort_acum)),formats['numbertotal'])
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)),formats['numbertotal'])
		
		widths = [8,30,53,17,20,24,17]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'libro_39.xlsx', 'rb')
		return self.env['popup.it'].get_file('Cuenta 34 - Intangibles',base64.encodebytes(b''.join(f.readlines())))
	

	def get_report_3_10(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_10()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_40()	
	
	def get_excel_3_10(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_40.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.10 Tributos por pagar")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_40(self):
			sql = """
				SELECT
				cuenta,
				nomenclatura,
				debe-haber AS saldo
				FROM get_f1_register('%s','%s',%s,'pen')
				WHERE left(cuenta,2) = '40'
			
			""" % (self.period_id.code[:4]+'00',
				self.period_id.code,
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.10: "LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 - TRIBUTOS POR PAGAR"', formats['especial5'])

		x+=2
		
		worksheet.write(x,0,"EJERCICIO",formats['especial2'])
		worksheet.write(x,1,self.period_id.fiscal_year_id.name,formats['especial2'])
		x+=1
		worksheet.write(x,0,"RUC:",formats['especial2'])
		worksheet.write(x,1,self.company_id.partner_id.vat,formats['especial2'])
		x+=1
		worksheet.merge_range(x,0,x,5,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])

		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,0,x,1,"CUENTA Y SUB CUENTA TRIBUTOS POR PAGAR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,2,x+1,2,"SALDO FINAL",formats_custom['especial_2_custom'])		
		x+=1
		worksheet.write(x,0,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.write(x,1,"DENOMINACION",formats_custom['especial_2_custom'])

		self.env.cr.execute(self.env['account.base.sunat'].pdf_get_sql_vst_40(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id))
		res = self.env.cr.dictfetchall()

		x+=1
		saldo = 0

		for i in res:
		
			worksheet.write(x,0,  i['cuenta'] if i['cuenta'] else '',formats['especial1']) 
			

			worksheet.write(x,1, i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1']) 
			

			worksheet.write(x,2,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])),formats['numberdos'])
			saldo += i['saldo']
			x+=1
		worksheet.write(x,1,"TOTAL",formats['especial2'])
		worksheet.write(x,2,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)),formats['numbertotal'])
	
		widths = [22,77,19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_40.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))
	

	def get_report_3_11(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_11()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_41()	
	
	def get_excel_3_11(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_41.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.11 Remuneraciones")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_41(self):
			sql = """
				SELECT
				gs.cuenta,
				aa.name AS nomenclatura,
				rp.ref,
				partner,
				td_partner,
				gs.doc_partner,
				SUM(saldo_mn) AS saldo
				FROM get_saldos_sin_cierre('%s','%s',%s) gs
				LEFT JOIN account_account aa ON aa.id = gs.account_id
				LEFT JOIN res_partner rp ON rp.id = gs.partner_id
				WHERE LEFT(gs.cuenta,2) = '41' and gs.saldo_mn <> 0
				GROUP BY gs.cuenta,aa.name,rp.ref,partner,td_partner,gs.doc_partner
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 - REMUNERACIONES POR PAGAR DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x+1,2,"CUENTA Y SUBCUENTA REMUNERACIONES POR PAGAR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x,6,"TRABAJADOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"SALDO FINAL",formats_custom['especial_2_custom'])			
		x+=1
		worksheet.merge_range(x,3,x+1,3,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+1,4,"APELLIDOS Y NOMBRES",formats_custom['especial_2_custom'])	
		worksheet.merge_range(x,5,x,6,"DOC DE IDENT",formats_custom['especial_2_custom'])			
		x+=1
		worksheet.write(x,1,"CODIGO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"DENOMINACION",formats_custom['especial_2_custom'])
		worksheet.write(x,5,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_41(self))
		res = self.env.cr.dictfetchall()
		x+=1
		saldo = 0

		for i in res:
		
			worksheet.write(x,1,  i['cuenta'] if i['cuenta'] else '',formats['especial1']) 			

			worksheet.write(x,2, i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1']) 

			worksheet.write(x,3, i['ref'] if i['ref'] else '',formats['especial1'])

			worksheet.write(x,4, i['partner'] if i['partner'] else '',formats['especial1']) 

			worksheet.write(x,5, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 

			worksheet.write(x,6, i['doc_partner'] if i['doc_partner'] else '',formats['especial1'])  
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])),formats['numberdos'])
			saldo += i['saldo']
			x+=1
		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)),formats['numbertotal'])
	
		widths = [10,10,30,10,34,8,12,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_41.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 - REMUNERACIONES POR PAGAR DEL MES DE '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_12(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_12()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_42()	
	
	def get_excel_3_12(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_42.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.12 Proveedores")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_42(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '42' and saldo_mn <> 0
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 42 - CTAS POR PAGAR COMERCIALES TERCEROS DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_42(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: '+ i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_42.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 42 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_13(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_13()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_46()	
	
	def get_excel_3_13(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_46.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.13 Cuentas por pagar")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_46(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '46' and saldo_mn <> 0
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 46 - CTAS POR PAGAR DIVERSAS TERCEROS DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_46(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_46.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 46 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_14(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_14()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_47()	
	
	def get_excel_3_14(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_47.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.14 Beneficios")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_47(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '47' and saldo_mn <> 0
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 47 - CTAS POR PAGAR DIVERSAS RELACIONADAS DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_47(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_47.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 47 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_15(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_15()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cuenta_49()	
	
	def get_excel_3_15(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_49.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.15 Ganancias")
		worksheet.set_tab_color('blue')
		def _get_sql_vst_49(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos_sin_cierre('%s','%s',%s)
				WHERE LEFT(cuenta,2) = '49' and saldo_mn <> 0 
			
			""" % (self.period_id.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO DE INVENTARIO Y BALANCE - CUENTA 49 - PASIVO DIFERIDO DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,3,"INFORMACION DEL PROVEEDOR",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x+2,4,"TD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+2,5,"NUMERO DEL DOCUMENTO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+2,6,"F. DE EMISION DEL COMP.DE PAGO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+2,7,"MONTO DE LA CUENTA POR COBRAR ",formats_custom['especial_2_custom'])
		
		x+=1
		worksheet.merge_range(x,1,x,2,"DOCUMENTO DE IDENTIDAD ",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,3,"APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"NUMERO",formats_custom['especial_2_custom'])

		self.env.cr.execute(_get_sql_vst_49(self))
		res = self.env.cr.dictfetchall()
		x+=1
		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0
		for i in res:

			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

			if doc_partner != i['doc_partner']:
				worksheet.write(x,6,"TOTAL:",formats['especial2'])
				worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numberdos'])
				x+=1
				saldo_mn = 0
				doc_partner = i['doc_partner']
				worksheet.write(x,1,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '',formats['especial2'])
				x+=1

		
			worksheet.write(x,1, i['td_partner'] if i['td_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['doc_partner'] if i['doc_partner'] else '',formats['especial1']) 
			

			worksheet.write(x,3, i['partner'] if i['partner'] else '',formats['especial1']) 
		

			worksheet.write(x,4, i['td_sunat'] if i['td_sunat'] else '',formats['especial1']) 
		

			worksheet.write(x,5, i['nro_comprobante'] if i['nro_comprobante'] else '',formats['especial1']) 
			

			worksheet.write(x,6, i['fecha_doc'] if i['fecha_doc'] else '',formats['especial1']) 
			

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])),formats['numberdos'])
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']
			x+=1

		worksheet.write(x,6,"TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)),formats['numbertotal'])
		x+=1
		worksheet.write(x,6,"SALDO FINAL TOTAL",formats['especial2'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)),formats['numbertotal'])
	
	
		widths = [8,23,10,60,6,27,24,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_49.xlsx', 'rb')
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 49 '+ self.period_id.name,base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_16(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_16()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_cta_50()	
	
	def get_excel_3_16(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta50.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.16 Cuenta 50")
		worksheet.set_tab_color('blue')
		decimal_rounding = '%0.2f'
		capital = self.env['sunat.table.data.031601'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)
		
		worksheet.merge_range(2,0,2,8, 'FORMATO 3.16: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA CUENTA 50 - CAPITAL"', formats['especial5'] )
		
		worksheet.write(4,1,"EJERCICIO",formats['especial2'])
		worksheet.write(4,2,self.period_id.fiscal_year_id.name,formats['especial2'])
		worksheet.write(5,1,"RUC:",formats['especial2'])
		worksheet.write(5,2,self.company_id.partner_id.vat,formats['especial2'])
		worksheet.merge_range(6,1,6,6,"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + self.company_id.partner_id.name ,formats['especial2'])
		worksheet.merge_range(7,1,7,6,"DETALLE DE LA PARTICIPACIÓN ACCIONARIA O PARTICIPACIONES SOCIALES:",formats['especial2'])
		
		formats_custom = {}
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom
		x=8

		worksheet.merge_range(x,1,x,3,"CAPITAL SOCIAL O PARTICIPACIONES SOCIALES AL 31.12",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.importe_cap),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"VALOR NOMINAL POR ACCIÓN O PARTICIPACIÓN SOCIAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.valor_nominal),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES SUSCRITAS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.nro_acc_sus),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES PAGADAS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(capital.nro_acc_pag),formats_custom['especial_2_custom'])
		x+=1
		worksheet.merge_range(x,1,x,3,"NÚMERO DE ACCIONISTAS O SOCIOS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,4,x,6,str(len(capital.line_ids)),formats_custom['especial_2_custom'])
		x+=2

		worksheet.merge_range(x,1,x,2,u"DOCUMENTO DE IDENTIDAD",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x+1,4,u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x+1,5,u"SOCIO TIPO DE ACCIONES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,6,x+1,6,u"NÚMERO DE ACCIONES O DE PARTICIPACIONES SOCIALES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x+1,7,u"PORCENTAJE TOTAL DE PARTICIPACION",formats_custom['especial_2_custom'])
		x+=1
		worksheet.write(x,1,"TIPO (TABLA 2)",formats_custom['especial_2_custom'])
		worksheet.write(x,2,u"NÚMERO",formats_custom['especial_2_custom'])
		x+1
		num_acciones, percentage = 0, 0
		for i in capital.line_ids:		
			worksheet.write(x,1,(i.partner_id.l10n_latam_identification_type_id.code_sunat or ''),formats['especial1'])

			worksheet.write(x,2,(i.partner_id.vat or ''),formats['especial1'])

			worksheet.write(x,3,(i.partner_id.name or ''),formats['especial1'])

			worksheet.write(x,4, (i.tipo or ''),formats['especial1'])
			
			worksheet.write(x,5,(str(i.num_acciones) or ''),formats['especial1'])
			num_acciones += (i.num_acciones or 0)

			worksheet.write(x,6,(str(i.percentage) or ''),formats['especial1'])
			percentage += (i.percentage or 0)

			x+=1
		x+=1	
		worksheet.write(x,5,"TOTAL",formats['especial2'])	
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % num_acciones)),formats['numbertotal'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % percentage)),formats['numbertotal'])
		
		widths = [8,15,17,41,38,27,25,17]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta50.xlsx', 'rb')
		return self.env['popup.it'].get_file('Cuenta 50 - Capital',base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_17(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_17()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_inventario_balance()	
	
	def get_excel_3_17(self):		
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'cta_3_17.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.17 Balance")
		worksheet.set_tab_color('blue')

		x=2
		worksheet.merge_range(x,0,x,4,'LIBRO INVENTARIO Y BALANCE - BALANCE DE COMPROBACION DEL MES DE '+ self.period_id.name, formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		worksheet.merge_range(x,1,x,2,"CUENTA Y SUBCUENTA CONTABLE",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,3,x,4,"SALDOS INICIALES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,5,x,6,"MOVIMIENTOS",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,7,x,8,"SALDOS FINALES",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,9,x,10,"SALDOS FINALES DEL BALANCE GENERAL",formats_custom['especial_2_custom'])
		worksheet.merge_range(x,11,x,12,"PERDIDAS FINALES EST. DE PERDIDAS Y GANAN. POR FUNCION",formats_custom['especial_2_custom'])
		x+=1	
		worksheet.write(x,1,"CUENTA",formats_custom['especial_2_custom'])
		worksheet.write(x,2,"DENOMINACION",formats_custom['especial_2_custom'])
		worksheet.write(x,3,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,4,"ACREEDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,5,"DEBE",formats_custom['especial_2_custom'])
		worksheet.write(x,6,"HABER",formats_custom['especial_2_custom'])
		worksheet.write(x,7,"DEUDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,8,"ACREEDOR",formats_custom['especial_2_custom'])
		worksheet.write(x,9,"ACTIVO",formats_custom['especial_2_custom'])
		worksheet.write(x,10,"PASIVO",formats_custom['especial_2_custom'])
		worksheet.write(x,11,"PERDIDA",formats_custom['especial_2_custom'])
		worksheet.write(x,12,"GANANCIA",formats_custom['especial_2_custom'])
		self.env.cr.execute(self.env['account.base.sunat'].pdf_get_sql_vst_inventario(self.period_id.fiscal_year_id.date_from,self.period_id.date_end,self.company_id.id))
		res = self.env.cr.dictfetchall()
		x+=1	
		debe_inicial, haber_inicial, debe, haber, saldo_deudor, saldo_acreedor, activo, pasivo, perdifun, gananfun = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		for i in res:

		
			worksheet.write(x,1, i['cuenta'] if i['cuenta'] else '',formats['especial1']) 
			

			worksheet.write(x,2, i['nomenclatura'] if i['nomenclatura'] else '',formats['especial1']) 
			

			worksheet.write(x,3,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe_inicial'])),formats['numberdos'] )
			debe_inicial += i['debe_inicial']
			

			worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber_inicial'])),formats['numberdos'] )
			haber_inicial += i['haber_inicial']
			

			worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])),formats['numberdos'] )
			debe += i['debe']
		

			worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])),formats['numberdos'] )
			haber += i['haber']
		

			worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_deudor'])),formats['numberdos'] )
			saldo_deudor += i['saldo_deudor']
			

			worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_acreedor'])),formats['numberdos'] )
			saldo_acreedor += i['saldo_acreedor']
		

			worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['activo'])) ,formats['numberdos'])
			activo += i['activo']
			

			worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['pasivo'])) ,formats['numberdos'])
			pasivo += i['pasivo']
		

			worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['perdifun'])) ,formats['numberdos'])
			perdifun += i['perdifun']
			

			worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['gananfun'])) ,formats['numberdos'])
			gananfun += i['gananfun']
			x+=1

		worksheet.write(x,2,'TOTALES:',formats['especial2'])
		worksheet.write(x,3,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe_inicial)),formats['numbertotal'])
		worksheet.write(x,4,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber_inicial)) ,formats['numbertotal'])
		worksheet.write(x,5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) ,formats['numbertotal'])
		worksheet.write(x,6,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)),formats['numbertotal'])
		worksheet.write(x,7,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_deudor)),formats['numbertotal'])
		worksheet.write(x,8,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_acreedor)),formats['numbertotal'])
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % activo)),formats['numbertotal'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % pasivo)),formats['numbertotal'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % perdifun)),formats['numbertotal'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % gananfun)),formats['numbertotal'])
		x+=1

		worksheet.write(x,2,'GANANCIA DEL EJERCICIO:',formats['especial2'])
		final_activo = abs(activo - pasivo) if (activo - pasivo) < 0 else 0
		final_pasivo = (activo - pasivo) if (activo - pasivo) > 0 else 0
		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_activo)) ,formats['numbertotal'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_pasivo)),formats['numbertotal'])
		final_perdifun = abs(perdifun - gananfun) if (perdifun - gananfun) < 0 else 0
		final_gananfun = (perdifun - gananfun) if (perdifun - gananfun) > 0 else 0
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_perdifun)),formats['numbertotal'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_gananfun)),formats['numbertotal'])
		x+=1
	
		worksheet.write(x,2,'SUMAS IGUALES:',formats['especial2'])

		worksheet.write(x,9,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_activo + activo))) ,formats['numbertotal'])
		worksheet.write(x,10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_pasivo + pasivo))) ,formats['numbertotal'])
		worksheet.write(x,11,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_perdifun + perdifun))) ,formats['numbertotal'])
		worksheet.write(x,12,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_gananfun + gananfun))) ,formats['numbertotal'])
		widths = [10,27,10,10,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'cta_3_17.xlsx', 'rb')
		return self.env['popup.it'].get_file(u'Formato 3.17 - Balance de Comprobación.xlsx',base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_18(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_18()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_efective_flow()	

	def get_excel_3_18(self):		
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Flujo_Efectivo.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)		

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"Formato 3.18 Flujo")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.18: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE FLUJOS DE EFECTIVO', formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=1
		formats_custom = {}

		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')
		formats_custom['especial_2_custom'] = especial_2_custom

		formats_custom_1 = {}

		especial_2_custom_1 = workbook.add_format({'bold': True})
		especial_2_custom_1.set_align('center')
		especial_2_custom_1.set_align('vcenter')
		especial_2_custom_1.set_text_wrap()
		especial_2_custom_1.set_font_size(10.5)
		especial_2_custom_1.set_font_name('Times New Roman')
		formats_custom_1['especial_2_custom_1'] = especial_2_custom_1

		ENV_GROUPS = [
			{'name': 'ACTIVIDADES DE OPERACION' ,'code': ['E1','E2'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE OPERACION'},
			{'name': 'ACTIVIDADES DE INVERSION' ,'code': ['E3','E4'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE INVERSION'},
			{'name': 'ACTIVIDADES DE FINANCIAMIENTO' ,'code': ['E5','E6'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE FINANCIAMIENTO'}
		]

		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '01')],limit=1)
		wiz = self.env['efective.flow.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_ini':period_aper.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		wiz._get_efective_flow_sql()
		
		worksheet.write(x,1,"ACTIVIDADES",formats_custom_1['especial_2_custom_1'])
		x+=1
		for group in ENV_GROUPS:
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			worksheet.write(x, 1, group['name'], formats['especial2'])
			total = 0
			x += 1
			for current in currents_positive:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			worksheet.write(x, 1, 'Menos:', formats['especial2'])
			x += 1
			for current in currents_negative:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			worksheet.write(x, 1, group['total_name'], formats['especial2'])
			worksheet.write(x, 2, total, formats['numbertotal'])
			x += 2
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		worksheet.write(x, 1, 'AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO', formats['especial2'])
		worksheet.write(x, 2, sum(efective_equivalent), formats['numbertotal'])
		x += 1
		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		for current in currents:
			worksheet.write(x, 1, current.name if current.name else '',formats['especial2'])
			worksheet.write(x, 2, current.total if current.total else '0.00',formats['numbertotal'])
			x += 1
		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		worksheet.write(x, 1, 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', formats['especial2'])
		worksheet.write(x, 2, sum(final_equivalent), formats['numbertotal'])
		
		
		widths = [10,132,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Flujo_Efectivo.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.18 - Estados de Flujo de Efectivo.xlsx',base64.encodebytes(b''.join(f.readlines())))


	def get_report_3_19(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_19()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_patrimony_net()	

	def get_excel_3_19(self):		
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Patrimonio_Neto.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)		

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)
		
		especial_2_custom = workbook.add_format({'bold': True})
		especial_2_custom.set_border(style=2)
		especial_2_custom.set_align('center')
		especial_2_custom.set_align('vcenter')
		especial_2_custom.set_text_wrap()
		especial_2_custom.set_font_size(10.5)
		especial_2_custom.set_font_name('Times New Roman')

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"FORMATO 3.19 Patrimonio")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.19 : "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE CAMBIOS EN EL PATRIMONIO NETO DEL 01.01 AL %s"'%(self.period_id.date_end.strftime('%d.%m')), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2

		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['net.patrimony.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})
		self.env.cr.execute(wiz._get_net_patrimony_sql())
		data = self._cr.dictfetchall()
		HEADERS = ['CONCEPTOS','CAPITAL','ACCIONES DE INVERSION','CAPITAL ADICIONAL','RESULTADOS NO REALIZADOS',
		'EXCEDENTE DE REVALUACION','RESERVAS','RESULTADOS ACUMULADOS','TOTALES']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,1,especial_2_custom)

		x+=1

		capital, acciones, cap_add, res_no_real, exce_de_rev, reservas, res_ac, total = 0, 0, 0, 0, 0, 0, 0, 0

		for line in data:
			worksheet.write(x,1,line['glosa'] if line['glosa'] else '',formats['especial1'])
			worksheet.write(x,2,line['capital'] if line['capital']  else '0.00',formats['numberdos'])
			worksheet.write(x,3,line['acciones'] if line['acciones']  else '0.00',formats['numberdos'])
			worksheet.write(x,4,line['cap_add'] if line['cap_add'] else '0.00',formats['numberdos'])
			worksheet.write(x,5,line['res_no_real'] if line['res_no_real'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['exce_de_rev'] if line['exce_de_rev'] else '0.00',formats['numberdos'])
			worksheet.write(x,7,line['reservas'] if line['reservas'] else '0.00',formats['numberdos'])
			worksheet.write(x,8,line['res_ac'] if line['res_ac'] else '0.00',formats['numberdos'])
			worksheet.write(x,9,line['total'] if line['total'] else '0.00',formats['numbertotal'])

			capital +=line['capital'] if line['capital'] else 0
			acciones +=line['acciones'] if line['acciones'] else 0
			cap_add +=line['cap_add'] if line['cap_add'] else 0
			res_no_real +=line['res_no_real'] if line['res_no_real'] else 0
			exce_de_rev +=line['exce_de_rev'] if line['exce_de_rev'] else 0
			reservas +=line['reservas'] if line['reservas'] else 0
			res_ac +=line['res_ac'] if line['res_ac'] else 0
			total +=line['total'] if line['total'] else 0

			x += 1

		worksheet.write(x,1,'TOTALES',especial_2_custom)
		worksheet.write(x,2,capital,formats['numbertotal'])
		worksheet.write(x,3,acciones,formats['numbertotal'])
		worksheet.write(x,4,cap_add,formats['numbertotal'])
		worksheet.write(x,5,res_no_real,formats['numbertotal'])
		worksheet.write(x,6,exce_de_rev,formats['numbertotal'])
		worksheet.write(x,7,reservas,formats['numbertotal'])
		worksheet.write(x,8,res_ac,formats['numbertotal'])
		worksheet.write(x,9,total,formats['numbertotal'])

		widths = [10,57,19,19,19,19,19,19,19,19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Patrimonio_Neto.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.19 - Estado de cambios en Patrimonio Neto.xlsx',base64.encodestring(b''.join(f.readlines())))


	def get_report_3_20(self):
		if self.type_show_inventory_balance == 'excel':
			return self.get_excel_3_20()
		if self.type_show_inventory_balance == "pdf":
			return self.get_pdf_function_result()	
	
	def get_excel_3_20(self):		
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Resultado_por_Funcion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)		

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet(u"FORMATO 3.20 FUNCIÓN")
		worksheet.set_tab_color('blue')
		
		x=2
		worksheet.merge_range(x,0,x,4,'FORMATO 3.20: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE GANANCIAS Y PÉRDIDAS POR FUNCIÓN DEL 01.01 AL %s"'%(self.period_id.date_end.strftime('%d.%m')), formats['especial5'])
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.name)
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.street if self.company_id.partner_id.street else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
		x+=1
		worksheet.write(x,1,self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')
		x+=2
		
		ENV_GROUPS = [
			{'name': 'INGRESOS BRUTOS' ,'code': 'F1'},
			{'name': 'COSTOS OPERACIONALES' ,'code': 'F2'},
			{'name': 'UTILIDAD OPERATIVA' ,'code': 'F3'},
			{'name': 'RESULTADOS ANTES DE PARTICIPACIONES E IMPUESTOS' , 'code': 'F4'},
			{'name': 'UTILIDAD (PERDIDA) NETA ACT CONTINUAS', 'code': 'F5'},
			{'name': 'UTILIDAD (PERDIDA) NETA DEL EJERCICIO', 'code': 'F6'}
		]
		
		TOTALS = self.get_totals(ENV_GROUPS)
		GROUPS = self.get_function_totals(ENV_GROUPS,TOTALS)

		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['function.result.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})
		self._cr.execute(wiz._get_function_result_sql())
		
		total_F1, total_F2 = 0, 0
		for group in GROUPS:
			total_F1 += group['total'] if group['code'] == 'F1' else 0
			total_F2 += group['total'] if group['code'] == 'F2' else 0
			currents = self.env['function.result'].search([('group_function','=',group['code'])])
			for current in currents:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, (-1.0 * current.total) if current.total else '0.00', formats['numberdos'])
				x += 1
			if group['code'] == 'F2':
				worksheet.write(x, 1, group['name'], formats['especial2'])
				worksheet.write(x, 2, group['total'], formats['numbertotal'])
				x += 2
				worksheet.write(x, 1, 'UTILIDAD BRUTA', formats['especial2'])
				worksheet.write(x, 2, total_F1 + total_F2, formats['numbertotal'])
				x += 2
			else:
				worksheet.write(x, 1, group['name'], formats['especial2'])
				worksheet.write(x, 2, group['total'], formats['numbertotal'])
				x += 2

		widths = [10,60,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Resultado_por_Funcion.xlsx', 'rb')
		return self.env['popup.it'].get_file('Formato 3.20 - Estado de Ganancias y Perdidas por Funcion.xlsx',base64.encodestring(b''.join(f.readlines())))
	
	def get_totals(self,groups):
		TOTALS = []
		for group in groups:
			currents = self.env['function.result'].search([('group_function','=',group['code'])]).mapped('total')
			total = {'sum': -1.0 * sum(currents), 'code': group['code']}
			TOTALS.append(total)
		return TOTALS
		
	def get_function_totals(self,groups,totals):
		def get_sum_group(code):
			return next(filter(lambda t: t['code'] == code, totals))['sum']
		####Totals#####
		next(filter(lambda g: g['code'] == 'F1', groups))['total'] = get_sum_group('F1')
		next(filter(lambda g: g['code'] == 'F2', groups))['total'] = get_sum_group('F2')
		operative_utility = get_sum_group('F1') + get_sum_group('F2')
		next(filter(lambda g: g['code'] == 'F3', groups))['total'] = operative_utility + get_sum_group('F3')
		tax_result = operative_utility + get_sum_group('F3') + get_sum_group('F4')
		next(filter(lambda g: g['code'] == 'F4', groups))['total'] = tax_result
		continue_utility = tax_result + get_sum_group('F5')
		next(filter(lambda g: g['code'] == 'F5', groups))['total'] = continue_utility
		continue_excercise = continue_utility + get_sum_group('F6')
		next(filter(lambda g: g['code'] == 'F6', groups))['total'] = continue_excercise
		return groups
	
	def get_pdf_cta_50(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths,capital):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.16: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA CUENTA 50 - CAPITAL"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-20, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-35, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-50, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)

			c.setFont("Helvetica-Bold", 9)
			c.drawString(50,hReal-70, 'DETALLE DE LA PARTICIPACIÓN ACCIONARIA O PARTICIPACIONES SOCIALES:')

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CAPITAL SOCIAL O PARTICIPACIONES SOCIALES AL 31.12</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.importe_cap),style)],
	  			[Paragraph("<font size=9><b>VALOR NOMINAL POR ACCIÓN O PARTICIPACIÓN SOCIAL</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.valor_nominal),style)],
				[Paragraph("<font size=9><b>NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES SUSCRITAS  </b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.nro_acc_sus),style)],
				[Paragraph("<font size=9><b>NÚMERO DE ACCIONES O PARTICIPACIONES SOCIALES PAGADAS</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(capital.nro_acc_pag),style)],
				[Paragraph("<font size=9><b>NÚMERO DE ACCIONISTAS O SOCIOS</b></font>",style), Paragraph("<font size=9><b>%s</b></font>"%str(len(capital.line_ids)),style)]]
			
			t=Table(data,colWidths=[320,320], rowHeights=[18,18,18,18,18])
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-170)

			data= [[Paragraph("<font size=7.5><b>DOCUMENTO DE IDENTIDAD</b></font>",style), 
				'',
				Paragraph("<font size=7.5><b>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO</b></font>",style), 
				Paragraph("<font size=7.5><b>TIPO DE ACCIONES</b></font>",style),
				Paragraph("<font size=7.5><b>NÚMERO DE ACCIONES O DE PARTICIPACIONES SOCIALES</b></font>",style),
				Paragraph("<font size=7.5><b>PORCENTAJE TOTAL DE PARTICIPACION</b></font>",style)],
				[Paragraph("<font size=7.5><b>TIPO (TABLA 2)</b></font>",style),
				Paragraph("<font size=7.5><b>NÚMERO</b></font>",style),'','','','']]
			
			t=Table(data,colWidths=size_widths, rowHeights=[18,30])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(3,1)),
				('SPAN',(4,0),(4,1)),
				('SPAN',(5,0),(5,1)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-235)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths,capital):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths,capital)
				return pagina+1,hReal-245
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "banco_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-245
		pagina = 1

		size_widths = [60,110,300,80,100,80] #770
		capital = self.env['sunat.table.data.031601'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)

		pdf_header(self,c,wReal,hReal,size_widths,capital)

		c.setFont("Helvetica", 7)

		num_acciones, percentage = 0, 0

		for i in capital.line_ids:
			first_pos = 50

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.l10n_latam_identification_type_id.code_sunat or ''),50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.vat or ''),50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.name or ''),250) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.tipo or ''),50) )
			first_pos += size_widths[3]

			c.drawRightString( first_pos+size_widths[4] ,pos_inicial,particionar_text( (str(i.num_acciones) or ''),130) )
			first_pos += size_widths[4]
			num_acciones += (i.num_acciones or 0)

			c.drawRightString( first_pos+size_widths[5] ,pos_inicial,particionar_text( (str(i.percentage) or ''),120) )
			percentage += (i.percentage or 0)

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths,capital)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,5,pagina,size_widths,capital)

		c.setFont("Helvetica-Bold", 7)
		c.line(600,pos_inicial,780,pos_inicial)
		c.drawString( 550 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 700,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % num_acciones)) )
		c.drawRightString( 780 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % percentage)))
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths,capital)
		c.setFont("Helvetica-Bold", 7)

		c.line(600,pos_inicial,780,pos_inicial)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 50 - Capital',base64.encodestring(b''.join(f.readlines())))
	
	def get_pdf_efective_flow(self):
		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		period_ini = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '01')],limit=1)
		wiz = self.env['efective.flow.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_ini':period_aper.id,'period_from':period_ini.id,'period_to':self.period_id.id})
		wiz._get_efective_flow_sql()
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Flujo_Efectivo.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [12*cm,2.5*cm]
		internal_height = [1*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>FORMATO 3.18: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE FLUJOS DE EFECTIVO"</strong>', style_title))
		elements.append(Spacer(20, 10))
		elements.append(Paragraph('<strong>           EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 10))

		ENV_GROUPS = [
			{'name': 'ACTIVIDADES DE OPERACION' ,'code': ['E1','E2'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE OPERACION'},
			{'name': 'ACTIVIDADES DE INVERSION' ,'code': ['E3','E4'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE INVERSION'},
			{'name': 'ACTIVIDADES DE FINANCIAMIENTO' ,'code': ['E5','E6'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE FINANCIAMIENTO'}
		]

		period_c = self.period_id.code

		t = Table([
			[Paragraph('<strong>ACTIVIDADES</strong>', style_cell), 
			Paragraph('<strong>%s</strong>' % str(period_c[4:]+'-'+period_c[:4]), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(Spacer(10, 10))
		
		for group in ENV_GROUPS:
			data, y, total = [], 0, 0
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left)])
			y += 1
			for current in currents_positive:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			data.append([Paragraph('<strong>Menos:</strong>', style_left),''])
			y += 1
			for current in currents_negative:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			data.append([Paragraph('<strong>%s</strong>' % group['total_name'], style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total), style_right)])
			y += 1
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)
			elements.append(spacer)
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO</strong>', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(efective_equivalent)), style_right)]
		], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		
		data, y = [], 0
		for current in currents:
			data.append([Paragraph(current.name, style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % current.total), style_right)])
			y += 1
			
		if data:
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)

		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>%s</strong>' % 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(final_equivalent)), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Flujo_Efectivo.pdf', 'rb')
		return self.env['popup.it'].get_file('Formato 3.18 - Estados de Flujo de Efectivo.pdf',base64.encodestring(b''.join(f.readlines())))

	def get_pdf_patrimony_net(self):
		#CREANDO ARCHIVO PDF
		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['net.patrimony.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Patrimonio_Neto.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=(2200,1000), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

		elements = []
		#Estilos 
		style_left_bold = ParagraphStyle(name = 'Right',alignment = TA_RIGHT, fontSize = 19, fontName="Helvetica-Bold" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_CENTER , fontSize = 25, fontName="Helvetica-Bold" )
		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=19, fontName="Helvetica")
		style_left_cell = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=15, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=19, fontName="Helvetica")
		style_title_tab = ParagraphStyle(name = 'Center',alignment = TA_CENTER, leading = 25, fontSize = 20, fontName="Helvetica-Bold" )
		

		company = self.company_id
		elements.append(Paragraph('FORMATO 3.19 : "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE CAMBIOS EN EL PATRIMONIO NETO DEL 01.01 AL %s"'%(self.period_id.date_end.strftime('%d.%m')), style_form))
		elements.append(Spacer(20, 15))
		elements.append(Paragraph('<strong>EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 15))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 15))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 20))


	#Crear Tabla
		headers = ['CUENTAS PATRIMONIALES','CAPITAL','ACCIONES DE INVERSION','CAPITAL ADICIONAL','RESULTADOS NO REALIZADOS',
		'EXCEDENTE DE REVALUACION','RESERVAS','RESULTADOS ACUMULADOS','TOTAL']

		datos = []
		datos.append([])

		for i in headers:
			datos[0].append(Paragraph(i,style_title_tab))

		x = 1
		capital, acciones, cap_add, res_no_real, exce_de_rev, reservas, res_ac, total = 0, 0, 0, 0, 0, 0, 0, 0

		self._cr.execute(wiz._get_net_patrimony_sql())
		data = self._cr.dictfetchall()

		for fila in data:
			datos.append([])
			datos[x].append(Paragraph((fila['glosa']) if fila['glosa'] else '',style_left_cell))
			datos[x].append(Paragraph(str(fila['capital']) if fila['capital'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['acciones']) if fila['acciones'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['cap_add']) if fila['cap_add'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['res_no_real']) if fila['res_no_real'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['exce_de_rev']) if fila['exce_de_rev'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['reservas']) if fila['reservas'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['res_ac']) if fila['res_ac'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['total']) if fila['total'] else '0.00',style_left_bold))

			capital += fila['capital'] if fila['capital'] else 0
			acciones += fila['acciones'] if fila['acciones'] else 0
			cap_add += fila['cap_add'] if fila['cap_add'] else 0
			res_no_real += fila['res_no_real'] if fila['res_no_real'] else 0
			exce_de_rev += fila['exce_de_rev'] if fila['exce_de_rev'] else 0
			reservas += fila['reservas'] if fila['reservas'] else 0
			res_ac += fila['res_ac'] if fila['res_ac'] else 0
			total += fila['total'] if fila['total'] else 0

			x += 1
		
		datos.append([])
		datos[x].append(Paragraph('TOTALES',style_title_tab))
		datos[x].append(Paragraph(str(round(capital,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(acciones,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(cap_add,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(res_no_real,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(exce_de_rev,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(reservas,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(res_ac,2)),style_left_bold))
		datos[x].append(Paragraph(str(round(total,2)),style_left_bold))

		table_datos = Table(datos, colWidths=[20*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm],rowHeights=[2.5*cm] + x * [2*cm])

		#color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))

		#Estilo de Tabla
		style_table = TableStyle([
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.25, colors.black), 
				('BOX', (0,0), (-1,-1), 0.25, colors.black),
			])
		table_datos.setStyle(style_table)

		elements.append(table_datos)

		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Formato 3.19 - Estado de cambios en Patrimonio Neto.pdf',base64.encodestring(b''.join(f.readlines())))
	
	def get_pdf_function_result(self):
		period_aper = self.env['account.period'].search([('code','=',self.period_id.code[:4] + '00')],limit=1)
		wiz = self.env['function.result.wizard'].create({'fiscal_year_id':self.fiscal_year_id.id,'period_from':period_aper.id,'period_to':self.period_id.id})
		self._cr.execute(wiz._get_function_result_sql())
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Resultado_por_Funcion.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [11*cm,2.5*cm]
		internal_height = [0.5*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>FORMATO 3.20: "LIBRO DE INVENTARIOS Y BALANCES - ESTADO DE GANANCIAS Y PÉRDIDAS POR FUNCIÓN DEL 01.01 AL 31.12</strong>', style_title))
		elements.append(Spacer(20, 10))
		elements.append(Paragraph('<strong>EJERCICIO: %s</strong>'%(self.period_id.fiscal_year_id.name), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph('<strong>RUC: %s</strong>'%(self.company_id.partner_id.vat), style_left))
		elements.append(Spacer(10, 5))
		elements.append(Paragraph(u'<strong>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s</strong>'%(self.company_id.partner_id.name), style_left))
		elements.append(Spacer(10, 10))

		ENV_GROUPS = [
			{'name': 'INGRESOS BRUTOS' ,'code': 'F1'},
			{'name': 'COSTOS OPERACIONALES' ,'code': 'F2'},
			{'name': 'UTILIDAD OPERATIVA' ,'code': 'F3'},
			{'name': 'RESULTADOS ANTES DE PARTICIPACIONES E IMPUESTOS' , 'code': 'F4'},
			{'name': 'UTILIDAD (PERDIDA) NETA ACT CONTINUAS', 'code': 'F5'},
			{'name': 'UTILIDAD (PERDIDA) NETA DEL EJERCICIO', 'code': 'F6'}
		]

		period_c = self.period_id.code

		t = Table([
			[Paragraph(u'<strong>DESCRIPCIÓN</strong>', style_cell), 
			Paragraph('<strong>%s</strong>' % str(period_c[4:]+'-'+period_c[:4]), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(Spacer(10, 10))

		TOTALS = wiz.get_totals(ENV_GROUPS)
		GROUPS = wiz.get_function_totals(ENV_GROUPS,TOTALS)

		data, y = [], 0
		total_F1, total_F2 = 0, 0
		for group in GROUPS:
			total_F1 += group['total'] if group['code'] == 'F1' else 0
			total_F2 += group['total'] if group['code'] == 'F2' else 0
			currents = self.env['function.result'].search([('group_function','=',group['code'])])
			for current in currents:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % (-1.0 * current.total)) if current.total else '0.00', style_right)])
				y += 1
			if group['code'] == 'F2':
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0

				data.append([Paragraph('<strong>%s</strong>' % 'UTILIDAD BRUTA', style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_F1 + total_F2)), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0
			else:
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0

		doc.build(elements)

		f = open(direccion +'Resultado_por_Funcion.pdf', 'rb')
		return self.env['popup.it'].get_file('Formato 3.20 - Estado de Ganancias y Perdidas por Funcion.pdf',base64.encodestring(b''.join(f.readlines())))
	
	def get_pdf_libro_37(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.7: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA ')
			c.drawCentredString((wReal/2)+20,hReal-18, 'CUENTA 20 - MERCADERIAS Y LA CUENTA 21 - PRODUCTOS TERMINADOS"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-35, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-50, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-65, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)
			c.drawString(50,hReal-80, u'MÉTODO DE EVALUACIÓN APLICADO: ')

			c.setFont("Helvetica-Bold", 9)

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=7.5><b>CODIGO DE LA EXISTENCIA</b></font>",style), 
				Paragraph("<font size=7.5><b>TIPO DE EXISTENCIA (TABLA 5)</b></font>",style), 
				Paragraph(u"<font size=7.5><b>DESCRIPCIÓN</b></font>",style), 
				Paragraph(u"<font size=7.5><b>CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6)</b></font>",style),
				Paragraph("<font size=7.5><b>CANTIDAD</b></font>",style),
				Paragraph("<font size=7.5><b>COSTO UNITARIO</b></font>",style),
				Paragraph("<font size=7.5><b>COSTO TOTAL</b></font>",style)]]
			
			t=Table(data,colWidths=size_widths, rowHeights=[30])
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-120)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_37.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-120
		pagina = 1

		size_widths = [60,70,260,80,100,80,80] #770
		###DESDE AQUI
		#capital = self.env['sunat.table.data.031601'].search([('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)

		pdf_header(self,c,wReal,hReal,size_widths)

		c.setFont("Helvetica", 7)

		#for i in capital.line_ids:
		#	first_pos = 50

		#	c.setFont("Helvetica", 7)
		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.l10n_latam_identification_type_id.code_sunat or ''),50) )
		#	first_pos += size_widths[0]

		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.vat or ''),50) )
		#	first_pos += size_widths[1]

		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.name or ''),250) )
		#	first_pos += size_widths[2]

		#	c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.tipo or ''),50) )
		#	first_pos += size_widths[3]

		#	c.drawRightString( first_pos+size_widths[4] ,pos_inicial,particionar_text( (str(i.num_acciones) or ''),130) )
		#	first_pos += size_widths[4]
		#	num_acciones += (i.num_acciones or 0)

		#	c.drawRightString( first_pos+size_widths[5] ,pos_inicial,particionar_text( (str(i.percentage) or ''),120) )
		#	percentage += (i.percentage or 0)

		#	pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,5,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.drawString( 600 ,pos_inicial-10,'COSTO TOTAL GENERAL:')
		c.drawRightString( 740,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % 0)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 20 - Mercaderias',base64.encodestring(b''.join(f.readlines())))
	
	def get_pdf_libro_39(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.9: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA ')
			c.drawCentredString((wReal/2)+20,hReal-18, 'LA CUENTA 34 - INTANGIBLES"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-35, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-50, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-65, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)

			c.setFont("Helvetica-Bold", 9)

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph(u"<font size=8><b>FECHA DE INICIO DE LA OPERACIÓN</b></font>",style), 
				Paragraph(u"<font size=8><b>DESCRIPCIÓN DEL INTANGIBLE</b></font>",style), 
				Paragraph("<font size=8><b>TIPO DE INTANGIBLE (TABLA 7)</b></font>",style), 
				Paragraph(u"<font size=8><b>VALOR CONTABLE DEL INTANGIBLE</b></font>",style),
				Paragraph("<font size=8><b>AMORTIZACIÓN CONTABLE ACUMULADA</b></font>",style),
				Paragraph("<font size=8><b>VALOR NETO CONTABLE DEL INTANGIBLE</b></font>",style)]]
			
			t=Table(data,colWidths=size_widths, rowHeights=[30])
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-105)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_39.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-120
		pagina = 1

		size_widths = [100,300,70,80,100,80] #770
		
		detail = self.env['sunat.table.data.39'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])

		pdf_header(self,c,wReal,hReal,size_widths)

		amount = amort_acum = total = 0

		for i in detail:
			first_pos = 50

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,i.date.strftime('%Y/%m/%d'))
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.name or ''),280) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.type or ''),100) )
			first_pos += size_widths[2]

			c.drawRightString( first_pos+size_widths[3]-2 ,pos_inicial,'{:,.2f}'.format((i.amount or 0)) )
			first_pos += size_widths[3]
			amount += (i.amount or 0)

			c.drawRightString( first_pos+size_widths[4]-2,pos_inicial,'{:,.2f}'.format((i.amort_acum or 0)) )
			first_pos += size_widths[4]
			amort_acum += (i.amort_acum or 0)

			c.drawRightString( first_pos+size_widths[5]-2,pos_inicial,'{:,.2f}'.format((i.total or 0)) )
			first_pos += size_widths[5]
			total += (i.total or 0)

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,15,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.drawString( 450 ,pos_inicial,'TOTALES')
		c.drawRightString( 598,pos_inicial,'{:,.2f}'.format(amount) )
		c.drawRightString( 698,pos_inicial,'{:,.2f}'.format(amort_acum) )
		c.drawRightString( 778,pos_inicial,'{:,.2f}'.format(total) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 34 - Intangibles',base64.encodestring(b''.join(f.readlines())))

	def get_pdf_38(self):
		import importlib
		import sys
		importlib.reload(sys)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, 'FORMATO 3.8: "LIBRO DE INVENTARIOS Y BALANCES - DETALLE DEL SALDO DE LA ')
			c.drawCentredString((wReal/2)+20,hReal-18, 'LA CUENTA 31 - VALORES"')
			c.setFont("Helvetica-Bold", 10)
			c.drawString(50,hReal-35, 'EJERCICIO: %s'%self.fiscal_year_id.name)
			c.drawString(50,hReal-50, 'RUC: %s'%self.company_id.partner_id.vat)
			c.drawString(50,hReal-65, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: %s'%self.company_id.partner_id.name)

			c.setFont("Helvetica-Bold", 9)

			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL DEL ACCIONISTA O SOCIO</b></font>",style), 
				Paragraph("<font size=8><b>TITULO</b></font>",style),'','',
				Paragraph("<font size=8><b>VALOR EN LIBROS</b></font>",style),'',''],
				[Paragraph("<font size=8><b>TIPO (TABLA 2)</b></font>",style),
				Paragraph("<font size=8><b>NÚMERO</b></font>",style),'',
				Paragraph("<font size=8><b>DENOMINACIÓN</b></font>",style),
				Paragraph("<font size=8><b>VALOR NOMINAL UNITARIO</b></font>",style),
				Paragraph("<font size=8><b>CANTIDAD</b></font>",style),
				Paragraph("<font size=8><b>COSTO TOTAL</b></font>",style),
				Paragraph("<font size=8><b>PROVISIÓN TOTAL</b></font>",style),
				Paragraph("<font size=8><b>TOTAL NETO</b></font>",style)]]
			
			t=Table(data,colWidths=size_widths, rowHeights=[18,30])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(5,0)),
				('SPAN',(6,0),(8,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,50,500) 
			t.drawOn(c,50,hReal-130)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-142
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "banco_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-142
		pagina = 1

		size_widths = [40,70,200,130,60,50,60,60,60] #770
		detail = self.env['sunat.table.data.38'].search([('company_id', '=', self.company_id.id),('date', '>=', self.fiscal_year_id.date_from),('date', '<=', self.period_id.date_end)])

		pdf_header(self,c,wReal,hReal,size_widths)

		c.setFont("Helvetica", 7)

		prov_total, total = 0, 0

		for i in detail:
			first_pos = 50

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.l10n_latam_identification_type_id.code_sunat or ''),50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.vat or ''),50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.partner_id.name or ''),220) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (i.name or ''),140) )
			first_pos += size_widths[3]

			c.drawRightString( first_pos+size_widths[4]-2,pos_inicial,'{:,.2f}'.format((i.amount or 0)) )
			first_pos += size_widths[4]

			c.drawRightString( first_pos+size_widths[5]-2,pos_inicial,'{:,.2f}'.format((i.qty or 0)) )
			first_pos += size_widths[5]
			
			c.drawRightString( first_pos+size_widths[6]-2,pos_inicial,'{:,.2f}'.format((i.total_cost or 0)) )
			first_pos += size_widths[6]
			
			c.drawRightString( first_pos+size_widths[7]-2,pos_inicial,'{:,.2f}'.format((i.prov_total or 0)) )
			first_pos += size_widths[7]
			prov_total+=(i.prov_total or 0)
			
			c.drawRightString( first_pos+size_widths[8]-2,pos_inicial,'{:,.2f}'.format((i.total or 0)) )
			first_pos += size_widths[8]
			total+=(i.total or 0)

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,5,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.drawString( 600 ,pos_inicial,'TOTALES:')
		c.drawRightString( 718,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % prov_total)) )
		c.drawRightString( 778,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Cuenta 31 - Valores',base64.encodestring(b''.join(f.readlines())))