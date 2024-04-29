# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountBookHonoraryWizard(models.TransientModel):
	_inherit = 'account.book.honorary.wizard'

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Libros_de_Honorarios.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBROS DE HONORARIOS############
		worksheet = workbook.add_worksheet("LIBROS DE HONORARIOS")
		worksheet.set_tab_color('blue')

		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,12, "LIBRO DE HONORARIOS", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,12,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d')),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d')),formats['especial2'])
			x+=2
		
		worksheet = ReportBase.get_headers(worksheet,self.get_header(),x,0,formats['boldbord'])
		self.env.cr.execute(self._get_sql(self.date_from if self.show_by == 'date' else self.period_from_id.date_start,self.date_to if self.show_by == 'date' else self.period_to_id.date_end,self.company_id.id,self.type_date))
		res = self.env.cr.dictfetchall()
		x+=1

		renta = retencion = neto_p = 0

		for line in res:
			worksheet.write(x,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
			worksheet.write(x,1,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,2,line['voucher'] if line['voucher'] else '',formats['especial1'])
			worksheet.write(x,3,line['fecha_e'] if line['fecha_e'] else '',formats['dateformat'])
			worksheet.write(x,4,line['fecha_p'] if line['fecha_p'] else '',formats['dateformat'])
			worksheet.write(x,5,line['td'] if line['td'] else '',formats['especial1'])
			worksheet.write(x,6,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,7,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,8,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,9,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,10,line['name'] if line['name'] else '',formats['especial1'])
			worksheet.write(x,11,line['divisa'] if line['divisa'] else '',formats['especial1'])
			worksheet.write(x,12,line['tipo_c'] if line['tipo_c'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,13,line['renta'] if line['renta'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['retencion'] if line['retencion'] else '0.00',formats['numberdos'])
			worksheet.write(x,15,line['neto_p'] if line['neto_p'] else '0.00',formats['numberdos'])
			worksheet.write(x,16,line['periodo_p'] if line['periodo_p'] else '',formats['especial1'])
			worksheet.write(x,17,line['is_not_home'] if line['is_not_home'] else '',formats['especial1'])
			renta += line['renta'] if line['renta'] else 0
			retencion += line['retencion'] if line['retencion'] else 0
			neto_p += line['neto_p'] if line['neto_p'] else 0
			x += 1
		
		worksheet.write(x,15,renta,formats['numbertotal'])
		worksheet.write(x,16,retencion,formats['numbertotal'])
		worksheet.write(x,17,neto_p,formats['numbertotal'])

		widths = [10,7,11,9,9,4,5,10,4,11,45,10,15,5,7,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Libros_de_Honorarios.xlsx', 'rb')

		return self.env['popup.it'].get_file('RH%s.xlsx'%(self.company_id.partner_id.vat),base64.encodebytes(b''.join(f.readlines())))
	
	def get_header(self):
		HEADERS = ['PERIODO','LIBRO','VOUCHER','FECHA E','FECHA P','TD','SERIE','NUMERO','TDP','RUC','NOMBRE','DIVISA','TC','RENTA','RETENCION','NETO P','PERIODO P','NO DOMICILIADO']
		return HEADERS

	def _get_sql(self,x_date_ini,x_date_end,x_company_id,x_date_type):

		sql = """select
			tt.periodo::character varying,
			tt.libro,
			tt.voucher,
			tt.fecha_e,
			tt.fecha_p,
			tt.td,
			tt.serie,
			tt.numero,
			tt.tdp,
			tt.docp,
			tt.apellido_p,
			tt.apellido_m,
			tt.namep,
			tt.divisa,
			tt.tipo_c,
			tt.renta,
			tt.retencion,
			tt.neto_p,
			tt.periodo_p,
			tt.is_not_home,
			rp.name
			from get_recxhon_1_1('%s','%s',%d,'%s') tt
			LEFT JOIN account_move am ON am.id = tt.am_id
			LEFT JOIN res_partner rp ON rp.id = am.partner_id
		""" % (x_date_ini.strftime('%Y/%m/%d'),x_date_end.strftime('%Y/%m/%d'),x_company_id,x_date_type)
		return sql

