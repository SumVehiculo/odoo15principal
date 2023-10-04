# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class ProductionIncomeWizard(models.TransientModel):
	_name = 'production.income.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True,default='pantalla')
	journal_id = fields.Many2one('account.journal',string='Diario')

	@api.onchange('company_id')
	def get_period(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				period = self.env['account.period'].search([('fiscal_year_id','=',fiscal_year.id),('date_start','<=',fields.Date.context_today(self)),('date_end','>=',fields.Date.context_today(self))],limit=1)
				if period:
					self.period = period
			else:
				period = self.env['account.period'].search([('date_start','<=',fields.Date.context_today(self)),('date_end','>=',fields.Date.context_today(self))],limit=1)
				if period:
					self.period = period

	def get_report(self):
		self.env.cr.execute("""
		DROP VIEW IF EXISTS production_income_book CASCADE;
		CREATE OR REPLACE view production_income_book as ("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		if self.type_show == 'pantalla':
			return {
				'name': u'Ingresos de Produccion',
				'type': 'ir.actions.act_window',
				'res_model': 'production.income.book',
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

		namefile = 'Ingresos_prod.xlsx'
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("INGRESOS DE PRODUCCION")

		worksheet.set_tab_color('blue')

		HEADERS = [u'FECHA','TIPO','SERIE',u'NUMERO','DOC. ALMACEN','RUC','EMPRESA','T. OP.','PRODUCTO','CODIGO','UNIDAD','CANTIDAD','VALOR',u'CATEGORÍA','CUENTA VALUACIÓN',u'CUENTA INGRESO',u'ALMACÉN']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		dic = self.env['production.income.book'].search([])

		for line in dic:
			worksheet.write(x,0,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,1,line.tipo if line.tipo else '',formats['especial1'])
			worksheet.write(x,2,line.serie if line.serie else '',formats['especial1'])
			worksheet.write(x,3,line.numero if line.numero else '',formats['especial1'])
			worksheet.write(x,4,line.doc if line.doc else '',formats['especial1'])
			worksheet.write(x,5,line.ruc if line.ruc else '',formats['especial1'])
			worksheet.write(x,6,line.empresa if line.empresa else '',formats['especial1'])
			worksheet.write(x,7,line.tipo_operacion if line.tipo_operacion else '',formats['especial1'])
			worksheet.write(x,8,line.producto if line.producto else '',formats['especial1'])
			worksheet.write(x,9,line.codigo if line.codigo else '',formats['especial1'])
			worksheet.write(x,10,line.unidad if line.unidad else '',formats['especial1'])
			worksheet.write(x,11,line.cantidad if line.cantidad else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.valor if line.valor else '0.00',formats['numberdos'])
			worksheet.write(x,13,line.categ_id.name if line.categ_id else '',formats['especial1'])
			worksheet.write(x,14,line.valuation_account_id.code if line.valuation_account_id else '',formats['especial1'])
			worksheet.write(x,15,line.input_account_id.code if line.input_account_id else '',formats['especial1'])
			worksheet.write(x,16,line.almacen if line.almacen else '',formats['especial1'])
			x += 1

		widths = [15,10,8,12,20,20,30,15,30,15,10,12,15,20,14,14,15]

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(u'Ingresos de Producción.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def make_invoice(self):
		if not self.journal_id:
			raise UserError('Debe seleccionar un Diario')
		self.env.cr.execute("""
		DROP VIEW IF EXISTS production_income_book CASCADE;
		CREATE OR REPLACE view production_income_book as ("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		self.env.cr.execute("""select almacen,valuation_account_id,SUM(coalesce(valor,0)) as debit from production_income_book
		group by almacen,valuation_account_id""")
		dic_debit = self.env.cr.dictfetchall()
		lineas = []
		for elem in dic_debit:
			vals = (0,0,{
				'account_id': elem['valuation_account_id'],
				'name': u'POR LOS INGRESOS DE PRODUCCIÓN DEL MES %s'%(self.period.name),
				'debit': elem['debit'],
				'credit': 0,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		self.env.cr.execute("""select almacen,input_account_id,SUM(coalesce(valor,0)) as credit from production_income_book
		group by almacen,input_account_id""")
		dic_credit = self.env.cr.dictfetchall()
		for elem in dic_credit:
			vals = (0,0,{
				'account_id': elem['input_account_id'],
				'name': u'POR LOS INGRESOS DE PRODUCCIÓN DEL MES %s'%(self.period.name),
				'debit': 0,
				'credit': elem['credit'],
				'company_id': self.company_id.id,
			})
			lineas.append(vals)

		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.period.date_end,
			'line_ids':lineas,
			'ref': 'PRO%s'%(self.period.date_end.strftime('%m%Y')),
			'glosa':u'POR LOS INGRESOS DE PRODUCCIÓN DEL MES %s'%(self.period.name),
			'move_type':'entry'})
		
		move_id.action_post()

		register = self.env['production.income.it'].search([('period_id','=',self.period.id),('company_id','=',self.company_id.id)],limit=1)
		if register:
			if register.move_id:
				if register.move_id.state != 'draft':
					register.move_id.button_cancel()
				register.move_id.line_ids.unlink()
				register.move_id.name = "/"
				register.move_id.unlink()
			
		else:
			register = self.env['production.income.it'].create({
			'company_id': self.company_id.id,
			'period_id': self.period.id})
		
		register.move_id = move_id.id

		################

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move_id.id,
		}

	def _get_sql(self,date_ini,date_end,company_id):

		sql = """SELECT
				row_number() OVER () AS id,
				T2.fecha,T2.tipo,T2.serie, T2.numero, T2.doc, T2.ruc, T2.empresa, T2.tipo_operacion, PT.name as producto, T2.codigo, T2.unidad, T2.cantidad,
				T2.valor, PT.categ_id,
				CASE WHEN vst_valuation.account_id IS NOT NULL THEN vst_valuation.account_id 
				ELSE (SELECT account_id FROM vst_property_stock_valuation_account WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS valuation_account_id,
				CASE WHEN vst_input.account_id IS NOT NULL THEN vst_input.account_id 
				ELSE (SELECT account_id FROM vst_property_stock_account_input WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS input_account_id,
				T2.almacen
				FROM
				(SELECT 
				GKV.fecha::date,
				GKV.type as tipo,
				GKV.serial as serie,
				GKV.nro as numero,
				GKV.stock_doc as doc,
				GKV.ruc as ruc,
				GKV.name as empresa,
				GKV.operation_type as tipo_operacion,
				GKV.product_id,
				GKV.default_code as codigo,
				GKV.unidad as unidad,
				GKV.ingreso as cantidad,
				GKV.debit as valor,
				GKV.almacen
				FROM get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product),(select array_agg(id) from stock_location),{company}) GKV
				LEFT JOIN stock_location ST ON ST.id = GKV.ubicacion_origen
				LEFT JOIN stock_location ST2 ON ST2.id = GKV.ubicacion_destino
				WHERE ST.usage = 'production' AND ST2.usage = 'internal' AND (GKV.fecha::date BETWEEN '{date_ini}' AND '{date_end}') AND left(GKV.stock_doc,5) = 'OP/MO' 
				AND GKV.ingreso >0)T2
				LEFT JOIN product_product PP ON PP.id = T2.product_id
				LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_valuation_account 
				WHERE company_id = {company}) vst_valuation ON vst_valuation.category_id = PT.categ_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_account_input 
				WHERE company_id = {company}) vst_input ON vst_input.category_id = PT.categ_id
		""".format(
				date_start_s = str(date_ini.year) + '0101',
				date_end_s = str(date_end).replace('-',''),
				date_ini = date_ini.strftime('%Y/%m/%d'),
				date_end = date_end.strftime('%Y/%m/%d'),
				company = company_id
			)
		return sql