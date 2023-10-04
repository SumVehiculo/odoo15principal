# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountSaleeRep(models.TransientModel):
	_inherit = 'account.sale.rep'

	def get_report(self):
		self.domain_dates()
		if self.type_show:
			self.env.cr.execute("""
				CREATE OR REPLACE view account_sale_book as ("""+self._get_sql()+""")""")
				
			if self.type_show == 'pantalla':
				return {
					'name': 'Registro Ventas',
					'type': 'ir.actions.act_window',
					'res_model': 'account.sale.book',
					'view_mode': 'tree',
					'view_id': self.env.ref('account_sale_rep_it.view_account_sale_book_tree').id if self.currency == 'pen' else self.env.ref('account_amount_currency_dolars_it.view_account_sale_book_usd_tree').id,
				}

			if self.type_show == 'excel':
				return self.get_excel() if self.currency == 'pen' else self.get_excel_usd()
			
			if self.type_show == 'csv':
				return self.getCsv()
		else:
			raise UserError("Es que complete el campo Mostrar en")

	def get_excel_usd(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_Ventas.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO VENTAS############
		worksheet = workbook.add_worksheet("REGISTRO VENTAS")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA CONT','LIBRO','VOUCHER','FECHA EM','FECHA VEN','TD','SERIE',u'AÑO',u'NÚMERO','TDP','RUC','PARTNER',
		'EXP','VENTA G','INAF','EXO','ISC V','ICBPER','OTROS V','IGV','TOTAL','MON','TC','FECHA DET','COMP DET',
		'FECHA DOC M','TD DOC M','SERIE M','NUMERO M','GLOSA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		#DECLARANDO TOTALES
		exp, venta_g, inaf, exo, isc_v, otros_v, icbper, igv_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0

		for line in self.env['account.sale.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha_cont if line.fecha_cont else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.fecha_e if line.fecha_e else '',formats['dateformat'])
			worksheet.write(x,5,line.fecha_v if line.fecha_v else '',formats['dateformat'])
			worksheet.write(x,6,line.td if line.td else '',formats['especial1'])
			worksheet.write(x,7,line.serie if line.serie else '',formats['especial1'])
			worksheet.write(x,8,line.anio if line.anio else '',formats['especial1'])
			worksheet.write(x,9,line.numero if line.numero else '',formats['especial1'])
			worksheet.write(x,10,line.tdp if line.tdp else '',formats['especial1'])
			worksheet.write(x,11,line.docp if line.docp else '',formats['especial1'])
			worksheet.write(x,12,line.namep if line.namep else '',formats['especial1'])
			worksheet.write(x,13,line.exp if line.exp else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.venta_g if line.venta_g else '0.00',formats['numberdos'])
			worksheet.write(x,15,line.inaf if line.inaf else '0.00',formats['numberdos'])
			worksheet.write(x,16,line.exo if line.exo else '0.00',formats['numberdos'])
			worksheet.write(x,17,line.isc_v if line.isc_v else '0.00',formats['numberdos'])
			worksheet.write(x,18,line.icbper if line.icbper else '0.00',formats['numberdos'])
			worksheet.write(x,19,line.otros_v if line.otros_v else '0.00',formats['numberdos'])
			worksheet.write(x,20,line.igv_v if line.igv_v else '0.00',formats['numberdos'])
			worksheet.write(x,21,line.total if line.total else '0.00',formats['numberdos'])
			worksheet.write(x,22,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,23,line.currency_rate if line.currency_rate else '0.0000',formats['numbercuatro'])
			worksheet.write(x,24,line.fecha_det if line.fecha_det else '',formats['dateformat'])
			worksheet.write(x,25,line.comp_det if line.comp_det else '',formats['especial1'])
			worksheet.write(x,26,line.f_doc_m if line.f_doc_m else '',formats['dateformat'])
			worksheet.write(x,27,line.td_doc_m if line.td_doc_m else '',formats['especial1'])
			worksheet.write(x,28,line.serie_m if line.serie_m else '',formats['especial1'])
			worksheet.write(x,29,line.numero_m if line.numero_m else '',formats['especial1'])
			worksheet.write(x,30,line.glosa if line.glosa else '',formats['especial1'])
			x += 1

			exp += line.exp if line.exp else 0
			venta_g += line.venta_g if line.venta_g else 0
			inaf += line.inaf if line.inaf else 0
			exo += line.exo if line.exo else 0
			isc_v += line.isc_v if line.isc_v else 0
			otros_v += line.otros_v if line.otros_v else 0
			icbper += line.icbper if line.icbper else 0
			igv_v += line.igv_v if line.igv_v else 0
			total += line.total if line.total else 0

		worksheet.write(x,13,exp,formats['numbertotal'])
		worksheet.write(x,14,venta_g,formats['numbertotal'])
		worksheet.write(x,15,inaf,formats['numbertotal'])
		worksheet.write(x,16,exo,formats['numbertotal'])
		worksheet.write(x,17,isc_v,formats['numbertotal'])
		worksheet.write(x,18,icbper,formats['numbertotal'])
		worksheet.write(x,19,otros_v,formats['numbertotal'])
		worksheet.write(x,20,igv_v,formats['numbertotal'])
		worksheet.write(x,21,total,formats['numbertotal'])

		widths = [9,12,7,11,10,10,3,10,10,10,4,11,40,10,10,10,10,10,10,10,10,12,5,7,12,12,12,12,12,12,47]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_Ventas.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro Ventas USD.xlsx',base64.encodestring(b''.join(f.readlines())))