# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class KardexEntryIncomeWizard(models.TransientModel):
	_name = 'kardex.entry.income.wizard'

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
		self.env.cr.execute("""DELETE FROM kardex_entry_income_book""")
		self.env.cr.execute("""
		INSERT INTO kardex_entry_income_book (fecha,tipo,serie,numero,doc_almacen,ruc,empresa,tipo_op,tipo_name, producto, default_code, unidad, qty, amount, cta_debe, cta_haber, origen, destino, almacen, analytic_account_id,analytic_tag_id) 
		("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		if self.type_show == 'pantalla':
			return {
				'name': u'Detalle de Ingresos',
				'type': 'ir.actions.act_window',
				'res_model': 'kardex.entry.income.book',
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

		namefile = 'Detalle_ingreso.xlsx'
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########DETALLE INGRESO############
		worksheet = workbook.add_worksheet("DETALLE INGRESO")

		worksheet.set_tab_color('blue')

		HEADERS = [u'FECHA','TIPO','SERIE',u'NÚMERO',u'DOC. ALMACÉN',u'RUC',u'EMPRESA',u'T. OP.',u'PRODUCTO',u'CODIGO PRODUCTO',u'UNIDAD','CANTIDAD','COSTO',
		'CTA DEBE','CTA HABER',u'UBICACIÓN ORIGEN',u'UBICACIÓN DESTINO',u'ALMACÉN',u'CTA ANALÍTICA','ETIQUETA ANALITICA']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		dic = self.env['kardex.entry.income.book'].search([])

		for line in dic:
			worksheet.write(x,0,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,1,line.tipo if line.tipo else '',formats['especial1'])
			worksheet.write(x,2,line.serie if line.serie else '',formats['especial1'])
			worksheet.write(x,3,line.numero if line.numero else '',formats['especial1'])
			worksheet.write(x,4,line.doc_almacen if line.doc_almacen else '',formats['especial1'])
			worksheet.write(x,5,line.ruc if line.ruc else '',formats['especial1'])
			worksheet.write(x,6,line.empresa if line.empresa else '',formats['especial1'])
			worksheet.write(x,7,line.tipo_op if line.tipo_op else '',formats['especial1'])
			worksheet.write(x,8,line.producto if line.producto else '',formats['especial1'])
			worksheet.write(x,9,line.default_code if line.default_code else '',formats['especial1'])
			worksheet.write(x,10,line.unidad if line.unidad else '',formats['especial1'])
			worksheet.write(x,11,line.qty if line.qty else 0,formats['numberdos'])
			worksheet.write(x,12,line.amount if line.amount else '0.00',formats['numberocho'])
			worksheet.write(x,13,line.cta_debe.code if line.cta_debe else '',formats['especial1'])
			worksheet.write(x,14,line.cta_haber.code if line.cta_haber else '',formats['especial1'])
			worksheet.write(x,15,line.origen if line.origen else '',formats['especial1'])
			worksheet.write(x,16,line.destino if line.destino else '',formats['especial1'])
			worksheet.write(x,17,line.almacen if line.almacen else '',formats['especial1'])
			worksheet.write(x,18,line.analytic_account_id.name if line.analytic_account_id else '',formats['especial1'])
			worksheet.write(x,19,line.analytic_tag_id.name if line.analytic_tag_id else '',formats['especial1'])
			x += 1

		widths = [10,6,7,9,16,12,48,8,41,20,9,11,14,15,15,33,33,11,22,20]

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(u'Detalle ingresos.xlsx',base64.encodestring(b''.join(f.readlines())))

	def make_invoice(self):
		self.env.cr.execute("""DELETE FROM kardex_entry_income_book""")
		self.env.cr.execute("""
		INSERT INTO kardex_entry_income_book (fecha,tipo,serie,numero,doc_almacen,ruc,empresa,tipo_op,tipo_name, producto, default_code, unidad, qty, amount, cta_debe, cta_haber, origen, destino, almacen, analytic_account_id,analytic_tag_id) 
		("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		self.env.cr.execute("""select tipo_op from kardex_entry_income_book
		group by tipo_op""")
		res = self.env.cr.dictfetchall()
		stock_journal_id = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).stock_journal_id
		if not stock_journal_id:
			raise UserError(u'No existe Diario de Existencias en Parametros Principales de Contabilidad para su Compañía')
		
		register = self.env['kardex.entry.income.it'].search([('period_id','=',self.period.id),('company_id','=',self.company_id.id)],limit=1)
		if register:
			if register.move_ids:
				for move in register.move_ids:
					if move.state != 'draft':
						move.button_cancel()
					move.line_ids.unlink()
					move.name = "/"
					move.unlink()
			
		else:
			register = self.env['kardex.entry.income.it'].create({
			'company_id': self.company_id.id,
			'period_id': self.period.id})
		
		for top in res:
			self.env.cr.execute("""select tipo_name,cta_debe,analytic_account_id,analytic_tag_id, sum(round(coalesce(amount,0),2)) as debit from kardex_entry_income_book
			where tipo_op = '%s'
			group by tipo_name,almacen,cta_debe,analytic_account_id,analytic_tag_id"""%top['tipo_op'])
			dic_debit = self.env.cr.dictfetchall()
			lineas = []
			for elem in dic_debit:
				vals = (0,0,{
					'account_id': elem['cta_debe'],
					'name':elem['tipo_name'],
					'debit': elem['debit'],
					'credit': 0,
					'analytic_account_id': elem['analytic_account_id'],
					'analytic_tag_ids': [(6, 0, [elem['analytic_tag_id']])] if elem['analytic_tag_id'] else None,
					'company_id': self.company_id.id,
				})
				lineas.append(vals)
			self.env.cr.execute("""select tipo_name,cta_haber,analytic_account_id,analytic_tag_id,SUM(round(coalesce(amount,0),2)) as credit from kardex_entry_income_book
			where tipo_op = '%s'
			group by tipo_name,almacen,cta_haber,analytic_account_id,analytic_tag_id"""%top['tipo_op'])
			dic_credit = self.env.cr.dictfetchall()
			for elem in dic_credit:
				vals = (0,0,{
					'account_id': elem['cta_haber'],
					'name': elem['tipo_name'],
					'debit': 0,
					'credit': elem['credit'],
					'analytic_account_id': elem['analytic_account_id'],
					'analytic_tag_ids': [(6, 0, [elem['analytic_tag_id']])] if elem['analytic_tag_id'] else None,
					'company_id': self.company_id.id,
				})
				lineas.append(vals)
			
			move_id = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': stock_journal_id.id,
				'date': self.period.date_end,
				'line_ids':lineas,
				'ref': 'INGRESOS-%s'%(self.period.code),
				'glosa': 'POR LOS INGRESOS EN ALMACEN MES DE %s'%(self.period.name),
				'kardex_income_id':register.id,
				'move_type':'entry'})
			
			move_id.action_post()

		return {
			'name': 'Asientos',
			'view_mode': 'tree',
			'view_type': 'form',
			'view_id': self.env.ref('account.view_move_tree').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', register.move_ids.ids)],
		}

	def _get_sql(self,date_ini,date_end,company_id):
		param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not param.type_operation_outproduction:
			raise UserError(u'Falta configurar Parámetro de "Consumo de Producción" en Parametros de Contabilidad de la Compañía.')
		if not param.type_operation_inproduction:
			raise UserError(u'Falta configurar Parámetro de "Ingreso de Producción" en Parametros de Contabilidad de la Compañía.')
		if not param.type_operation_gv:
			raise UserError(u'Falta configurar Parámetro de "Gasto Vinculado" en Parametros de Contabilidad de la Compañía.')

		sql = """SELECT T.* FROM(SELECT 
				GKV.fecha::date,
				GKV.type_doc as tipo,
				GKV.serial as serie,
				GKV.nro as numero,
				GKV.numdoc_cuadre as doc_almacen,
				GKV.doc_partner as ruc,
				GKV.name as empresa,
				ei12.code as tipo_op,
				ei12.name as tipo_name,
				GKV.name_template as producto,
				GKV.default_code,
				GKV.unidad,
				GKV.ingreso as qty,
				round(GKV.debit,6) as amount,
				CASE WHEN vst_valuation.account_id IS NOT NULL THEN vst_valuation.account_id 
				ELSE (SELECT account_id FROM vst_property_stock_valuation_account WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS cta_debe,
				CASE WHEN ei12.category_account = TRUE THEN 
				(CASE WHEN vst_input.account_id IS NOT NULL THEN vst_input.account_id 
				ELSE (SELECT account_id FROM vst_property_stock_account_input WHERE company_id = {company} AND category_id IS NULL LIMIT 1) END)
				ELSE ei12.account_id END as cta_haber,
				GKV.origen,
				GKV.destino,
				GKV.almacen,
				SM.analytic_account_id,
				SM.analytic_tag_id
				FROM get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product),(select array_agg(id) from stock_location),{company}) GKV
				LEFT JOIN stock_move SM on SM.id = GKV.stock_moveid
				LEFT JOIN stock_picking SP on  SP.id = SM.picking_id
				LEFT JOIN stock_location ST ON ST.id = GKV.ubicacion_origen
				LEFT JOIN stock_location ST2 ON ST2.id = GKV.ubicacion_destino
				LEFT JOIN type_operation_kardex ei12 on ei12.code = (case when GKV.operation_type <> '00' then GKV.operation_type else (case when coalesce(GKV.origen,'') = '' then '{gv}'
																											when ST.usage = 'internal' AND ST2.usage = 'production' then '{consumo_produccion}'
																											when ST.usage = 'production' AND ST2.usage = 'internal' then '{ingreso_produccion}' end) end)
				LEFT JOIN product_product PP ON PP.id = GKV.product_id
				LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_valuation_account 
				WHERE company_id = {company}) vst_valuation ON vst_valuation.category_id = PT.categ_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_account_input 
				WHERE company_id = {company}) vst_input ON vst_input.category_id = PT.categ_id
				WHERE (GKV.fecha::date BETWEEN '{date_ini}' AND '{date_end}') and coalesce(GKV.debit,0) > 0)T
	
		""".format(
				date_start_s = str(date_ini.year) + '0101',
				date_end_s = str(date_end).replace('-',''),
				date_ini = date_ini.strftime('%Y/%m/%d'),
				date_end = date_end.strftime('%Y/%m/%d'),
				company = company_id,
				consumo_produccion = param.type_operation_outproduction.code,
				gv = param.type_operation_gv.code,
				ingreso_produccion = param.type_operation_inproduction.code
			)
		return sql