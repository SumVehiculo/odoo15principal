# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class KardexEntryOutcomeWizard(models.TransientModel):
	_inherit = 'kardex.entry.outcome.wizard'


	def get_report(self):		
		self.env.cr.execute("""DELETE FROM kardex_entry_outcome_book""")
		self.env.cr.execute("""
		INSERT INTO kardex_entry_outcome_book (fecha,tipo,serie,numero,doc_almacen,ruc,empresa,tipo_op,tipo_name, producto, default_code, unidad, qty, amount, cta_debe, cta_haber, origen, destino, almacen, analytic_account_id,analytic_tag_id,work_order_id) 
		("""+self._get_sql_report(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
		if self.type_show == 'pantalla':
			return {
				'name': u'Detalle de Salidas',
				'type': 'ir.actions.act_window',
				'res_model': 'kardex.entry.outcome.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}
		if self.type_show == 'excel':
			return self.get_excel()


	def _get_sql_report(self,date_ini,date_end,company_id):
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
				GKV.salida as qty,
				round(GKV.credit,6) as amount,
				CASE WHEN ei12.category_account = TRUE THEN (
				CASE WHEN vst_output.account_id IS NOT NULL THEN vst_output.account_id 
				WHEN vst_output.category_id IS NOT NULL AND vst_output.account_id IS NULL THEN NULL
				ELSE (SELECT account_id FROM vst_property_stock_account_output WHERE company_id = {company} AND category_id IS NULL LIMIT 1) END
				) ELSE ipr.account_id::integer END as cta_debe,
				CASE WHEN vst_valuation.account_id IS NOT NULL THEN vst_valuation.account_id 
				ELSE (SELECT account_id FROM vst_property_stock_valuation_account WHERE company_id = {company} AND category_id IS NULL LIMIT 1)
				END AS cta_haber,
				GKV.origen,
				GKV.destino,
				GKV.almacen,
				SM.analytic_account_id,
				SM.analytic_tag_id,
				SM.work_order_id
				FROM get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product),(select array_agg(id) from stock_location),{company}) GKV
				LEFT JOIN stock_move SM on SM.id = GKV.stock_moveid
				LEFT JOIN stock_picking SP on  SP.id = SM.picking_id
				LEFT JOIN stock_location ST ON ST.id = GKV.ubicacion_origen
				LEFT JOIN stock_location ST2 ON ST2.id = GKV.ubicacion_destino
				LEFT JOIN type_operation_kardex ei12 on ei12.code = (case when GKV.operation_type <> '00' then GKV.operation_type else (case when coalesce(GKV.origen,'') = '' then '{gv}'
																											when ST.usage = 'internal' AND ST2.usage = 'production' then '{consumo_produccion}'
																											when ST.usage = 'production' AND ST2.usage = 'internal' then '{ingreso_produccion}' end) end)
				LEFT JOIN (select split_part(value_reference, ',', 2) as account_id,
				 				  split_part(res_id, ',', 2) as id  
							from ir_property 
							where company_id = {company} 
							and res_id like 'type.operation.kardex,%' and res_id is not null ) ipr ON ipr.id::integer = ei12.id
				LEFT JOIN product_product PP ON PP.id = GKV.product_id
				LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_valuation_account 
				WHERE company_id = {company}) vst_valuation ON vst_valuation.category_id = PT.categ_id
				LEFT JOIN (SELECT category_id,account_id
				FROM vst_property_stock_account_output 
				WHERE company_id = {company}) vst_output ON vst_output.category_id = PT.categ_id
				WHERE (GKV.fecha::date BETWEEN '{date_ini}' AND '{date_end}') and coalesce(GKV.credit,0) > 0)T
	
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