# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER, TA_LEFT, TA_RIGHT
import time
import decimal

class AccountMove(models.Model):
	_inherit = 'account.move'

	def generate_excel_rep_it(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Voucher.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("VOUCHER")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,5, self.name, formats['especial4'])

		worksheet.write(3,0, "Referencia:", formats['especial2'])
		worksheet.write(4,0, "Glosa:", formats['especial2'])
		worksheet.write(5,0, "Fecha Contable:", formats['especial2'])

		worksheet.write(3,1, self.ref, formats['especial4'])
		worksheet.write(4,1, self.glosa, formats['especial4'])
		worksheet.write(5,1, self.date , formats['especialdate'])

		worksheet.write(3,3, "Diario:", formats['especial2'])
		worksheet.write(4,3, "Tipo de Cambio:", formats['especial2'])
		worksheet.write(5,3, u"Compañía:", formats['especial2'])

		worksheet.write(3,4, self.journal_id.name, formats['especial4'])
		worksheet.write(4,4, str(self.currency_rate), formats['especial4'])
		worksheet.write(5,4, self.company_id.name , formats['especial4'])

		HEADERS = ['CUENTA','SOCIO','TD','NRO COMP','DESCRIPCION','CUENTA ANALITICA','IMPORTE MONEDA','MONEDA','DEBE','HABER','TC']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,7,0,formats['boldbord'])

		x=8

		debit, credit = 0, 0

		for line in self.line_ids:
			worksheet.write(x,0,line.account_id.code + ' ' + line.account_id.name if line.account_id else '',formats['especial1'])
			worksheet.write(x,1,(line.partner_id.vat if line.partner_id.vat else '') + ' ' + line.partner_id.name if line.partner_id else '',formats['especial1'])
			worksheet.write(x,2,line.type_document_id.code + ' ' + line.type_document_id.name  if line.type_document_id else '',formats['especial1'])
			worksheet.write(x,3,line.nro_comp if line.nro_comp else '',formats['especial1'])
			worksheet.write(x,4,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,5,line.analytic_account_id.name if line.analytic_account_id else '',formats['especial1'])
			worksheet.write(x,6,line.amount_currency if line.amount_currency else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.currency_id.name if line.currency_id else '',formats['especial1'])
			worksheet.write(x,8,line.debit if line.debit else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.credit if line.credit else '0.00',formats['numberdos'])
			worksheet.write(x,10,line.tc if line.tc else '1.00',formats['numbercuatro'])

			debit += line.debit if line.debit else 0
			credit += line.credit if line.credit else 0

			x += 1

		worksheet.write(x,8,debit,formats['numbertotal'])
		worksheet.write(x,9,credit,formats['numbertotal'])

		widths = [25,50,20,25,50,15,15,9,15,15,7]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		#####################################################################################################################
		
		workbook.close()

		f = open(direccion +'Voucher.xlsx', 'rb')

		return self.env['popup.it'].get_file(self.name+'.xlsx',base64.encodebytes(b''.join(f.readlines())))


	def generate_pdf_rep_it(self):
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
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** ASIENTO CONTABLE %s ***"%(self.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			c.setFont("Helvetica-Bold", 10)
			c.drawString(40,hReal-60,"Referencia")
			c.drawString(40,hReal-75,"Glosa")
			c.drawString(40,hReal-90,"Fecha Contable")
			c.drawString(470,hReal-60,"Diario")
			c.drawString(470,hReal-75,"Tipo de Cambio")
			c.drawString(470,hReal-90,u"Compañía")
			c.setFont("Helvetica", 10)
			c.drawString(150,hReal-60,(self.ref or ''))
			c.drawString(150,hReal-75,(self.glosa or ''))
			c.drawString(150,hReal-90,self.date.strftime('%Y/%m/%d'))
			c.drawString(580,hReal-60,self.journal_id.name)
			c.drawString(580,hReal-75,str(self.currency_rate))
			c.drawString(580,hReal-90,self.company_id.name)

			data= [['CUENTA','SOCIO','TD','NRO COMP','DESCRIPCION','CTA ANALITICA','IMPORTE MON','MON','DEBE','HABER','TC']]
			t=Table(data,colWidths=size_widths, rowHeights=[18])
			color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))
			t.setStyle(TableStyle([
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('BACKGROUND', (0, 0), (12, 0),color_cab),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),8)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-120)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-130
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "voucher.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [100,140,40,65,120,80,80,25,50,50,35]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-90

		c.setFont("Helvetica",9)

		for line in self.line_ids:
			first_pos = 30

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.account_id.code + ' ' + line.account_id.name if line.account_id else '',100) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( (line.partner_id.vat if line.partner_id.vat else '') + ' ' + line.partner_id.name if line.partner_id else '',150) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.type_document_id.code + ' ' + line.type_document_id.name  if line.type_document_id else '',40) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.nro_comp if line.nro_comp else '',65) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.name if line.name else '',120) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.analytic_account_id.name if line.analytic_account_id else '',90) )
			first_pos += size_widths[5]

			c.drawRightString( first_pos+80 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.amount_currency)))
			first_pos += size_widths[6]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( line.currency_id.name if line.currency_id else '',50) )
			first_pos += size_widths[7]

			c.drawRightString( first_pos+50 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.debit)))
			first_pos += size_widths[8]

			c.drawRightString( first_pos+50 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % line.credit)))
			first_pos += size_widths[9]

			c.drawRightString( first_pos+35 ,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % line.tc)))

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file(self.name+'.pdf',base64.encodebytes(b''.join(f.readlines())))