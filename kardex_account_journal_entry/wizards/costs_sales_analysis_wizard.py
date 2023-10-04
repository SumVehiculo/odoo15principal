# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class CostsSalesAnalysisWizard(models.TransientModel):
	_name = 'costs.sales.analysis.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True,default='pantalla')

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
		#self.env['kardex.parameter.guardar.anio'].create({'fecha_inicio': self.period.fiscal_year_id.date_from, 'fecha_final':self.period.date_end}).guardar()
		self.env.cr.execute("""
		CREATE OR REPLACE view costs_sales_analysis_book as ("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		if self.type_show == 'pantalla':
			return {
				'name': u'Análisis de Costo de Venta',
				'type': 'ir.actions.act_window',
				'res_model': 'costs.sales.analysis.book',
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

		namefile = 'Analisis_Costo_Venta.xlsx'
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########ANALISIS DE COSTO DE VENTA############
		worksheet = workbook.add_worksheet("ANALISIS DE COSTO DE VENTA")

		worksheet.set_tab_color('blue')

		HEADERS = [u'ALMACÉN','PRODUCTO','CANTIDAD','VALOR','CUENTA PRODUCTO',u'CUENTA VARIACIÓN','CUENTA DE COSTO DE VENTA']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		dic = self.env['costs.sales.analysis.book'].search([])

		for line in dic:
			worksheet.write(x,0,line.almacen if line.almacen else '',formats['especial1'])
			worksheet.write(x,1,line.producto if line.producto else '',formats['especial1'])
			worksheet.write(x,2,line.cantidad if line.cantidad else '0.00',formats['numberdos'])
			worksheet.write(x,3,line.valor if line.valor else '0.00',formats['numberdos'])
			worksheet.write(x,4,line.valuation_account_id.code if line.valuation_account_id else '',formats['especial1'])
			worksheet.write(x,5,line.input_account_id.code if line.input_account_id else '',formats['especial1'])
			worksheet.write(x,6,line.output_account_id.code if line.output_account_id else '',formats['especial1'])
			x += 1

		widths = [15,30,12,15,14,14,16]

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(u'Análisis de Costo de Venta.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def make_invoice(self):
		self.env.cr.execute("""
		DROP VIEW IF EXISTS costs_sales_analysis_book CASCADE;
		CREATE OR REPLACE view costs_sales_analysis_book as ("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		self.env.cr.execute("""select almacen,output_account_id,ROUND(SUM(coalesce(valor,0)),2) as debit from costs_sales_analysis_book
		where valor >= 0
		group by almacen,output_account_id""")
		dic_debit = self.env.cr.dictfetchall()
		lineas = []
		for elem in dic_debit:
			vals = (0,0,{
				'account_id': elem['output_account_id'],
				'name': 'COSTO DE DE VENTAS %s - %s'%(elem['almacen'],self.period.name),
				'debit': elem['debit'],
				'credit': 0,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		self.env.cr.execute("""select almacen,valuation_account_id,ROUND(SUM(coalesce(valor,0)),2) as credit from costs_sales_analysis_book
		where valor >= 0
		group by almacen,valuation_account_id""")
		dic_credit = self.env.cr.dictfetchall()
		for elem in dic_credit:
			vals = (0,0,{
				'account_id': elem['valuation_account_id'],
				'name': 'COSTO DE DE VENTAS %s - %s'%(elem['almacen'],self.period.name),
				'debit': 0,
				'credit': elem['credit'],
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		destination_journal = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).destination_journal
		if not destination_journal:
			raise UserError(u'No existe Diario Asientos Automaticos en Parametros Principales de Contabilidad para su Compañía')
		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': destination_journal.id,
			'date': self.period.date_end,
			'line_ids':lineas,
			'ref': 'COSTO DE VENTAS: %s'%(self.period.name),
			'glosa':'POR EL COSTO DE VENTAS DEL PERIODO %s'%(self.period.name),
			'move_type':'entry'})

		move_id.action_post()

		register = self.env['costs.sales.analysis.it'].search([('period_id','=',self.period.id),('company_id','=',self.company_id.id)],limit=1)
		if register:
			if register.move_id:
				if register.move_id.state != 'draft':
					register.move_id.button_cancel()
				register.move_id.line_ids.unlink()
				register.move_id.name = "/"
				register.move_id.unlink()
			if register.move_return_id:
				if register.move_return_id.state != 'draft':
					register.move_return_id.button_cancel()
				register.move_return_id.line_ids.unlink()
				register.move_return_id.name = "/"
				register.move_return_id.unlink()
			
		else:
			register = self.env['costs.sales.analysis.it'].create({
			'company_id': self.company_id.id,
			'period_id': self.period.id})
		
		register.move_id = move_id.id

		#############DEVOLUCION###############
		self.env.cr.execute("""select almacen,output_account_id,ROUND(SUM(coalesce(valor,0)),2)*-1 as credit from costs_sales_analysis_book
		where valor < 0
		group by almacen,output_account_id""")
		dic_debit = self.env.cr.dictfetchall()
		lineas = []
		for elem in dic_debit:
			vals = (0,0,{
				'account_id': elem['output_account_id'],
				'name': u'DEVOLUCIÓN COSTO DE DE VENTAS %s - %s'%(elem['almacen'],self.period.name),
				'debit': 0,
				'credit': elem['credit'],
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		self.env.cr.execute("""select almacen,valuation_account_id,ROUND(SUM(coalesce(valor,0)),2)*-1 as debit from costs_sales_analysis_book
		where valor < 0
		group by almacen,valuation_account_id""")
		dic_credit = self.env.cr.dictfetchall()
		for elem in dic_credit:
			vals = (0,0,{
				'account_id': elem['valuation_account_id'],
				'name': u'DEVOLUCIÓN COSTO DE DE VENTAS %s - %s'%(elem['almacen'],self.period.name),
				'debit': elem['debit'],
				'credit': 0,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		if len(lineas)>0:
			move_return_id = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': destination_journal.id,
				'date': self.period.date_end,
				'line_ids':lineas,
				'ref': u'DEVOLUCIÓN COSTO DE VENTAS: %s'%(self.period.name),
				'glosa':u'POR LA DEVOLUCIÓN COSTO DE VENTAS DEL PERIODO %s'%(self.period.name),
				'move_type':'entry'})

			move_return_id.action_post()
			register.move_return_id = move_return_id.id

			return {
				'name': 'Asientos de Costo de Ventas',
				'view_mode': 'tree',
				'view_type': 'form',
				'view_id': self.env.ref('account.view_move_tree').id,
				'res_model': 'account.move',
				'type': 'ir.actions.act_window',
				'domain': [('id', 'in', [move_return_id.id,move_id.id])],
			}

		################

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move_id.id,
		}

	def _get_sql(self,date_ini,date_end,company_id):
		param = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1)
		if not param.location_ids_csa:
			raise UserError('Debe configurar parámetro de Ubicación Origen en Parámetros Principales de Contabilidad, Pestaña "KARDEX"')
		if not param.location_dest_ids_csa:
			raise UserError('Debe configurar parámetro de Ubicación Destino en Parámetros Principales de Contabilidad, Pestaña "KARDEX"')
		
		sql_type_operation = ""
		if param.operation_type_ids_csa:
			sql_type_operation = "AND GKV.operation_type in (%s)"%(','.join("'%s'"%str(i.code) for i in param.operation_type_ids_csa))
		
		sql_inv_origen = " AND GKV.ubicacion_origen in (%s)"%(','.join("'%s'"%str(i) for i in param.location_ids_csa.ids))
		sql_inv_origen2 = " AND GKV.ubicacion_origen in (%s)"%(','.join("'%s'"%str(i) for i in param.location_dest_ids_csa.ids))
		sql_inv_destino = " AND GKV.ubicacion_destino in (%s)"%(','.join("'%s'"%str(i) for i in param.location_dest_ids_csa.ids))
		sql_inv_destino2 = " AND GKV.ubicacion_destino in (%s)"%(','.join("'%s'"%str(i) for i in param.location_ids_csa.ids))

		sql = """SELECT
				row_number() OVER () AS id,
				T2.almacen,
				PT.name AS producto,
				T2.salida AS cantidad,
				ROUND(T2.credit,2) AS valor,
				CASE WHEN vst_valuation.account_id IS NOT NULL THEN vst_valuation.account_id
				WHEN vst_valuation.category_id IS NOT NULL AND vst_valuation.account_id IS NULL THEN NULL
				ELSE (SELECT account_id FROM vst_property_stock_valuation_account WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS valuation_account_id,
				CASE WHEN vst_input.account_id IS NOT NULL THEN vst_input.account_id 
				WHEN vst_input.category_id IS NOT NULL AND vst_input.account_id IS NULL THEN NULL
				ELSE (SELECT account_id FROM vst_property_stock_account_input WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS input_account_id,
				CASE WHEN vst_output.account_id IS NOT NULL THEN vst_output.account_id 
				WHEN vst_output.category_id IS NOT NULL AND vst_output.account_id IS NULL THEN NULL
				ELSE (SELECT account_id FROM vst_property_stock_account_output WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS output_account_id
				FROM
				(SELECT
				almacen,
				product_id,
				SUM(COALESCE(salida,0)) AS salida,
				SUM(COALESCE(credit,0)) AS credit FROM
				(SELECT 
				GKV.almacen,
				GKV.name_template,
				GKV.product_id,
				GKV.salida,
				GKV.credit
				FROM get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product),(select array_agg(id) from stock_location),{company}) GKV
				WHERE (GKV.fecha::date BETWEEN '{date_ini}' AND '{date_end}') {sql_inv_origen} {sql_inv_destino}
				{sql_type_operation}
				UNION ALL
				SELECT 
				GKV.almacen,
				GKV.name_template,
				GKV.product_id,
				-(GKV.ingreso) AS salida,
				-(GKV.debit) AS credit
				FROM get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product),(select array_agg(id) from stock_location),{company}) GKV
				WHERE (GKV.fecha::date BETWEEN '{date_ini}' AND '{date_end}') {sql_inv_origen2} {sql_inv_destino2}
				{sql_type_operation})T
				GROUP BY almacen,product_id)T2
				LEFT JOIN product_product PP ON PP.id = T2.product_id
				LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_valuation_account 
				WHERE company_id = {company}) vst_valuation ON vst_valuation.category_id = PT.categ_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_account_input 
				WHERE company_id = {company}) vst_input ON vst_input.category_id = PT.categ_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_account_output 
				WHERE company_id = {company}) vst_output ON vst_output.category_id = PT.categ_id
		""".format(
				date_start_s = str(date_ini.year) + '0101',
				date_end_s = str(date_end).replace('-',''),
				date_ini = date_ini.strftime('%Y/%m/%d'),
				date_end = date_end.strftime('%Y/%m/%d'),
				company = company_id,
				sql_inv_origen = sql_inv_origen,
				sql_inv_origen2 = sql_inv_origen2,
				sql_inv_destino = sql_inv_destino,
				sql_inv_destino2 = sql_inv_destino2,
				sql_type_operation = sql_type_operation
			)
		return sql