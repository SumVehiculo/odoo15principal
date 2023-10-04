# -*- coding: utf-8 -*-

from socket import herror
from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountBookPerceptionWizard(models.TransientModel):
	_name = 'account.book.perception.wizard'
	_description = 'Account Book Perception Wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_from = fields.Date(string=u'Fecha Inicial')
	date_to = fields.Date(string=u'Fecha Final')
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	show_by = fields.Selection([('date','Fechas'),('period','Periodos')],string='Mostrar en base a',default='date')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True,default='pantalla')
	type =  fields.Selection([('solo','Solo Percepciones'),('det','Detalle Percepciones')],string=u'Mostrar', required=True,default='solo')
	show_header = fields.Boolean(string='Mostrar cabecera',default=False)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):
		if self.type == 'solo':
			self.env.cr.execute("""
			CREATE OR REPLACE view account_book_perception_sp as (select row_number() OVER () AS id, T.* FROM ("""+self._get_sql(self.date_from if self.show_by == 'date' else self.period_from_id.date_start,self.date_to if self.show_by == 'date' else self.period_to_id.date_end,self.company_id.id)+""")T )""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Solo Percepciones',
					'type': 'ir.actions.act_window',
					'res_model': 'account.book.perception.sp',
					'view_mode': 'tree',
					'view_type': 'form',
				}
			if self.type_show == 'excel':
				return self.get_excel()
				
		if self.type == 'det':
			self.env.cr.execute("""
			CREATE OR REPLACE view account_book_perception
			 as (select row_number() OVER () AS id, T.* FROM ("""+self._get_sql(self.date_from if self.show_by == 'date' else self.period_from_id.date_start,self.date_to if self.show_by == 'date' else self.period_to_id.date_end,self.company_id.id)+""")T )""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Detalle Percepciones',
					'type': 'ir.actions.act_window',
					'res_model': 'account.book.perception',
					'view_mode': 'tree',
					'view_type': 'form',
				}
			if self.type_show == 'excel':
				return self.get_excel()
	
	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		if self.type == 'solo':
			namefile = 'PR%s.xlsx'%(self.company_id.partner_id.vat)
		if self.type == 'det':
			namefile = 'PRDET%s.xlsx'%(self.company_id.partner_id.vat)
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		if self.type == 'solo':
			##########SOLO PERCEPCIONES############
			worksheet = workbook.add_worksheet("SOLO PERCEPCIONES")
		if self.type == 'det':
			##########DETALLE PERCEPCIONES############
			worksheet = workbook.add_worksheet("DETALLE PERCEPCIONES")

		worksheet.set_tab_color('blue')
		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,12, "PERCEPCIONES", formats['especial5'] )
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
		self.env.cr.execute(self._get_sql(self.date_from if self.show_by == 'date' else self.period_from_id.date_start,self.date_to if self.show_by == 'date' else self.period_to_id.date_end,self.company_id.id))
		res = self.env.cr.dictfetchall()

		percepcion = montof = 0
		x+=1

		for line in res:
			worksheet.write(x,0,line['periodo_con'] if line['periodo_con'] else '',formats['especial1'])
			worksheet.write(x,1,line['periodo_percep'] if line['periodo_percep'] else '',formats['especial1'])
			worksheet.write(x,2,line['fecha_uso'] if line['fecha_uso'] else '',formats['dateformat'])
			worksheet.write(x,3,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,4,line['voucher'] if line['voucher'] else '',formats['especial1'])
			worksheet.write(x,5,line['tipo_per'] if line['tipo_per'] else '',formats['especial1'])
			worksheet.write(x,6,line['ruc_agente'] if line['ruc_agente'] else '',formats['especial1'])
			worksheet.write(x,7,line['partner'] if line['partner'] else '',formats['especial1'])
			worksheet.write(x,8,line['tipo_comp'] if line['tipo_comp'] else '',formats['especial1'])
			worksheet.write(x,9,line['serie_cp'] if line['serie_cp'] else '',formats['especial1'])
			worksheet.write(x,10,line['numero_cp'] if line['numero_cp'] else '',formats['especial1'])
			worksheet.write(x,11,line['fecha_com_per'] if line['fecha_com_per'] else '',formats['dateformat'])
			worksheet.write(x,12,line['percepcion'] if line['percepcion'] else '0.00',formats['numberdos'])
			percepcion += line['percepcion'] if line['percepcion'] else 0
			if self.type == 'det':
				worksheet.write(x,13,line['t_comp'] if line['t_comp'] else '',formats['especial1'])
				worksheet.write(x,14,line['serie_comp'] if line['serie_comp'] else '',formats['especial1'])
				worksheet.write(x,15,line['numero_comp'] if line['numero_comp'] else '',formats['especial1'])
				worksheet.write(x,16,line['fecha_cp'] if line['fecha_cp'] else '',formats['dateformat'])
				worksheet.write(x,17,line['montof'] if line['montof'] else '0.00',formats['numberdos'])
				montof += line['montof'] if line['montof'] else 0
			x += 1
		
		worksheet.write(x,12,percepcion,formats['numbertotal'])
		if self.type == 'det':
			worksheet.write(x,17,montof,formats['numbertotal'])

		widths = [10,9,12,7,11,4,11,40,4,6,10,12,10]

		if self.type == 'det':
				widths.append(6)
				widths.append(7)
				widths.append(10)
				widths.append(10)

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(namefile,base64.encodebytes(b''.join(f.readlines())))

	def _get_sql(self,date_ini,date_end,company_id):
		if self.type == 'solo':
			sql = """select periodo_con::character varying, periodo_percep::character varying, fecha_uso, libro,
			voucher, tipo_per, ruc_agente, partner, tipo_comp, serie_cp, numero_cp,
			fecha_com_per, percepcion
			from get_percepciones_sp('%s','%s',%d)
			""" % (date_ini.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id)
		else:
			sql = """select periodo_con::character varying, periodo_percep::character varying, fecha_uso, libro,
			voucher, tipo_per, ruc_agente, partner, tipo_comp, serie_cp, numero_cp,
			fecha_com_per, percepcion, t_comp, serie_comp, numero_comp, fecha_cp, montof
			from get_percepciones('%s','%s',%d)
			""" % (date_ini.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id)
		
		return sql
	
	def get_header(self):
		HEADERS = ['PERIODO CON','FECHA PERC','FECHA USO','LIBRO','VOUCHER','TDP','RUC','PARTNER','TD','SERIE',u'NÚMERO','FECHA COM PER','PERCEPCION']
		if self.type == 'det':
			HEADERS.append('TD COMP')
			HEADERS.append('SERIE COMP')
			HEADERS.append('NRO COMP')
			HEADERS.append('FECHA CP')
			HEADERS.append('MONTO')
		return HEADERS