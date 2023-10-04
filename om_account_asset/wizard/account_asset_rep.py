# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountAssetRep(models.TransientModel):
	_name = 'account.asset.rep'
	_description = 'Account Asset Free Rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string=u'Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string=u'Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):
		self.env.cr.execute("""
			CREATE OR REPLACE view account_asset_book as ("""+self._get_sql(self.period_from.date_start,self.period_to.date_end,self.company_id.id)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Analisis de Depreciaciones',
				'type': 'ir.actions.act_window',
				'res_model': 'account.asset.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
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

		workbook = Workbook(direccion +'Analisis_de_Depreciaciones.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########ANALISIS DE DEPRECIACIONES############
		worksheet = workbook.add_worksheet("ANALISIS DE DEPRECIACIONES")
		worksheet.set_tab_color('blue')
		
		HEADERS = ['CODIGO','ACTIVO','MES','PERIODO','CATEGORIA','CTA ANALITICA','ETIQUETA ANALITICA','CTA ACTIVO','CTA GASTO','CTA DEPRECIACION','VALOR DE DEPRECIACION']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.asset.book'].search([]):
			worksheet.write(x,0,line.code if line.code else '',formats['especial1'])
			worksheet.write(x,1,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,2,line.mes if line.mes else '',formats['especial1'])
			worksheet.write(x,3,line.period if line.period else '',formats['especial1'])
			worksheet.write(x,4,line.cat_name if line.cat_name else '',formats['especial1'])
			worksheet.write(x,5,line.cta_analitica if line.cta_analitica else '',formats['especial1'])
			worksheet.write(x,6,line.eti_analitica if line.eti_analitica else '',formats['especial1'])
			worksheet.write(x,7,line.cta_activo if line.cta_activo else '',formats['especial1'])
			worksheet.write(x,8,line.cta_gasto if line.cta_gasto else '',formats['especial1'])
			worksheet.write(x,9,line.cta_depreciacion if line.cta_depreciacion else '',formats['especial1'])
			worksheet.write(x,10,line.valor_dep if line.valor_dep else '',formats['numberdos'])
			x += 1

		widths = [7,40,5,9,40,16,16,12,12,19,24]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Analisis_de_Depreciaciones.xlsx', 'rb')

		return self.env['popup.it'].get_file('Analisis de Depreciaciones.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_sql(self,x_date_ini,x_date_end,x_company_id):

		sql = """select id, code, name, mes, period, cat_name, cta_analitica, eti_analitica, cta_activo, cta_gasto, cta_depreciacion, valor_dep
                from get_activos('%s','%s',%d)
		""" % (x_date_ini.strftime('%Y/%m/%d'),
			x_date_end.strftime('%Y/%m/%d'),
			x_company_id)

		return sql
