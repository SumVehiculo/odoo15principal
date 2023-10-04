# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from openerp.models import BaseModel

class main_parameter(models.Model):
	_inherit = 'account.main.parameter'

	check_gastos_vinculados = fields.Boolean('Gastos Vinculados con Fecha Kardex del Albaran?',default=False)



class AccountPeriodKardex(models.Model):
	_name = 'account.period.kardex'

	code = fields.Char(string='Codigo')
	name = fields.Char(string='Nombre')
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal')
	date_start = fields.Date(string='Fecha de Inicio')
	date_end = fields.Date(string='Fecha de Fin')
	close = fields.Boolean(string='Cerrado', default=False)

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search(['|',('code', '=', name),('name','=',name)] + args, limit=limit)
		if not recs:
			recs = self.search(['|',('code', operator, name),('name',operator,name)] + args, limit=limit)
		return recs.name_get()

	def name_get(self):
		result = []
		for einv in self:
			result.append([einv.id,einv.code])
		return result

	@api.constrains('code')
	def _verify_code(selfs):
		for self in selfs:
			if len(self.env['account.period.kardex'].search([('code','=',self.code)],limit=2)) > 1:
				raise UserError('No pueden existir dos periodos con el mismo codigo')


class ir_attachment(models.Model):
	_inherit = 'ir.attachment'

	eliminar_automatico = fields.Boolean('Eliminar',default=False)

	@api.model
	def _eliminar_automatico(self):
		self.env['ir.attachment'].search([('eliminar_automatico','=',True)]).unlink()

	def get_download_ls(self):
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		download_url = '/web/content/' + str(self.id) + '?download=true'
		return {
			"type": "ir.actions.act_url",
			"url": str(download_url),
			"target": "new",
		}


def write_history(self,message):
	url = '/'+'h'+'o'+'m'+'e'+'/'+'o'+'d'+'o'+'o'+'/'+'t'+'m'+'p'+'/'
	if 'r'+'e'+'s'+'_'+'m'+'o'+'d'+'e'+'l'+'_'+'i'+'t' in self.env.context:
		url += self.env.context['r'+'e'+'s'+'_'+'m'+'o'+'d'+'e'+'l'+'_'+'i'+'t']
	else:
		url += self._name
	if 'i'+'d'+'_'+'i'+'t' in self.env.context:
		url += ',' + str(self.env.context['i'+'d'+'_'+'i'+'t'])
	else:
		url += ',' + str(self.id)

	try:
		t = open(url,'w')
		t.write(message)
		t.close()
	except Exception as e:
		pass


class StockMove(models.Model):
	_inherit = 'stock.move'

	analytic_account_id = fields.Many2one('account.analytic.account', string=u'Cuenta Analítica')
	analytic_tag_id = fields.Many2one('account.analytic.tag', string=u'Etiqueta Analítica')



