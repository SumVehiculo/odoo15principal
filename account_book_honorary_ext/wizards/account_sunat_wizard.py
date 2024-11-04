# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4,letter
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
import decimal

class AccountSunatWizard(models.TransientModel):
	_inherit = 'account.sunat.wizard'
	
	def get_plame(self,type):

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		name_doc = "0601"+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_end.month))+str(ruc)

		ctxt = ""
		separator = "|"

		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(7,self.period_id,self.company_id.id,honorary_type_date=self.type_date)

		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()
		
		if type == 1:
			name_doc += ".ps4"
			for recibo in dicc:
				ctxt += str(recibo['tdp']) + separator
				ctxt += str(recibo['docp']) + separator
				ctxt += str(recibo['apellido_p']) + separator
				ctxt += str(recibo['apellido_m']) + separator
				ctxt += str(recibo['namep']) + separator
				ctxt += str(recibo['is_not_home']) + separator
				ctxt += str(recibo['c_d_imp']) if recibo['c_d_imp'] else '0'
				ctxt += separator
				ctxt = ctxt + """\r\n"""
		else:
			name_doc += ".4ta"
			for recibo in dicc:
				ctxt += str(recibo['tdp']) + separator
				ctxt += str(recibo['docp']) + separator
				ctxt += str(recibo['honorary_type']) + separator
				ctxt += str(recibo['serie']) if recibo['serie'] else ''
				ctxt += separator
				ctxt += str(recibo['numero']) if recibo['numero'] else ''
				ctxt += separator
				ctxt += str(recibo['renta']) if recibo['renta'] else '0'
				ctxt += separator
				ctxt += str(recibo['fecha_e'].strftime('%d/%m/%Y')) + separator
				ctxt += str(recibo['fecha_p'].strftime('%d/%m/%Y')) if recibo['fecha_p'] else ''
				ctxt += separator
				ctxt += '0' if recibo['retencion'] == 0 else '1'
				ctxt += separator
				ctxt += '' + separator + '' + separator
				ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))

	def get_excel_recibos(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Recibos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self.env['account.base.sunat']._get_sql(7,self.period_id,self.company_id.id,honorary_type_date=self.type_date)

		worksheet = workbook.add_worksheet("Recibos")
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,1,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,2,line['honorary_type'] if line['honorary_type'] else '',formats['especial1'])
			worksheet.write(x,3,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,4,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,5,line['renta'] if line['renta'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['fecha_e'] if line['fecha_e'] else '',formats['dateformat'])
			worksheet.write(x,7,line['fecha_p'] if line['fecha_p'] else '',formats['dateformat'])
			worksheet.write(x,8,'0' if line['retencion'] == 0 else '1',formats['especial1'])
			worksheet.write(x,9,'',formats['especial1'])
			worksheet.write(x,10,'',formats['especial1'])
			x+=1

		widths = [9,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Recibos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Recibos.xlsx',base64.encodebytes(b''.join(f.readlines())))