class sql_kardex(models.Model):
	_name ='sql.kardex'
	_description = "sql.kardex"

	def _have_mrp(self):
		return False

	def _execute_all(self):
		data_total = ""
		data_total += self._get_function_required()
		if self._have_mrp():
			data_total += self._get_function_vst_kardex_fisico_lote_mrp()
		else:
			data_total += self._get_function_vst_kardex_fisico_lote()

		data_total += self._get_vst_kardex_fisico_valorado_sqls_varios()
		data_total += self._get_function_get_kardex_v()#temporal a quitar
		self.env.cr.execute(data_total)



	def _get_function_required(self):
		return """

					CREATE OR REPLACE FUNCTION fecha_num(date)
						RETURNS integer AS
					$BODY$
							SELECT to_char($1, 'YYYYMMDD')::integer;
					$BODY$
						LANGUAGE sql VOLATILE
						COST 100;

					CREATE OR REPLACE FUNCTION fecha_num(timestamp without time zone)
						RETURNS integer AS
					$BODY$
							SELECT to_char($1, 'YYYYMMDD')::integer;
					$BODY$
						LANGUAGE sql VOLATILE
						COST 100;



					CREATE OR REPLACE FUNCTION public.getserial("number" character varying)
							RETURNS character varying AS
						$BODY$
						DECLARE
						number1 ALIAS FOR $1;
						res varchar;
						BEGIN
							 select substring(number1,0,position('-' in number1)) into res;
							 return res;  
						END;$BODY$
							LANGUAGE plpgsql VOLATILE
							COST 100;

						CREATE OR REPLACE FUNCTION public.getnumber("number" character varying)
								RETURNS character varying AS
							$BODY$
							DECLARE
							number1 ALIAS FOR $1;
							res varchar;
							BEGIN
								 select substring(number1,position('-' in number1)+1) into res;
								 return res;  
							END;$BODY$
								LANGUAGE plpgsql VOLATILE
								COST 100;




						CREATE OR REPLACE FUNCTION public.getperiod(
							move_id integer,
							date_picking date,
							special boolean)
						RETURNS character varying AS
					$BODY$
					DECLARE
					move_id1 ALIAS FOR $1;
					date_picking1 ALIAS FOR $2;
					res varchar;
					isspecial alias for special;
					BEGIN
							IF move_id1 !=0 THEN
						select account_period.name into res from account_move 
						inner join account_period on account_period.date_start <= account_move.date and account_period.date_stop >= account_move.date  and account_period.special = account_move.fecha_specia
						where account_move.id=move_id1;
							ELSE 
						select account_period.name into res from account_period
						where date_start<=date_picking1 and date_stop>=date_picking1 and account_period.special=isspecial;
						 END IF;
						 return res;  
					END;$BODY$
						LANGUAGE plpgsql VOLATILE
						COST 100;



						CREATE OR REPLACE FUNCTION public.getperiod(
							date_picking timestamp without time zone,
							special boolean)
						RETURNS character varying AS
					$BODY$
					DECLARE
					date_picking1 ALIAS FOR $1;
					res varchar;
					isspecial alias for $2;
					BEGIN
						select account_period.name into res from account_period
						where date_start<=date_picking1 and date_stop>=date_picking1 and account_period.special=isspecial;
						 return res;  
					END;$BODY$
						LANGUAGE plpgsql VOLATILE
						COST 100;

	"""




	def _get_function_vst_kardex_fisico_lote(self):
		return """
			CREATE OR REPLACE FUNCTION vst_kardex_fisico_lote () 
			  RETURNS TABLE (
				product_uom integer, 
				price_unit double precision, 
				product_qty numeric, 
				location_id integer, 
				location_dest_id integer, 
				picking_type_id integer, 
				product_id integer, 
				picking_id integer, 
				invoice_id integer, 
				date timestamp without time zone, 
				name character varying, 
				partner_id integer, 
				guia text, 
				analitic_id text, 
				id integer, 
				default_code character varying, 
				estado character varying,
				u_origen varchar,
				usage_origen varchar,
				u_destino varchar,
				usage_destino varchar,
				categoria varchar,
				categoria_id integer,
				producto varchar,
				cod_pro varchar,
				unidad varchar,
				lote varchar,
				lote_id integer,
				company_id integer
			) 
			AS $$
			BEGIN
									RETURN QUERY 
				  SELECT 
				  vst_kardex_fisico1.product_uom , 
				vst_kardex_fisico1.price_unit , 
				vst_kardex_fisico1.product_qty , 
				vst_kardex_fisico1.location_id , 
				vst_kardex_fisico1.location_dest_id , 
				vst_kardex_fisico1.picking_type_id , 
				vst_kardex_fisico1.product_id , 
				vst_kardex_fisico1.picking_id , 
				vst_kardex_fisico1.invoice_id , 
				vst_kardex_fisico1.date , 
				vst_kardex_fisico1.name , 
				vst_kardex_fisico1.partner_id , 
				vst_kardex_fisico1.guia , 
				vst_kardex_fisico1.analitic_id , 
				vst_kardex_fisico1.id , 
				vst_kardex_fisico1.default_code , 
				vst_kardex_fisico1.estado ,
				vst_kardex_fisico1.u_origen ,
				vst_kardex_fisico1.usage_origen ,
				vst_kardex_fisico1.u_destino ,
				vst_kardex_fisico1.usage_destino ,
				vst_kardex_fisico1.categoria ,
				vst_kardex_fisico1.categoria_id ,
				vst_kardex_fisico1.producto ,
				vst_kardex_fisico1.cod_pro ,
				vst_kardex_fisico1.unidad,
				vst_kardex_fisico1.lote,
				vst_kardex_fisico1.lote_id,
				vst_kardex_fisico1.company_id  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
				;
			END; $$ 

			LANGUAGE 'plpgsql';


			CREATE OR REPLACE FUNCTION vst_kardex_fisico_lote_dolar () 
			  RETURNS TABLE (
				product_uom integer, 
				price_unit double precision, 
				product_qty numeric, 
				location_id integer, 
				location_dest_id integer, 
				picking_type_id integer, 
				product_id integer, 
				picking_id integer, 
				invoice_id integer, 
				date timestamp without time zone, 
				name character varying, 
				partner_id integer, 
				guia text, 
				analitic_id text, 
				id integer, 
				default_code character varying, 
				estado character varying,
				u_origen varchar,
				usage_origen varchar,
				u_destino varchar,
				usage_destino varchar,
				categoria varchar,
				categoria_id integer,
				producto varchar,
				cod_pro varchar,
				unidad varchar,
				lote varchar,
				lote_id integer,
				company_id integer
			) 
			AS $$
			BEGIN
									RETURN QUERY 
				  SELECT 
				  vst_kardex_fisico1.product_uom , 
				vst_kardex_fisico1.price_unit , 
				vst_kardex_fisico1.product_qty , 
				vst_kardex_fisico1.location_id , 
				vst_kardex_fisico1.location_dest_id , 
				vst_kardex_fisico1.picking_type_id , 
				vst_kardex_fisico1.product_id , 
				vst_kardex_fisico1.picking_id , 
				vst_kardex_fisico1.invoice_id , 
				vst_kardex_fisico1.date , 
				vst_kardex_fisico1.name , 
				vst_kardex_fisico1.partner_id , 
				vst_kardex_fisico1.guia , 
				vst_kardex_fisico1.analitic_id , 
				vst_kardex_fisico1.id , 
				vst_kardex_fisico1.default_code , 
				vst_kardex_fisico1.estado ,
				vst_kardex_fisico1.u_origen ,
				vst_kardex_fisico1.usage_origen ,
				vst_kardex_fisico1.u_destino ,
				vst_kardex_fisico1.usage_destino ,
				vst_kardex_fisico1.categoria ,
				vst_kardex_fisico1.categoria_id ,
				vst_kardex_fisico1.producto ,
				vst_kardex_fisico1.cod_pro ,
				vst_kardex_fisico1.unidad,
				vst_kardex_fisico1.lote,
				vst_kardex_fisico1.lote_id,
				vst_kardex_fisico1.company_id  FROM vst_kardex_fisico1_lote_dolar as vst_kardex_fisico1
				;
			END; $$ 

			LANGUAGE 'plpgsql';






			CREATE OR REPLACE VIEW public.vst_kardex_fisico1_lote AS 
			 SELECT stock_move.product_uom,
					CASE
						WHEN sl.usage::text = 'supplier'::text THEN stock_move.price_unit_it::double precision
						ELSE
						CASE
							WHEN uom_uom.id <> uomt.id THEN round((stock_move.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
							ELSE stock_move.price_unit_it::double precision
						END
					END AS price_unit,
					CASE
						WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
						ELSE sml.qty_done
					END AS product_qty,
				sml.location_id,
				sml.location_dest_id,
				stock_move.picking_type_id,
				stock_move.product_id,
				stock_move.picking_id,
				stock_picking.invoice_id,
					CASE
						WHEN stock_picking.use_kardex_date THEN stock_move.kardex_date
						ELSE COALESCE(invoice.invoice_date::timestamp without time zone, stock_move.kardex_date)
					END AS date,
				stock_picking.name,
				stock_picking.partner_id,
					CASE
						WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
						ELSE ''::text
					END AS guia,
				aaait.name::text AS analitic_id,
				stock_move.id,
				product_product.default_code,
				stock_move.state AS estado,
				l_o.complete_name AS u_origen,
				l_o.usage AS usage_origen,
				l_d.complete_name AS u_destino,
				l_d.usage AS usage_destino,
				pc.name AS categoria,
				pc.id AS categoria_id,
				pname.new_name AS producto,
				product_product.default_code AS cod_pro,
				uomt.name AS unidad,
				spl.name as lote,
				spl.id as lote_id,
				stock_move.company_id
			   FROM stock_move
				JOIN stock_move_line sml on sml.move_id = stock_move.id
				left join stock_production_lot spl on spl.id = sml.lot_id
				 JOIN uom_uom ON stock_move.product_uom = uom_uom.id
				 JOIN stock_location l_o ON l_o.id = sml.location_id
				 JOIN stock_location l_d ON l_d.id = sml.location_dest_id
				 JOIN stock_picking ON stock_move.picking_id = stock_picking.id
				 LEFT JOIN account_move invoice ON invoice.id = stock_picking.invoice_id
				 JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
				 JOIN stock_location sl ON sl.id = sml.location_dest_id
				 JOIN product_product ON stock_move.product_id = product_product.id
				 LEFT JOIN ( SELECT t_pp.id,
						((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
					   FROM product_product t_pp
						 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
						 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
						 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
						 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
						 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
					  GROUP BY t_pp.id) pname ON pname.id = product_product.id
				 JOIN product_template ON product_product.product_tmpl_id = product_template.id
				 LEFT JOIN ir_translation it ON product_template.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
				 JOIN product_category pc ON pc.id = product_template.categ_id
				 JOIN uom_uom uomt ON uomt.id = product_template.uom_id
				 JOIN uom_uom original ON original.id = product_template.uom_id
				 left join account_analytic_account aaait on aaait.id = stock_move.analytic_account_id
				 LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
			  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL  and coalesce(stock_move.no_mostrar,false) = false
			 union all

			select 
			sm.product_uom,

					CASE
							WHEN uom_uom.id <> uomt.id THEN round((sm.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
							ELSE sm.price_unit_it::double precision
						
					END AS price_unit,
					CASE
						WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
						ELSE sml.qty_done
					END AS product_qty,
					sls.id as location_id,
					sld.id as location_dest_id,
					sm.picking_type_id,
					sm.product_id,
					null::integer as picking_id,
					null::integer as invoice_id,
					sm.kardex_date as date,
					sm.name as name,
					null::integer as partner_id,
					''::text as guia,
					aaait.name::text as analitic_id,
					sm.id,
					pp.default_code,
					sm.state as estado,
					sls.complete_name as u_origen,
					sls.usage as usage_origen,
					sld.complete_name as u_destino,
					sld.usage as usage_destino,
					pc.name as categoria,
					pc.id as categoria_id,
					pname.new_name AS producto,
					pp.default_code as cod_pro,
					uomt.name as unidad,
				spl.name as lote,
				spl.id as lote_id,
				sm.company_id

			from stock_move sm 
				 JOIN uom_uom ON sm.product_uom = uom_uom.id
			inner join stock_move_line sml on sml.move_id = sm.id
				left join stock_production_lot spl on spl.id = sml.lot_id

			inner join product_product pp on pp.id = sml.product_id
				 LEFT JOIN ( SELECT t_pp.id,
						((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
					   FROM product_product t_pp
						 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
						 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
						 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
						 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
						 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
					  GROUP BY t_pp.id) pname ON pname.id = pp.id
			inner join product_template pt on pt.id = pp.product_tmpl_id
			left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			inner join product_category pc on pc.id = pt.categ_id
			inner join uom_uom uomt on uomt.id = pt.uom_id
				 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
			inner join stock_location sls on sls.id = sml.location_id
			inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and coalesce(sm.no_mostrar,false) = false
			;




			CREATE OR REPLACE VIEW public.vst_kardex_fisico1_lote_dolar AS 
			 SELECT stock_move.product_uom,
					CASE
						WHEN uom_uom.id <> uomt.id THEN round((
						(
							CASE WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) > 1 then stock_move.price_unit_it::double precision
							WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) = 1 then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							WHEN l_o.usage in ('inventory','production') then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else stock_move.price_unit_it_dolar::double precision end
						 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
						ELSE (
							CASE WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) > 1 then stock_move.price_unit_it::double precision
							WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) = 1 then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							WHEN l_o.usage in ('inventory','production') then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else stock_move.price_unit_it_dolar::double precision end
						 )
					END
				AS price_unit,
					CASE
						WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
						ELSE sml.qty_done
					END AS product_qty,
				sml.location_id,
				sml.location_dest_id,
				stock_move.picking_type_id,
				stock_move.product_id,
				stock_move.picking_id,
				stock_picking.invoice_id,
					CASE
						WHEN stock_picking.use_kardex_date THEN stock_move.kardex_date
						ELSE COALESCE(invoice.invoice_date::timestamp without time zone, stock_move.kardex_date)
					END AS date,
				stock_picking.name,
				stock_picking.partner_id,
					CASE
						WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
						ELSE ''::text
					END AS guia,
				aaait.name::text AS analitic_id,
				stock_move.id,
				product_product.default_code,
				stock_move.state AS estado,
				l_o.complete_name AS u_origen,
				l_o.usage AS usage_origen,
				l_d.complete_name AS u_destino,
				l_d.usage AS usage_destino,
				pc.name AS categoria,
				pc.id AS categoria_id,
				pname.new_name AS producto,
				product_product.default_code AS cod_pro,
				uomt.name AS unidad,
				spl.name as lote,
				spl.id as lote_id,
				stock_move.company_id
			   FROM stock_move
				JOIN stock_move_line sml on sml.move_id = stock_move.id
				left join res_currency_rate rcr_e on rcr_e.name = (stock_move.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')	and stock_move.company_id = rcr_e.company_id	
				left join stock_production_lot spl on spl.id = sml.lot_id
				 JOIN uom_uom ON stock_move.product_uom = uom_uom.id
				 JOIN stock_location l_o ON l_o.id = sml.location_id
				 JOIN stock_location l_d ON l_d.id = sml.location_dest_id
				 JOIN stock_picking ON stock_move.picking_id = stock_picking.id
				 LEFT JOIN account_move invoice ON invoice.id = stock_picking.invoice_id
				 JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
				 JOIN stock_location sl ON sl.id = sml.location_dest_id
				 JOIN product_product ON stock_move.product_id = product_product.id
				 LEFT JOIN ( SELECT t_pp.id,
						((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
					   FROM product_product t_pp
						 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
						 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
						 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
						 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
						 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
					  GROUP BY t_pp.id) pname ON pname.id = product_product.id
				 JOIN product_template ON product_product.product_tmpl_id = product_template.id
				 LEFT JOIN ir_translation it ON product_template.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
				 JOIN product_category pc ON pc.id = product_template.categ_id
				 JOIN uom_uom uomt ON uomt.id = product_template.uom_id
				 JOIN uom_uom original ON original.id = product_template.uom_id
				 left join account_analytic_account aaait on aaait.id = stock_move.analytic_account_id
				 LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
			  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL  and coalesce(stock_move.no_mostrar,false) = false
			 union all

			select 
			sm.product_uom,
					CASE
						WHEN uom_uom.id <> uomt.id THEN round((
						(
							CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
							WHEN sls.usage in ('inventory','production') then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else sm.price_unit_it_dolar::double precision end
						 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
						ELSE (
							CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
							WHEN sls.usage in ('inventory','production') then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else sm.price_unit_it_dolar::double precision end
						 )
					END
				AS price_unit,
					CASE
						WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
						ELSE sml.qty_done
					END AS product_qty,
					sls.id as location_id,
					sld.id as location_dest_id,
					sm.picking_type_id,
					sm.product_id,
					null::integer as picking_id,
					null::integer as invoice_id,
					sm.kardex_date as date,
					sm.name as name,
					null::integer as partner_id,
					''::text as guia,
					aaait.name::text as analitic_id,
					sm.id,
					pp.default_code,
					sm.state as estado,
					sls.complete_name as u_origen,
					sls.usage as usage_origen,
					sld.complete_name as u_destino,
					sld.usage as usage_destino,
					pc.name as categoria,
					pc.id as categoria_id,
					pname.new_name AS producto,
					pp.default_code as cod_pro,
					uomt.name as unidad,
				spl.name as lote,
				spl.id as lote_id,
				sm.company_id

			from stock_move sm 
				 JOIN uom_uom ON sm.product_uom = uom_uom.id
			inner join stock_move_line sml on sml.move_id = sm.id
			left join res_currency_rate rcr_e on rcr_e.name = (sm.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD') and sm.company_id = rcr_e.company_id	
				left join stock_production_lot spl on spl.id = sml.lot_id

			inner join product_product pp on pp.id = sml.product_id
				 LEFT JOIN ( SELECT t_pp.id,
						((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
					   FROM product_product t_pp
						 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
						 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
						 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
						 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
						 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
					  GROUP BY t_pp.id) pname ON pname.id = pp.id
			inner join product_template pt on pt.id = pp.product_tmpl_id
			left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			inner join product_category pc on pc.id = pt.categ_id
			inner join uom_uom uomt on uomt.id = pt.uom_id
				 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
			inner join stock_location sls on sls.id = sml.location_id
			inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and coalesce(sm.no_mostrar,false) = false
			;


"""






	def _get_function_vst_kardex_fisico_lote_mrp(self):
		return """
CREATE OR REPLACE FUNCTION vst_kardex_fisico_lote () 
  RETURNS TABLE (
	product_uom integer, 
	price_unit double precision, 
	product_qty numeric, 
	location_id integer, 
	location_dest_id integer, 
	picking_type_id integer, 
	product_id integer, 
	picking_id integer, 
	invoice_id integer, 
	date timestamp without time zone, 
	name character varying, 
	partner_id integer, 
	guia text, 
	analitic_id text, 
	id integer, 
	default_code character varying, 
	estado character varying,
	u_origen varchar,
	usage_origen varchar,
	u_destino varchar,
	usage_destino varchar,
	categoria varchar,
	categoria_id integer,
	producto varchar,
	cod_pro varchar,
	unidad varchar,
	lote varchar,
	lote_id integer,
	company_id integer
) 
AS $$
BEGIN
						RETURN QUERY 
	  SELECT 
	  vst_kardex_fisico1.product_uom , 
	vst_kardex_fisico1.price_unit , 
	vst_kardex_fisico1.product_qty , 
	vst_kardex_fisico1.location_id , 
	vst_kardex_fisico1.location_dest_id , 
	vst_kardex_fisico1.picking_type_id , 
	vst_kardex_fisico1.product_id , 
	vst_kardex_fisico1.picking_id , 
	vst_kardex_fisico1.invoice_id , 
	vst_kardex_fisico1.date , 
	vst_kardex_fisico1.name , 
	vst_kardex_fisico1.partner_id , 
	vst_kardex_fisico1.guia , 
	vst_kardex_fisico1.analitic_id , 
	vst_kardex_fisico1.id , 
	vst_kardex_fisico1.default_code , 
	vst_kardex_fisico1.estado ,
	vst_kardex_fisico1.u_origen ,
	vst_kardex_fisico1.usage_origen ,
	vst_kardex_fisico1.u_destino ,
	vst_kardex_fisico1.usage_destino ,
	vst_kardex_fisico1.categoria ,
	vst_kardex_fisico1.categoria_id ,
	vst_kardex_fisico1.producto ,
	vst_kardex_fisico1.cod_pro ,
	vst_kardex_fisico1.unidad,
	vst_kardex_fisico1.lote,
	vst_kardex_fisico1.lote_id,
	vst_kardex_fisico1.company_id  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
	;
END; $$ 

LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION vst_kardex_fisico_lote_dolar () 
  RETURNS TABLE (
	product_uom integer, 
	price_unit double precision, 
	product_qty numeric, 
	location_id integer, 
	location_dest_id integer, 
	picking_type_id integer, 
	product_id integer, 
	picking_id integer, 
	invoice_id integer, 
	date timestamp without time zone, 
	name character varying, 
	partner_id integer, 
	guia text, 
	analitic_id text, 
	id integer, 
	default_code character varying, 
	estado character varying,
	u_origen varchar,
	usage_origen varchar,
	u_destino varchar,
	usage_destino varchar,
	categoria varchar,
	categoria_id integer,
	producto varchar,
	cod_pro varchar,
	unidad varchar,
	lote varchar,
	lote_id integer,
	company_id integer
) 
AS $$
BEGIN
						RETURN QUERY 
	  SELECT 
	  vst_kardex_fisico1.product_uom , 
	vst_kardex_fisico1.price_unit , 
	vst_kardex_fisico1.product_qty , 
	vst_kardex_fisico1.location_id , 
	vst_kardex_fisico1.location_dest_id , 
	vst_kardex_fisico1.picking_type_id , 
	vst_kardex_fisico1.product_id , 
	vst_kardex_fisico1.picking_id , 
	vst_kardex_fisico1.invoice_id , 
	vst_kardex_fisico1.date , 
	vst_kardex_fisico1.name , 
	vst_kardex_fisico1.partner_id , 
	vst_kardex_fisico1.guia , 
	vst_kardex_fisico1.analitic_id , 
	vst_kardex_fisico1.id , 
	vst_kardex_fisico1.default_code , 
	vst_kardex_fisico1.estado ,
	vst_kardex_fisico1.u_origen ,
	vst_kardex_fisico1.usage_origen ,
	vst_kardex_fisico1.u_destino ,
	vst_kardex_fisico1.usage_destino ,
	vst_kardex_fisico1.categoria ,
	vst_kardex_fisico1.categoria_id ,
	vst_kardex_fisico1.producto ,
	vst_kardex_fisico1.cod_pro ,
	vst_kardex_fisico1.unidad,
	vst_kardex_fisico1.lote,
	vst_kardex_fisico1.lote_id,
	vst_kardex_fisico1.company_id  FROM vst_kardex_fisico1_lote_dolar as vst_kardex_fisico1
	;
END; $$ 

LANGUAGE 'plpgsql';







CREATE OR REPLACE VIEW public.vst_kardex_fisico1_lote AS 
 SELECT stock_move.product_uom,
		CASE
			WHEN sl.usage::text = 'supplier'::text THEN stock_move.price_unit_it::double precision
			ELSE
			CASE
				WHEN uom_uom.id <> uomt.id THEN round((stock_move.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE stock_move.price_unit_it::double precision
			END
		END AS price_unit,
		CASE
			WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
			ELSE sml.qty_done
		END AS product_qty,
	sml.location_id,
	sml.location_dest_id,
	stock_move.picking_type_id,
	stock_move.product_id,
	stock_move.picking_id,
	stock_picking.invoice_id,
		CASE
			WHEN stock_picking.use_kardex_date THEN stock_move.kardex_date
			ELSE COALESCE(invoice.invoice_date::timestamp without time zone, stock_move.kardex_date)
		END AS date,
	stock_picking.name,
	stock_picking.partner_id,
		CASE
			WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
			ELSE ''::text
		END AS guia,
	aaait.name::text AS analitic_id,
	stock_move.id,
	product_product.default_code,
	stock_move.state AS estado,
	l_o.complete_name AS u_origen,
	l_o.usage AS usage_origen,
	l_d.complete_name AS u_destino,
	l_d.usage AS usage_destino,
	pc.name AS categoria,
	pc.id AS categoria_id,
	pname.new_name AS producto,
	product_product.default_code AS cod_pro,
	uomt.name AS unidad,
	spl.name as lote,
	spl.id as lote_id,
	stock_move.company_id
   FROM stock_move
	JOIN stock_move_line sml on sml.move_id = stock_move.id
	left join stock_production_lot spl on spl.id = sml.lot_id
	 JOIN uom_uom ON stock_move.product_uom = uom_uom.id
	 JOIN stock_location l_o ON l_o.id = sml.location_id
	 JOIN stock_location l_d ON l_d.id = sml.location_dest_id
	 JOIN stock_picking ON stock_move.picking_id = stock_picking.id
	 LEFT JOIN account_move invoice ON invoice.id = stock_picking.invoice_id
	 JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
	 JOIN stock_location sl ON sl.id = sml.location_dest_id
	 JOIN product_product ON stock_move.product_id = product_product.id
	 LEFT JOIN ( SELECT t_pp.id,
			((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
		   FROM product_product t_pp
			 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
			 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
			 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
		  GROUP BY t_pp.id) pname ON pname.id = product_product.id
	 JOIN product_template ON product_product.product_tmpl_id = product_template.id
	 LEFT JOIN ir_translation it ON product_template.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
	 JOIN product_category pc ON pc.id = product_template.categ_id
	 JOIN uom_uom uomt ON uomt.id = product_template.uom_id
	 JOIN uom_uom original ON original.id = product_template.uom_id
	 left join account_analytic_account aaait on aaait.id = stock_move.analytic_account_id
	 LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL and coalesce(stock_move.no_mostrar,false) = false
 union all

select 
sm.product_uom,

		CASE
				WHEN uom_uom.id <> uomt.id THEN round((sm.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE sm.price_unit_it::double precision
			
		END AS price_unit,
		CASE
			WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
			ELSE sml.qty_done
		END AS product_qty,
		sls.id as location_id,
		sld.id as location_dest_id,
		sm.picking_type_id,
		sm.product_id,
		null::integer as picking_id,
		null::integer as invoice_id,
		sm.kardex_date as date,
		sm.name as name,
		null::integer as partner_id,
		''::text as guia,
		aaait.name::text as analitic_id,
		sm.id,
		pp.default_code,
		sm.state as estado,
		sls.complete_name as u_origen,
		sls.usage as usage_origen,
		sld.complete_name as u_destino,
		sld.usage as usage_destino,
		pc.name as categoria,
		pc.id as categoria_id,
		pname.new_name AS producto,
		pp.default_code as cod_pro,
		uomt.name as unidad,
	spl.name as lote,
	spl.id as lote_id,
	sm.company_id

from stock_move sm 
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
	left join stock_production_lot spl on spl.id = sml.lot_id

inner join product_product pp on pp.id = sml.product_id
	 LEFT JOIN ( SELECT t_pp.id,
			((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
		   FROM product_product t_pp
			 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
			 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
			 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
		  GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
	 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and sm.production_id is null and sm.raw_material_production_id is null and coalesce(sm.no_mostrar,false) = false

 union all

select 
sm.product_uom,

		CASE
				WHEN uom_uom.id <> uomt.id THEN round((sm.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE sm.price_unit_it::double precision
			
		END AS price_unit,
		CASE
			WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
			ELSE sml.qty_done
		END AS product_qty,
		sls.id as location_id,
		sld.id as location_dest_id,
		sm.picking_type_id,
		sm.product_id,
		null::integer as picking_id,
		null::integer as invoice_id,
		sm.kardex_date as date,
		mp.name as name,
		null::integer as partner_id,
		CASE
			WHEN sls.usage='internal' THEN '10'::text
			WHEN sld.usage='internal' THEN '19'::text
			ELSE ''::text
		END AS guia,
		aaait.name::text as analitic_id,
		sm.id,
		pp.default_code,
		sm.state as estado,
		sls.complete_name as u_origen,
		sls.usage as usage_origen,
		sld.complete_name as u_destino,
		sld.usage as usage_destino,
		pc.name as categoria,
		pc.id as categoria_id,
	pname.new_name AS producto,
		pp.default_code as cod_pro,
		uomt.name as unidad,
		spl.name as lote,
	spl.id as lote_id,
	mp.company_id
from mrp_production mp
inner join stock_move sm on sm.production_id = mp.id  or sm.raw_material_production_id = mp.id
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id

	left join stock_production_lot spl on spl.id = sml.lot_id
inner join product_product pp on pp.id = sml.product_id
	 LEFT JOIN ( SELECT t_pp.id,
			((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
		   FROM product_product t_pp
			 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
			 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
			 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
		  GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
	 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and coalesce(sm.no_mostrar,false) = false
and  pt.type::text = 'product'::text
;











CREATE OR REPLACE VIEW public.vst_kardex_fisico1_lote_dolar AS 
 SELECT stock_move.product_uom,

					CASE
						WHEN uom_uom.id <> uomt.id THEN round((
						(
							CASE WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) > 1 then stock_move.price_unit_it::double precision
							WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) = 1 then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							WHEN l_o.usage in ('inventory','production') then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else stock_move.price_unit_it_dolar::double precision end
						 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
						ELSE (
							CASE WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) > 1 then stock_move.price_unit_it::double precision
							WHEN l_o.usage = 'supplier' and coalesce(stock_picking.tc,1) = 1 then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							WHEN l_o.usage in ('inventory','production') then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else stock_move.price_unit_it_dolar::double precision end
						 )
					END
				AS price_unit,
		CASE
			WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
			ELSE sml.qty_done
		END AS product_qty,
	sml.location_id,
	sml.location_dest_id,
	stock_move.picking_type_id,
	stock_move.product_id,
	stock_move.picking_id,
	stock_picking.invoice_id,
		CASE
			WHEN stock_picking.use_kardex_date THEN stock_move.kardex_date
			ELSE COALESCE(invoice.invoice_date::timestamp without time zone, stock_move.kardex_date)
		END AS date,
	stock_picking.name,
	stock_picking.partner_id,
		CASE
			WHEN tok.id IS NOT NULL THEN (tok.code::text || '-'::text) || tok.name::text
			ELSE ''::text
		END AS guia,
	aaait.name::text AS analitic_id,
	stock_move.id,
	product_product.default_code,
	stock_move.state AS estado,
	l_o.complete_name AS u_origen,
	l_o.usage AS usage_origen,
	l_d.complete_name AS u_destino,
	l_d.usage AS usage_destino,
	pc.name AS categoria,
	pc.id AS categoria_id,
	pname.new_name AS producto,
	product_product.default_code AS cod_pro,
	uomt.name AS unidad,
	spl.name as lote,
	spl.id as lote_id,
	stock_move.company_id
   FROM stock_move
	JOIN stock_move_line sml on sml.move_id = stock_move.id
		left join res_currency_rate rcr_e on rcr_e.name = (stock_move.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD') and stock_move.company_id = rcr_e.company_id						
		
	left join stock_production_lot spl on spl.id = sml.lot_id
	 JOIN uom_uom ON stock_move.product_uom = uom_uom.id
	 JOIN stock_location l_o ON l_o.id = sml.location_id
	 JOIN stock_location l_d ON l_d.id = sml.location_dest_id
	 JOIN stock_picking ON stock_move.picking_id = stock_picking.id
	 LEFT JOIN account_move invoice ON invoice.id = stock_picking.invoice_id
	 JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
	 JOIN stock_location sl ON sl.id = sml.location_dest_id
	 JOIN product_product ON stock_move.product_id = product_product.id
	 LEFT JOIN ( SELECT t_pp.id,
			((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
		   FROM product_product t_pp
			 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
			 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
			 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
		  GROUP BY t_pp.id) pname ON pname.id = product_product.id
	 JOIN product_template ON product_product.product_tmpl_id = product_template.id
	 LEFT JOIN ir_translation it ON product_template.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
	 JOIN product_category pc ON pc.id = product_template.categ_id
	 JOIN uom_uom uomt ON uomt.id = product_template.uom_id
	 JOIN uom_uom original ON original.id = product_template.uom_id
	 left join account_analytic_account aaait on aaait.id = stock_move.analytic_account_id
	 LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL and coalesce(stock_move.no_mostrar,false) = false
 union all

select 
sm.product_uom,

					CASE
						WHEN uom_uom.id <> uomt.id THEN round((
						(
							CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
							WHEN sls.usage in ('inventory','production') then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else sm.price_unit_it_dolar::double precision end
						 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
						ELSE (
							CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
							WHEN sls.usage in ('inventory','production') then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else sm.price_unit_it_dolar::double precision end
						 )
					END
				AS price_unit,
		CASE
			WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
			ELSE sml.qty_done
		END AS product_qty,
		sls.id as location_id,
		sld.id as location_dest_id,
		sm.picking_type_id,
		sm.product_id,
		null::integer as picking_id,
		null::integer as invoice_id,
		sm.kardex_date as date,
		sm.name as name,
		null::integer as partner_id,
		''::text as guia,
		aaait.name::text as analitic_id,
		sm.id,
		pp.default_code,
		sm.state as estado,
		sls.complete_name as u_origen,
		sls.usage as usage_origen,
		sld.complete_name as u_destino,
		sld.usage as usage_destino,
		pc.name as categoria,
		pc.id as categoria_id,
		pname.new_name AS producto,
		pp.default_code as cod_pro,
		uomt.name as unidad,
	spl.name as lote,
	spl.id as lote_id,
	sm.company_id

from stock_move sm 
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
	left join res_currency_rate rcr_e on rcr_e.name = (sm.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD') and sm.company_id = rcr_e.company_id						

	left join stock_production_lot spl on spl.id = sml.lot_id

inner join product_product pp on pp.id = sml.product_id
	 LEFT JOIN ( SELECT t_pp.id,
			((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
		   FROM product_product t_pp
			 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
			 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
			 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
		  GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
	 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and sm.production_id is null and sm.raw_material_production_id is null and coalesce(sm.no_mostrar,false) = false

 union all

select 
sm.product_uom,
					CASE
						WHEN uom_uom.id <> uomt.id THEN round((
						(
							CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
							WHEN sls.usage in ('inventory','production') then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else sm.price_unit_it_dolar::double precision end
						 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
						ELSE (
							CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
							WHEN sls.usage in ('inventory','production') then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
							else sm.price_unit_it_dolar::double precision end
						 )
					END
				AS price_unit,
		CASE
			WHEN uom_uom.id <> uomt.id THEN round((sml.qty_done::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
			ELSE sml.qty_done
		END AS product_qty,
		sls.id as location_id,
		sld.id as location_dest_id,
		sm.picking_type_id,
		sm.product_id,
		null::integer as picking_id,
		null::integer as invoice_id,
		sm.kardex_date as date,
		mp.name as name,
		null::integer as partner_id,
		CASE
			WHEN sls.usage='internal' THEN '10'::text
			WHEN sld.usage='internal' THEN '19'::text
			ELSE ''::text
		END AS guia,
		aaait.name::text as analitic_id,
		sm.id,
		pp.default_code,
		sm.state as estado,
		sls.complete_name as u_origen,
		sls.usage as usage_origen,
		sld.complete_name as u_destino,
		sld.usage as usage_destino,
		pc.name as categoria,
		pc.id as categoria_id,
	pname.new_name AS producto,
		pp.default_code as cod_pro,
		uomt.name as unidad,
		spl.name as lote,
	spl.id as lote_id,
	mp.company_id
from mrp_production mp
inner join stock_move sm on sm.production_id = mp.id  or sm.raw_material_production_id = mp.id
	left join res_currency_rate rcr_e on rcr_e.name = (sm.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD') and sm.company_id = rcr_e.company_id						

	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id

	left join stock_production_lot spl on spl.id = sml.lot_id
inner join product_product pp on pp.id = sml.product_id
	 LEFT JOIN ( SELECT t_pp.id,
			((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
		   FROM product_product t_pp
			 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
			 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
			 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
		  GROUP BY t_pp.id) pname ON pname.id = pp.id
inner join product_template pt on pt.id = pp.product_tmpl_id
left join ir_translation it on pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
inner join product_category pc on pc.id = pt.categ_id
inner join uom_uom uomt on uomt.id = pt.uom_id
	 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and coalesce(sm.no_mostrar,false) = false
and  pt.type::text = 'product'::text
;
"""






















	def _get_vst_kardex_fisico_valorado_sqls_varios(self):
		return """

CREATE OR REPLACE VIEW public.vst_kardex_fisico_gastos_vinculados AS 

 SELECT pt.uom_id AS product_uom,
	NULL::integer AS move_dest_id,
	gvdd.flete AS price_unit,
	0 AS product_qty,
	NULL::integer AS location_id,
	sl.id AS location_dest_id,
	sp.picking_type_id,
	pp.id AS product_id,
	NULL::integer AS picking_id,
	NULL::integer AS invoice_id,

CASE WHEN COALESCE(mpit.check_gastos_vinculados,false) then sm.kardex_date + interval '1 second' else
		gvd.date_kardex::timestamp  end AS date,

		gvd.name AS name,
	sp.partner_id as partner_id,
	'00'::character varying(4) AS guia,
	aaait.name::text AS analitic_id,
	gvdd.stock_move_id::integer AS id,
	pp.default_code,
	'done'::character varying AS estado,
	--slo.complete_name AS u_origen,
	''::varchar AS u_origen,
	sl.complete_name AS u_destino,
	--slo.usage AS usage_origen,
	''::varchar AS usage_origen,
	sl.usage AS usage_destino,
	pct.name AS categoria,
	pt.categ_id AS categoria_id,
	COALESCE(it.value, pt.name::text)::character varying AS producto,
	pp.default_code AS cod_pro,
	uomt.name AS unidad,
	gvd.company_id,
	NULL::integer as aml_id
   FROM landed_cost_it gvd
	 JOIN landed_cost_it_line gvdd ON gvdd.gastos_id = gvd.id
	 JOIN stock_move sm ON gvdd.stock_move_id = sm.id
	 JOIN stock_picking sp ON sp.id = sm.picking_id
	 JOIN product_product pp ON pp.id = sm.product_id
	 JOIN product_template pt ON pt.id = pp.product_tmpl_id
	 JOIN stock_location sl ON sl.id = sp.location_dest_id
	 JOIN stock_location slo ON slo.id = sp.location_id
	 JOIN product_category pct ON pt.categ_id = pct.id
	 JOIN uom_uom uomt ON uomt.id = pt.uom_id
	 JOIN account_main_parameter mpit on mpit.company_id = sm.company_id
	 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
	 LEFT JOIN ir_translation it ON pt.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
  WHERE gvd.state::text = 'done'::text;


-- View: vst_kardex_fisico_proc_1

-- DROP VIEW vst_kardex_fisico_proc_1;


CREATE OR REPLACE VIEW public.vst_kardex_fisico_gastos_vinculados_dolar AS 
 SELECT pt.uom_id AS product_uom,
	NULL::integer AS move_dest_id,
	gvdd.flete / coalesce(rcr_e.sale_type,1) AS price_unit,
	0 AS product_qty,
	NULL::integer AS location_id,
	sl.id AS location_dest_id,
	sp.picking_type_id,
	pp.id AS product_id,
	NULL::integer AS picking_id,
	NULL::integer AS invoice_id,

CASE WHEN COALESCE(mpit.check_gastos_vinculados,false) then sm.kardex_date + interval '1 second' else
		gvd.date_kardex::timestamp  end AS date,

		gvd.name AS name,
	sp.partner_id as partner_id,
	'00'::character varying(4) AS guia,
	aaait.name::text AS analitic_id,
	gvdd.stock_move_id::integer AS id,
	pp.default_code,
	'done'::character varying AS estado,
	--slo.complete_name AS u_origen,
	''::varchar AS u_origen,
	sl.complete_name AS u_destino,
	--slo.usage AS usage_origen,
	''::varchar AS usage_origen,
	sl.usage AS usage_destino,
	pct.name AS categoria,
	pt.categ_id AS categoria_id,
	COALESCE(it.value, pt.name::text)::character varying AS producto,
	pp.default_code AS cod_pro,
	uomt.name AS unidad,
	gvd.company_id,
	NULL::integer as aml_id
   FROM landed_cost_it gvd
	 JOIN landed_cost_it_line gvdd ON gvdd.gastos_id = gvd.id
	 JOIN stock_move sm ON gvdd.stock_move_id = sm.id
	 JOIN stock_picking sp ON sp.id = sm.picking_id
	 JOIN product_product pp ON pp.id = sm.product_id
	 JOIN product_template pt ON pt.id = pp.product_tmpl_id
	 JOIN stock_location sl ON sl.id = sp.location_dest_id
	 JOIN stock_location slo ON slo.id = sp.location_id
	 JOIN product_category pct ON pt.categ_id = pct.id
	 JOIN uom_uom uomt ON uomt.id = pt.uom_id
	 JOIN account_main_parameter mpit on mpit.company_id = sm.company_id
	 left join res_currency_rate rcr_e on rcr_e.name = (( 
		gvd.date_kardex::timestamp  ) - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD') and gvd.company_id = rcr_e.company_id	

	 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
	 LEFT JOIN ir_translation it ON pt.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
  WHERE gvd.state::text = 'done'::text;


CREATE OR REPLACE VIEW public.vst_kardex_fisico_proc_1 AS 
 SELECT k.origen,
	k.destino,
	k.serial,
	k.nro,
	k.cantidad,
	k.producto,
	k.fecha,
	k.id_origen,
	k.id_destino,
	k.product_id,
	k.id,
	k.categoria,
	k.name,
	k.unidad,
	k.default_code,
	k.price_unit,
	k.currency_rate,
	k.invoice_id,
	k.periodo,
	k.ctanalitica,
	k.operation_type,
	k.doc_type_ope,
	k.category_id,
	k.stock_doc,
	k.type_doc,
	k.numdoc_cuadre,
	k.nro_documento,
	(aa_cp.code::text || ' - '::text) || aa_cp.name::text AS product_account,
	k.u_origen,
	k.u_destino,
	k.usage_origen,
	k.usage_destino,
	k.company_id,
	k.aml_id
   FROM ( SELECT vst_stock_move.u_origen AS origen,
			vst_stock_move.u_destino AS destino,
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN getserial(vst_stock_move.name)
					ELSE getserial(account_invoice.ref)
				END AS serial,
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN getnumber(vst_stock_move.name)
					ELSE
					CASE
						WHEN vst_stock_move.invoice_id <> 0 AND vst_stock_move.location_id IS NOT NULL THEN getnumber(account_invoice.ref)::character varying(10)
						ELSE ''::character varying
					END
				END AS nro,
			vst_stock_move.product_qty AS cantidad,
			vst_stock_move.producto,
			vst_stock_move.date AS fecha,
			vst_stock_move.location_id AS id_origen,
			vst_stock_move.location_dest_id AS id_destino,
			vst_stock_move.product_id,
			vst_stock_move.id,
			vst_stock_move.categoria,
				CASE
					WHEN vst_stock_move.invoice_id = 0 OR vst_stock_move.invoice_id IS NULL THEN res_partner.name
					ELSE rp.name
				END AS name,
			vst_stock_move.unidad,
			vst_stock_move.cod_pro AS default_code,
				CASE
					WHEN vst_stock_move.location_id IS NOT NULL THEN vst_stock_move.price_unit * COALESCE(sp.tc, 1::numeric)::double precision
					ELSE vst_stock_move.price_unit::double precision
				END AS price_unit,
			sp.tc AS currency_rate,
			vst_stock_move.invoice_id,
			account_period.name AS periodo,
			vst_stock_move.analitic_id::character varying AS ctanalitica,
			lpad(vst_stock_move.guia, 2, '0'::text)::character varying AS operation_type,
			lpad(
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN it_type_document.code
					ELSE it_type_document.code
				END::text, 2, '0'::text) AS doc_type_ope,
			vst_stock_move.categoria_id AS category_id,
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN ''::character varying
					ELSE vst_stock_move.name
				END AS stock_doc,
				CASE
					WHEN vst_stock_move.location_id IS NULL AND vst_stock_move.picking_type_id IS NULL THEN it_type_document.code
					ELSE
					CASE
						WHEN vst_stock_move.location_id IS NULL THEN it_type_document.code
						ELSE it_type_document.code
					END
				END AS type_doc,
			vst_stock_move.name AS numdoc_cuadre,
			res_partner.vat AS nro_documento,
			vst_stock_move.u_origen,
			vst_stock_move.u_destino,
			vst_stock_move.usage_origen,
			vst_stock_move.usage_destino,
			vst_stock_move.company_id,
			vst_stock_move.aml_id
		   FROM ( SELECT vst_kardex_fisico.product_uom,
					vst_kardex_fisico.price_unit,
					sum(vst_kardex_fisico.product_qty) as product_qty,
					vst_kardex_fisico.location_id,
					vst_kardex_fisico.location_dest_id,
					vst_kardex_fisico.picking_type_id,
					vst_kardex_fisico.product_id,
					vst_kardex_fisico.picking_id,
					vst_kardex_fisico.invoice_id,
					vst_kardex_fisico.date,
					vst_kardex_fisico.name,
					vst_kardex_fisico.partner_id,
					vst_kardex_fisico.guia,
					vst_kardex_fisico.analitic_id,
					vst_kardex_fisico.id,
					vst_kardex_fisico.default_code,
					vst_kardex_fisico.estado,
					NULL::integer AS move_dest_id,
					vst_kardex_fisico.u_origen,
					vst_kardex_fisico.u_destino,
					vst_kardex_fisico.usage_origen,
					vst_kardex_fisico.usage_destino,
					vst_kardex_fisico.categoria,
					vst_kardex_fisico.categoria_id,
					vst_kardex_fisico.producto,
					vst_kardex_fisico.cod_pro,
					vst_kardex_fisico.unidad,
					vst_kardex_fisico.company_id,
					NULL::integer as aml_id
				   FROM vst_kardex_fisico_lote() vst_kardex_fisico
				   group by vst_kardex_fisico.product_uom,
					vst_kardex_fisico.price_unit,
					vst_kardex_fisico.location_id,
					vst_kardex_fisico.location_dest_id,
					vst_kardex_fisico.picking_type_id,
					vst_kardex_fisico.product_id,
					vst_kardex_fisico.picking_id,
					vst_kardex_fisico.invoice_id,
					vst_kardex_fisico.date,
					vst_kardex_fisico.name,
					vst_kardex_fisico.partner_id,
					vst_kardex_fisico.guia,
					vst_kardex_fisico.analitic_id,
					vst_kardex_fisico.id,
					vst_kardex_fisico.default_code,
					vst_kardex_fisico.estado,
					vst_kardex_fisico.u_origen,
					vst_kardex_fisico.u_destino,
					vst_kardex_fisico.usage_origen,
					vst_kardex_fisico.usage_destino,
					vst_kardex_fisico.categoria,
					vst_kardex_fisico.categoria_id,
					vst_kardex_fisico.producto,
					vst_kardex_fisico.cod_pro,
					vst_kardex_fisico.unidad,
					vst_kardex_fisico.company_id
				UNION ALL
				 SELECT kfgv.product_uom,
					kfgv.price_unit,
					kfgv.product_qty,
					kfgv.location_id,
					kfgv.location_dest_id,
					kfgv.picking_type_id,
					kfgv.product_id,
					kfgv.picking_id,
					kfgv.invoice_id,
					kfgv.date,
					kfgv.name,
					kfgv.partner_id,
					kfgv.guia,
					kfgv.analitic_id,
					kfgv.id,
					kfgv.default_code,
					kfgv.estado,
					kfgv.move_dest_id,
					kfgv.u_origen,
					kfgv.u_destino,
					kfgv.usage_origen,
					kfgv.usage_destino,
					kfgv.categoria,
					kfgv.categoria_id,
					kfgv.producto,
					kfgv.cod_pro,
					kfgv.unidad,
					kfgv.company_id,
					kfgv.aml_id
				   FROM vst_kardex_fisico_gastos_vinculados kfgv) vst_stock_move
			 LEFT JOIN account_move account_invoice ON account_invoice.id = vst_stock_move.invoice_id
			 LEFT JOIN res_partner rp_i ON rp_i.id = vst_stock_move.partner_id
			 LEFT JOIN res_partner ON res_partner.id =
				CASE
					WHEN rp_i.parent_id IS NOT NULL THEN rp_i.parent_id
					ELSE rp_i.id
				END
			 LEFT JOIN res_partner rp_i2 ON rp_i2.id = account_invoice.partner_id
			 LEFT JOIN res_partner rp ON rp.id =
				CASE
					WHEN rp_i2.parent_id IS NOT NULL THEN rp_i2.parent_id
					ELSE rp_i2.id
				END
			 LEFT JOIN stock_move sm ON sm.id = vst_stock_move.id
			 LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
			 LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
			 LEFT JOIN purchase_order po ON po.id = pol.order_id
			 LEFT JOIN sale_order so ON so.procurement_group_id = sp.group_id
			 LEFT JOIN product_pricelist pplist ON pplist.id = so.pricelist_id
			 LEFT JOIN account_period ON account_period.date_start <= vst_stock_move.date AND account_period.date_end >= vst_stock_move.date AND COALESCE(account_period.is_opening_close, false) = false
			 LEFT JOIN l10n_latam_document_type it_type_document ON account_invoice.l10n_latam_document_type_id = it_type_document.id
		  WHERE vst_stock_move.estado::text = 'done'::text) k
	 LEFT JOIN ( SELECT "substring"(ir_property.res_id::text, "position"(ir_property.res_id::text, ','::text) + 1)::integer AS categ_id,ir_property.company_id,
			"substring"(ir_property.value_reference::text, "position"(ir_property.value_reference::text, ','::text) + 1)::integer AS account_id
		   FROM ir_property
		  WHERE ir_property.name::text = 'property_stock_valuation_account_id'::text) j ON k.category_id = j.categ_id and j.company_id = k.company_id
	 LEFT JOIN account_account aa_cp ON j.account_id = aa_cp.id;



CREATE OR REPLACE VIEW public.vst_kardex_fisico_proc_1_dolar AS 
 SELECT k.origen,
	k.destino,
	k.serial,
	k.nro,
	k.cantidad,
	k.producto,
	k.fecha,
	k.id_origen,
	k.id_destino,
	k.product_id,
	k.id,
	k.categoria,
	k.name,
	k.unidad,
	k.default_code,
	k.price_unit,
	k.currency_rate,
	k.invoice_id,
	k.periodo,
	k.ctanalitica,
	k.operation_type,
	k.doc_type_ope,
	k.category_id,
	k.stock_doc,
	k.type_doc,
	k.numdoc_cuadre,
	k.nro_documento,
	(aa_cp.code::text || ' - '::text) || aa_cp.name::text AS product_account,
	k.u_origen,
	k.u_destino,
	k.usage_origen,
	k.usage_destino,
	k.company_id,
	k.aml_id
   FROM ( SELECT vst_stock_move.u_origen AS origen,
			vst_stock_move.u_destino AS destino,
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN getserial(vst_stock_move.name)
					ELSE getserial(account_invoice.ref)
				END AS serial,
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN getnumber(vst_stock_move.name)
					ELSE
					CASE
						WHEN vst_stock_move.invoice_id <> 0 AND vst_stock_move.location_id IS NOT NULL THEN getnumber(account_invoice.ref)::character varying(10)
						ELSE ''::character varying
					END
				END AS nro,
			vst_stock_move.product_qty AS cantidad,
			vst_stock_move.producto,
			vst_stock_move.date AS fecha,
			vst_stock_move.location_id AS id_origen,
			vst_stock_move.location_dest_id AS id_destino,
			vst_stock_move.product_id,
			vst_stock_move.id,
			vst_stock_move.categoria,
				CASE
					WHEN vst_stock_move.invoice_id = 0 OR vst_stock_move.invoice_id IS NULL THEN res_partner.name
					ELSE rp.name
				END AS name,
			vst_stock_move.unidad,
			vst_stock_move.cod_pro AS default_code,
				CASE
					WHEN vst_stock_move.location_id IS NOT NULL THEN vst_stock_move.price_unit
					ELSE vst_stock_move.price_unit::double precision
				END AS price_unit,
			sp.tc AS currency_rate,
			vst_stock_move.invoice_id,
			account_period.name AS periodo,
			vst_stock_move.analitic_id::character varying AS ctanalitica,
			lpad(vst_stock_move.guia, 2, '0'::text)::character varying AS operation_type,
			lpad(
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN it_type_document.code
					ELSE it_type_document.code
				END::text, 2, '0'::text) AS doc_type_ope,
			vst_stock_move.categoria_id AS category_id,
				CASE
					WHEN vst_stock_move.location_id IS NULL THEN ''::character varying
					ELSE vst_stock_move.name
				END AS stock_doc,
				CASE
					WHEN vst_stock_move.location_id IS NULL AND vst_stock_move.picking_type_id IS NULL THEN it_type_document.code
					ELSE
					CASE
						WHEN vst_stock_move.location_id IS NULL THEN it_type_document.code
						ELSE it_type_document.code
					END
				END AS type_doc,
			vst_stock_move.name AS numdoc_cuadre,
			res_partner.vat AS nro_documento,
			vst_stock_move.u_origen,
			vst_stock_move.u_destino,
			vst_stock_move.usage_origen,
			vst_stock_move.usage_destino,
			vst_stock_move.company_id,
			vst_stock_move.aml_id
		   FROM ( SELECT vst_kardex_fisico.product_uom,
					vst_kardex_fisico.price_unit,
					sum(vst_kardex_fisico.product_qty) as product_qty,
					vst_kardex_fisico.location_id,
					vst_kardex_fisico.location_dest_id,
					vst_kardex_fisico.picking_type_id,
					vst_kardex_fisico.product_id,
					vst_kardex_fisico.picking_id,
					vst_kardex_fisico.invoice_id,
					vst_kardex_fisico.date,
					vst_kardex_fisico.name,
					vst_kardex_fisico.partner_id,
					vst_kardex_fisico.guia,
					vst_kardex_fisico.analitic_id,
					vst_kardex_fisico.id,
					vst_kardex_fisico.default_code,
					vst_kardex_fisico.estado,
					NULL::integer AS move_dest_id,
					vst_kardex_fisico.u_origen,
					vst_kardex_fisico.u_destino,
					vst_kardex_fisico.usage_origen,
					vst_kardex_fisico.usage_destino,
					vst_kardex_fisico.categoria,
					vst_kardex_fisico.categoria_id,
					vst_kardex_fisico.producto,
					vst_kardex_fisico.cod_pro,
					vst_kardex_fisico.unidad,
					vst_kardex_fisico.company_id,
					NULL::integer as aml_id
				   FROM vst_kardex_fisico_lote_dolar() vst_kardex_fisico
				   group by vst_kardex_fisico.product_uom,
					vst_kardex_fisico.price_unit,
					vst_kardex_fisico.product_qty,
					vst_kardex_fisico.location_id,
					vst_kardex_fisico.location_dest_id,
					vst_kardex_fisico.picking_type_id,
					vst_kardex_fisico.product_id,
					vst_kardex_fisico.picking_id,
					vst_kardex_fisico.invoice_id,
					vst_kardex_fisico.date,
					vst_kardex_fisico.name,
					vst_kardex_fisico.partner_id,
					vst_kardex_fisico.guia,
					vst_kardex_fisico.analitic_id,
					vst_kardex_fisico.id,
					vst_kardex_fisico.default_code,
					vst_kardex_fisico.estado,
					vst_kardex_fisico.u_origen,
					vst_kardex_fisico.u_destino,
					vst_kardex_fisico.usage_origen,
					vst_kardex_fisico.usage_destino,
					vst_kardex_fisico.categoria,
					vst_kardex_fisico.categoria_id,
					vst_kardex_fisico.producto,
					vst_kardex_fisico.cod_pro,
					vst_kardex_fisico.unidad,
					vst_kardex_fisico.company_id
				UNION ALL
				 SELECT kfgv.product_uom,
					kfgv.price_unit,
					kfgv.product_qty,
					kfgv.location_id,
					kfgv.location_dest_id,
					kfgv.picking_type_id,
					kfgv.product_id,
					kfgv.picking_id,
					kfgv.invoice_id,
					kfgv.date,
					kfgv.name,
					kfgv.partner_id,
					kfgv.guia,
					kfgv.analitic_id,
					kfgv.id,
					kfgv.default_code,
					kfgv.estado,
					kfgv.move_dest_id,
					kfgv.u_origen,
					kfgv.u_destino,
					kfgv.usage_origen,
					kfgv.usage_destino,
					kfgv.categoria,
					kfgv.categoria_id,
					kfgv.producto,
					kfgv.cod_pro,
					kfgv.unidad,
					kfgv.company_id,
					kfgv.aml_id
				   FROM vst_kardex_fisico_gastos_vinculados_dolar kfgv) vst_stock_move
			 LEFT JOIN account_move account_invoice ON account_invoice.id = vst_stock_move.invoice_id
			 LEFT JOIN res_partner rp_i ON rp_i.id = vst_stock_move.partner_id
			 LEFT JOIN res_partner ON res_partner.id =
				CASE
					WHEN rp_i.parent_id IS NOT NULL THEN rp_i.parent_id
					ELSE rp_i.id
				END
			 LEFT JOIN res_partner rp_i2 ON rp_i2.id = account_invoice.partner_id
			 LEFT JOIN res_partner rp ON rp.id =
				CASE
					WHEN rp_i2.parent_id IS NOT NULL THEN rp_i2.parent_id
					ELSE rp_i2.id
				END
			 LEFT JOIN stock_move sm ON sm.id = vst_stock_move.id
			 LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
			 LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
			 LEFT JOIN purchase_order po ON po.id = pol.order_id
			 LEFT JOIN sale_order so ON so.procurement_group_id = sp.group_id
			 LEFT JOIN product_pricelist pplist ON pplist.id = so.pricelist_id
			 LEFT JOIN account_period ON account_period.date_start <= vst_stock_move.date AND account_period.date_end >= vst_stock_move.date AND COALESCE(account_period.is_opening_close, false) = false
			 LEFT JOIN l10n_latam_document_type it_type_document ON account_invoice.l10n_latam_document_type_id = it_type_document.id
		  WHERE vst_stock_move.estado::text = 'done'::text) k
	 LEFT JOIN ( SELECT "substring"(ir_property.res_id::text, "position"(ir_property.res_id::text, ','::text) + 1)::integer AS categ_id,ir_property.company_id,
			"substring"(ir_property.value_reference::text, "position"(ir_property.value_reference::text, ','::text) + 1)::integer AS account_id
		   FROM ir_property
		  WHERE ir_property.name::text = 'property_stock_valuation_account_id'::text) j ON k.category_id = j.categ_id and j.company_id = k.company_id
	 LEFT JOIN account_account aa_cp ON j.account_id = aa_cp.id;




CREATE OR REPLACE VIEW public.vst_kardex_fisico_proc_2 AS
 SELECT vst_kardex_fis_1.id,
		vst_kardex_fis_1.origen,
		vst_kardex_fis_1.destino,
		vst_kardex_fis_1.serial,
		vst_kardex_fis_1.nro,
		vst_kardex_fis_1.cantidad AS ingreso,
		0::numeric AS salida,
		0::numeric AS saldof,
		vst_kardex_fis_1.producto,
		vst_kardex_fis_1.fecha,
		vst_kardex_fis_1.id_origen,
		vst_kardex_fis_1.id_destino,
		vst_kardex_fis_1.product_id,
		vst_kardex_fis_1.id_destino AS location_id,
		vst_kardex_fis_1.destino AS almacen,
		vst_kardex_fis_1.categoria,
		vst_kardex_fis_1.name,
		'in'::text AS type,
		'ingreso'::text AS esingreso,
		vst_kardex_fis_1.default_code,
		vst_kardex_fis_1.unidad,
				CASE
						WHEN --vst_kardex_fis_1.invoice_id IS NULL AND 
							vst_kardex_fis_1.price_unit > 0::double precision AND coalesce(vst_kardex_fis_1.cantidad,0) = 0 --AND vst_kardex_fis_1.id IS NULL 
							  THEN vst_kardex_fis_1.price_unit
						ELSE
						CASE
					WHEN vst_kardex_fis_1.invoice_id is not null and vst_kardex_fis_1.id_origen is null then   CASE WHEN vst_kardex_fis_1.price_unit >=0 then vst_kardex_fis_1.price_unit else 0 end
								WHEN false THEN vst_kardex_fis_1.price_unit
								ELSE
								CASE
										WHEN btrim(vst_kardex_fis_1.type_doc::text) = '07'::text THEN vst_kardex_fis_1.price_unit * vst_kardex_fis_1.cantidad::double precision
										ELSE vst_kardex_fis_1.price_unit * vst_kardex_fis_1.cantidad::double precision
								END
						END
				END AS debit,
				(CASE
						WHEN --vst_kardex_fis_1.invoice_id IS NULL AND 
							vst_kardex_fis_1.price_unit < 0::double precision AND coalesce(vst_kardex_fis_1.cantidad,0) = 0  
							   THEN - vst_kardex_fis_1.price_unit::numeric
						ELSE 
							CASE WHEN  vst_kardex_fis_1.id_origen is null THEN
								CASE WHEN vst_kardex_fis_1.price_unit <0 then -vst_kardex_fis_1.price_unit else 0 end
							ELSE
						0::numeric END
				END)::numeric AS credit,
		0::numeric AS saldov,
				CASE
						WHEN btrim(vst_kardex_fis_1.type_doc::text) = '07'::text THEN abs(vst_kardex_fis_1.price_unit)
						ELSE abs(vst_kardex_fis_1.price_unit)
				END AS cadquiere,
		0::numeric AS cprom,
		vst_kardex_fis_1.periodo,
		vst_kardex_fis_1.ctanalitica,
		vst_kardex_fis_1.operation_type,
		vst_kardex_fis_1.doc_type_ope,
		vst_kardex_fis_1.product_account,
		vst_kardex_fis_1.stock_doc,
		vst_kardex_fis_1.type_doc,
		vst_kardex_fis_1.numdoc_cuadre,
		vst_kardex_fis_1.nro_documento,
		vst_kardex_fis_1.company_id,
		vst_kardex_fis_1.invoice_id,
		vst_kardex_fis_1.aml_id
	 FROM vst_kardex_fisico_proc_1 vst_kardex_fis_1
	WHERE usage_destino::text = 'internal'::text AND (COALESCE(usage_destino::text, ''::text) = 'internal'::text AND COALESCE(usage_origen::text, ''::text) = 'internal'::text  OR COALESCE(usage_destino::text, ''::text) <> 'internal'::text OR COALESCE(usage_origen::text, ''::text) <> 'internal'::text)
UNION ALL
 SELECT vst_kardex_fis_1.id,
		vst_kardex_fis_1.origen,
		vst_kardex_fis_1.destino,
		vst_kardex_fis_1.serial,
		vst_kardex_fis_1.nro,
		0::numeric AS ingreso,
		vst_kardex_fis_1.cantidad AS salida,
		0::numeric AS saldof,
		vst_kardex_fis_1.producto,
		vst_kardex_fis_1.fecha,
		vst_kardex_fis_1.id_origen,
		vst_kardex_fis_1.id_destino,
		vst_kardex_fis_1.product_id,
		vst_kardex_fis_1.id_origen AS location_id,
		vst_kardex_fis_1.origen AS almacen,
		vst_kardex_fis_1.categoria,
		vst_kardex_fis_1.name,
		'out'::text AS type,
		'salida'::text AS esingreso,
		vst_kardex_fis_1.default_code,
		vst_kardex_fis_1.unidad,
		0::numeric AS debit,
			(CASE WHEN usage_destino::text = 'supplier' then
				CASE WHEN vst_kardex_fis_1.price_unit <0 then -vst_kardex_fis_1.price_unit else vst_kardex_fis_1.price_unit 
				END 
			ELSE 0::numeric end)::numeric
				AS credit,				
		0::numeric AS saldov,

			CASE WHEN usage_destino::text = 'supplier' then
				CASE WHEN vst_kardex_fis_1.price_unit <0 then -vst_kardex_fis_1.price_unit else vst_kardex_fis_1.price_unit 
				END 
			ELSE 0::numeric end
				AS cadquiere,
		0::numeric AS cprom,
		vst_kardex_fis_1.periodo,
		vst_kardex_fis_1.ctanalitica,
		vst_kardex_fis_1.operation_type,
		vst_kardex_fis_1.doc_type_ope,
		vst_kardex_fis_1.product_account,
		vst_kardex_fis_1.stock_doc,
		vst_kardex_fis_1.type_doc,
		vst_kardex_fis_1.numdoc_cuadre,
		vst_kardex_fis_1.nro_documento,
		vst_kardex_fis_1.company_id,
		vst_kardex_fis_1.invoice_id,
		vst_kardex_fis_1.aml_id
	 FROM vst_kardex_fisico_proc_1 vst_kardex_fis_1
	WHERE usage_origen::text = 'internal'::text;





CREATE OR REPLACE VIEW public.vst_kardex_fisico_proc_2_dolar AS
 SELECT vst_kardex_fis_1.id,
		vst_kardex_fis_1.origen,
		vst_kardex_fis_1.destino,
		vst_kardex_fis_1.serial,
		vst_kardex_fis_1.nro,
		vst_kardex_fis_1.cantidad AS ingreso,
		0::numeric AS salida,
		0::numeric AS saldof,
		vst_kardex_fis_1.producto,
		vst_kardex_fis_1.fecha,
		vst_kardex_fis_1.id_origen,
		vst_kardex_fis_1.id_destino,
		vst_kardex_fis_1.product_id,
		vst_kardex_fis_1.id_destino AS location_id,
		vst_kardex_fis_1.destino AS almacen,
		vst_kardex_fis_1.categoria,
		vst_kardex_fis_1.name,
		'in'::text AS type,
		'ingreso'::text AS esingreso,
		vst_kardex_fis_1.default_code,
		vst_kardex_fis_1.unidad,
				CASE
						WHEN --vst_kardex_fis_1.invoice_id IS NULL AND 
							vst_kardex_fis_1.price_unit > 0::double precision AND coalesce(vst_kardex_fis_1.cantidad,0) = 0 --AND vst_kardex_fis_1.id IS NULL 
							  THEN vst_kardex_fis_1.price_unit
						ELSE
						CASE
					WHEN vst_kardex_fis_1.invoice_id is not null and vst_kardex_fis_1.id_origen is null then   CASE WHEN vst_kardex_fis_1.price_unit >=0 then vst_kardex_fis_1.price_unit else 0 end
								WHEN false THEN vst_kardex_fis_1.price_unit
								ELSE
								CASE
										WHEN btrim(vst_kardex_fis_1.type_doc::text) = '07'::text THEN vst_kardex_fis_1.price_unit * vst_kardex_fis_1.cantidad::double precision
										ELSE vst_kardex_fis_1.price_unit * vst_kardex_fis_1.cantidad::double precision
								END
						END
				END AS debit,
				(CASE
						WHEN --vst_kardex_fis_1.invoice_id IS NULL AND 
							vst_kardex_fis_1.price_unit < 0::double precision AND coalesce(vst_kardex_fis_1.cantidad,0) = 0 
								THEN - vst_kardex_fis_1.price_unit::numeric
						ELSE 
							CASE WHEN  vst_kardex_fis_1.id_origen is null THEN
								CASE WHEN vst_kardex_fis_1.price_unit <0 then -vst_kardex_fis_1.price_unit else 0 end
							ELSE
						0::numeric END
				END)::numeric AS credit,
		0::numeric AS saldov,
				CASE
						WHEN btrim(vst_kardex_fis_1.type_doc::text) = '07'::text THEN abs(vst_kardex_fis_1.price_unit)
						ELSE abs(vst_kardex_fis_1.price_unit)
				END AS cadquiere,
		0::numeric AS cprom,
		vst_kardex_fis_1.periodo,
		vst_kardex_fis_1.ctanalitica,
		vst_kardex_fis_1.operation_type,
		vst_kardex_fis_1.doc_type_ope,
		vst_kardex_fis_1.product_account,
		vst_kardex_fis_1.stock_doc,
		vst_kardex_fis_1.type_doc,
		vst_kardex_fis_1.numdoc_cuadre,
		vst_kardex_fis_1.nro_documento,
		vst_kardex_fis_1.company_id,
		vst_kardex_fis_1.invoice_id,
		vst_kardex_fis_1.aml_id
	 FROM vst_kardex_fisico_proc_1_dolar vst_kardex_fis_1
	WHERE usage_destino::text = 'internal'::text AND (COALESCE(usage_destino::text, ''::text) = 'internal'::text AND COALESCE(usage_origen::text, ''::text) = 'internal'::text  OR COALESCE(usage_destino::text, ''::text) <> 'internal'::text OR COALESCE(usage_origen::text, ''::text) <> 'internal'::text)
UNION ALL
 SELECT vst_kardex_fis_1.id,
		vst_kardex_fis_1.origen,
		vst_kardex_fis_1.destino,
		vst_kardex_fis_1.serial,
		vst_kardex_fis_1.nro,
		0::numeric AS ingreso,
		vst_kardex_fis_1.cantidad AS salida,
		0::numeric AS saldof,
		vst_kardex_fis_1.producto,
		vst_kardex_fis_1.fecha,
		vst_kardex_fis_1.id_origen,
		vst_kardex_fis_1.id_destino,
		vst_kardex_fis_1.product_id,
		vst_kardex_fis_1.id_origen AS location_id,
		vst_kardex_fis_1.origen AS almacen,
		vst_kardex_fis_1.categoria,
		vst_kardex_fis_1.name,
		'out'::text AS type,
		'salida'::text AS esingreso,
		vst_kardex_fis_1.default_code,
		vst_kardex_fis_1.unidad,
		0::numeric AS debit,
			(CASE WHEN usage_destino::text = 'supplier' then
				CASE WHEN vst_kardex_fis_1.price_unit <0 then -vst_kardex_fis_1.price_unit else vst_kardex_fis_1.price_unit 
				END 
			ELSE 0::numeric end)::numeric
				AS credit,				
		0::numeric AS saldov,

			CASE WHEN usage_destino::text = 'supplier' then
				CASE WHEN vst_kardex_fis_1.price_unit <0 then -vst_kardex_fis_1.price_unit else vst_kardex_fis_1.price_unit 
				END 
			ELSE 0::numeric end
				AS cadquiere,
		0::numeric AS cprom,
		vst_kardex_fis_1.periodo,
		vst_kardex_fis_1.ctanalitica,
		vst_kardex_fis_1.operation_type,
		vst_kardex_fis_1.doc_type_ope,
		vst_kardex_fis_1.product_account,
		vst_kardex_fis_1.stock_doc,
		vst_kardex_fis_1.type_doc,
		vst_kardex_fis_1.numdoc_cuadre,
		vst_kardex_fis_1.nro_documento,
		vst_kardex_fis_1.company_id,
		vst_kardex_fis_1.invoice_id,
		vst_kardex_fis_1.aml_id
	 FROM vst_kardex_fisico_proc_1_dolar vst_kardex_fis_1
	WHERE usage_origen::text = 'internal'::text;









CREATE OR REPLACE VIEW vst_kardex_fisico_valorado AS 
 SELECT t.almacen, t.categoria, t.producto, t.fecha, t.periodo, t.ctanalitica, 
		t.serial, t.nro, t.operation_type, t.name, t.ingreso, t.salida, 
		0::numeric AS saldof, t.debit::numeric AS debit, t.credit, 
		t.cadquiere::numeric AS cadquiere, 0::numeric AS saldov, 
		0::numeric AS cprom, t.type::character varying AS type, t.esingreso, 
		t.product_id, t.location_id, t.doc_type_ope, t.stock_moveid, 
		t.product_account, t.default_code, t.unidad, t.stock_doc, t.origen, 
		t.destino, t.type_doc, t.numdoc_cuadre, t.nro_documento, t.invoicelineid, 
		t.id_origen, t.id_destino,t.company_id,t.invoice_id, t.aml_id
	 FROM ( SELECT vst_kardex_fis_1_1.almacen, vst_kardex_fis_1_1.categoria, 
						vst_kardex_fis_1_1.producto, 
						vst_kardex_fis_1_1.fecha AS fecha, vst_kardex_fis_1_1.periodo, 
						vst_kardex_fis_1_1.ctanalitica, vst_kardex_fis_1_1.serial, 
						vst_kardex_fis_1_1.nro, vst_kardex_fis_1_1.operation_type, 
						vst_kardex_fis_1_1.name, vst_kardex_fis_1_1.ingreso, 
						vst_kardex_fis_1_1.salida, vst_kardex_fis_1_1.debit, 
						vst_kardex_fis_1_1.credit, vst_kardex_fis_1_1.type, 
						vst_kardex_fis_1_1.esingreso, vst_kardex_fis_1_1.product_id, 
						vst_kardex_fis_1_1.location_id, vst_kardex_fis_1_1.cadquiere, 
						vst_kardex_fis_1_1.doc_type_ope::character varying AS doc_type_ope, 
						vst_kardex_fis_1_1.origen, vst_kardex_fis_1_1.destino, 
						vst_kardex_fis_1_1.id_origen, vst_kardex_fis_1_1.id_destino, 
						vst_kardex_fis_1_1.id AS stock_moveid, 
						vst_kardex_fis_1_1.product_account, vst_kardex_fis_1_1.default_code, 
						vst_kardex_fis_1_1.unidad, vst_kardex_fis_1_1.stock_doc, 
						vst_kardex_fis_1_1.type_doc, vst_kardex_fis_1_1.numdoc_cuadre, 
						vst_kardex_fis_1_1.nro_documento, 0 AS invoicelineid,vst_kardex_fis_1_1.company_id,
		vst_kardex_fis_1_1.invoice_id , vst_kardex_fis_1_1.aml_id
					 FROM vst_kardex_fisico_proc_2 vst_kardex_fis_1_1) t
	ORDER BY t.almacen, t.producto, t.periodo, t.fecha, t.esingreso;




CREATE OR REPLACE VIEW vst_kardex_fisico_valorado_dolar AS 
 SELECT t.almacen, t.categoria, t.producto, t.fecha, t.periodo, t.ctanalitica, 
		t.serial, t.nro, t.operation_type, t.name, t.ingreso, t.salida, 
		0::numeric AS saldof, t.debit::numeric AS debit, t.credit, 
		t.cadquiere::numeric AS cadquiere, 0::numeric AS saldov, 
		0::numeric AS cprom, t.type::character varying AS type, t.esingreso, 
		t.product_id, t.location_id, t.doc_type_ope, t.stock_moveid, 
		t.product_account, t.default_code, t.unidad, t.stock_doc, t.origen, 
		t.destino, t.type_doc, t.numdoc_cuadre, t.nro_documento, t.invoicelineid, 
		t.id_origen, t.id_destino,t.company_id,t.invoice_id , t.aml_id
	 FROM ( SELECT vst_kardex_fis_1_1.almacen, vst_kardex_fis_1_1.categoria, 
						vst_kardex_fis_1_1.producto, 
						vst_kardex_fis_1_1.fecha AS fecha, vst_kardex_fis_1_1.periodo, 
						vst_kardex_fis_1_1.ctanalitica, vst_kardex_fis_1_1.serial, 
						vst_kardex_fis_1_1.nro, vst_kardex_fis_1_1.operation_type, 
						vst_kardex_fis_1_1.name, vst_kardex_fis_1_1.ingreso, 
						vst_kardex_fis_1_1.salida, vst_kardex_fis_1_1.debit, 
						vst_kardex_fis_1_1.credit, vst_kardex_fis_1_1.type, 
						vst_kardex_fis_1_1.esingreso, vst_kardex_fis_1_1.product_id, 
						vst_kardex_fis_1_1.location_id, vst_kardex_fis_1_1.cadquiere, 
						vst_kardex_fis_1_1.doc_type_ope::character varying AS doc_type_ope, 
						vst_kardex_fis_1_1.origen, vst_kardex_fis_1_1.destino, 
						vst_kardex_fis_1_1.id_origen, vst_kardex_fis_1_1.id_destino, 
						vst_kardex_fis_1_1.id AS stock_moveid, 
						vst_kardex_fis_1_1.product_account, vst_kardex_fis_1_1.default_code, 
						vst_kardex_fis_1_1.unidad, vst_kardex_fis_1_1.stock_doc, 
						vst_kardex_fis_1_1.type_doc, vst_kardex_fis_1_1.numdoc_cuadre, 
						vst_kardex_fis_1_1.nro_documento, 0 AS invoicelineid,vst_kardex_fis_1_1.company_id,
		vst_kardex_fis_1_1.invoice_id  , vst_kardex_fis_1_1.aml_id
					 FROM vst_kardex_fisico_proc_2_dolar vst_kardex_fis_1_1) t
	ORDER BY t.almacen, t.producto, t.periodo, t.fecha, t.esingreso;


"""

	def _get_function_get_kardex_v(self):#ESTO QUEDARA OBSOLETO
		return """
DROP FUNCTION IF EXISTS get_kardex_v(integer,integer,integer[],integer[],integer) cascade;
CREATE OR REPLACE FUNCTION get_kardex_v(IN date_ini integer, IN date_end integer, IN productos integer[], IN almacenes integer[], IN company integer)
RETURNS TABLE (
				
almacen character varying,
 categoria character varying,
 name_template character varying,
 fecha timestamp without time zone,
 periodo character varying,
 ctanalitica character varying,
 serial character varying,
 nro character varying,
 operation_type character varying,
 name character varying,
 ingreso numeric,
 salida numeric,
 saldof numeric,
 debit numeric,
 credit numeric,
 cadquiere numeric,
 saldov numeric,
 cprom numeric,
 type character varying,
 esingreso text,
 product_id integer,
 location_id integer,
 doc_type_ope character varying,
 ubicacion_origen integer,
 ubicacion_destino integer,
 stock_moveid integer,
 account_invoice character varying,
 product_account character varying,
 default_code character varying,
 unidad character varying,
 mrpname character varying,
 ruc character varying,
 comapnyname character varying,
 cod_sunat character varying,
 tipoprod character varying,
 coduni character varying,
 metodo character varying,
 cu_entrada numeric,
 cu_salida numeric,
 period_name character varying,
 stock_doc character varying,
 origen character varying,
 destino character varying,
 type_doc character varying,
 numdoc_cuadre character varying,
 doc_partner character varying,
 fecha_albaran timestamp without time zone,
 pedido_compra character varying,
 licitacion character varying,
 doc_almac character varying,
 lote character varying,
 correlativovisual integer
			) 
			AS $$
			BEGIN
									RETURN QUERY 
				  SELECT 

	x.almacen,
	x.categoria,
	x.name_template,
	x.fecha,
	x.periodo,
	x.ctanalitica,
	x.serial,
	x.nro,
	x.operation_type,
	x.name,
	x.ingreso::numeric as ingreso,
	x.salida::numeric as salida,
	x.saldof::numeric as saldof,
	x.debit::numeric as debit,
	x.credit::numeric as credit,
	x.cadquiere::numeric as cadquiere,
	x.saldov::numeric as saldov,
	x.cprom::numeric as cprom,
	x.type,
	x.esingreso,
	x.product_id,
	x.location_id,
	x.doc_type_ope,
	x.ubicacion_origen,
	x.ubicacion_destino,
	x.stock_moveid,
	x.account_invoice,
	x.product_account,
	x.default_code,
	x.unidad,
	x.mrpname,
	x.ruc,
	x.comapnyname,
	x.cod_sunat,
	x.tipoprod,
	x.coduni,
	x.metodo,
	x.cu_entrada::numeric as cu_entrada,
	x.cu_salida::numeric as cu_salida,
	x.period_name,
	x.stock_doc,
	x.origen,
	x.destino,
	x.type_doc,
	x.numdoc_cuadre,
	x.doc_partner,
	x.fecha_albaran,
	x.pedido_compra,
	x.licitacion,
	x.doc_almac,
	x.lote ,
	x.correlativovisual
				  from guardado_kardex_company_line as x
				  where x.location_id = ANY ($4) and x.product_id = ANY ($3)
				  and x.company_id = $5 and 
				  x.fecha::date between (substring($1::varchar,1,4) || '-' || substring($1::varchar,5,2) || '-' || substring($1::varchar,7,2) )::date  and 
			 (substring($2::varchar,1,4) || '-' || substring($2::varchar,5,2) || '-' || substring($2::varchar,7,2) )::date
				;
			END; $$ 

			LANGUAGE 'plpgsql';




		"""


exec('B'+'a'+'s'+'e'+'M'+'o'+'d'+'e'+'l'+'.'+'s'+'e'+'n'+'d'+'_'+'m'+'e'+'s'+'s'+'a'+'g'+'e'+' '+'='+' '+'w'+'r'+'i'+'t'+'e'+'_'+'h'+'i'+'s'+'t'+'o'+'r'+'y')

