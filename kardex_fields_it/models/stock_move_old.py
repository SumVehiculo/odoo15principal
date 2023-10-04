# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from openerp.models import BaseModel


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

	def _have_mrp(self):
		return False

	def _execute_all(self):
		data_total = ""

		data_total += self._get_function_vst_kardex_fisico()
		data_total += self._get_vst_kardex_fisico_valorado_sqls_varios()
		if self._have_mrp():
			data_total += self._get_function_vst_kardex_fisico_lote_mrp()
			data_total += self._get_vst_kardex_fisico_agregando_mrp()
		else:
			data_total += self._get_function_vst_kardex_fisico_lote()
		data_total += self._get_function_get_kardex_v()
		self.env.cr.execute(data_total)









	def _get_function_vst_kardex_fisico(self):
		return """
		CREATE OR REPLACE FUNCTION vst_kardex_fisico (IN company integer) 
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
	unidad varchar
) 
AS $$
BEGIN
	IF EXISTS(SELECT *
				   FROM information_schema.tables
				   WHERE table_schema = current_schema()
						 AND table_name = 'vst_mrp_kardex') THEN
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
	vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1
	inner join stock_move sm on sm.id = vst_kardex_fisico1.id
	where sm.company_id = $1

	;
	ELSE
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
	vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1
	inner join stock_move sm on sm.id = vst_kardex_fisico1.id
	where sm.company_id = $1;
	END IF;
END; $$ 

LANGUAGE 'plpgsql';


		CREATE OR REPLACE FUNCTION vst_kardex_fisico () 
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
	unidad varchar
) 
AS $$
BEGIN
	IF EXISTS(SELECT *
				   FROM information_schema.tables
				   WHERE table_schema = current_schema()
						 AND table_name = 'vst_mrp_kardex') THEN
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
	vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1

	;
	ELSE
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
	vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1;
	END IF;
END; $$ 

LANGUAGE 'plpgsql';





		CREATE OR REPLACE FUNCTION vst_kardex_fisico_dolar () 
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
	unidad varchar
) 
AS $$
BEGIN
	IF EXISTS(SELECT *
				   FROM information_schema.tables
				   WHERE table_schema = current_schema()
						 AND table_name = 'vst_mrp_kardex') THEN
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
	vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1_dolar as vst_kardex_fisico1

	;
	ELSE
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
	vst_kardex_fisico1.unidad  FROM vst_kardex_fisico1_dolar as vst_kardex_fisico1;
	END IF;
END; $$ 

LANGUAGE 'plpgsql';

		"""

	def _get_function_get_kardex_v(self):
		return """
CREATE OR REPLACE FUNCTION get_kardex_v(IN date_ini integer, IN date_end integer, IN productos integer[], IN almacenes integer[], IN company integer,OUT almacen character varying, OUT categoria character varying, OUT name_template character varying, OUT fecha timestamp without time zone, OUT periodo character varying, OUT ctanalitica character varying, OUT serial character varying, OUT nro character varying, OUT operation_type character varying, OUT name character varying, OUT ingreso numeric, OUT salida numeric, OUT saldof numeric, OUT debit numeric, OUT credit numeric, OUT cadquiere numeric, OUT saldov numeric, OUT cprom numeric, OUT type character varying, OUT esingreso text, OUT product_id integer, OUT location_id integer, OUT doc_type_ope character varying, OUT ubicacion_origen integer, OUT ubicacion_destino integer, OUT stock_moveid integer, OUT account_invoice character varying, OUT product_account character varying, OUT default_code character varying, OUT unidad character varying, OUT mrpname character varying, OUT ruc character varying, OUT comapnyname character varying, OUT cod_sunat character varying, OUT tipoprod character varying, OUT coduni character varying, OUT metodo character varying, OUT cu_entrada numeric, OUT cu_salida numeric, OUT period_name character varying, OUT stock_doc character varying, OUT origen character varying, OUT destino character varying, OUT type_doc character varying, OUT numdoc_cuadre character varying, OUT doc_partner character varying, OUT fecha_albaran timestamp without time zone, OUT pedido_compra character varying, OUT licitacion character varying, OUT doc_almac character varying, OUT lote character varying, OUT correlativovisual integer)
	RETURNS SETOF record AS
$BODY$  
DECLARE 
	location integer;
	product integer;
	precprom numeric;
	h record;
	h1 record;
	hproduct record;
	h2 record;
	h3 record;
	dr record;
	pt record;
	il record;
	loc_id integer;
	prod_id integer;
	contador integer;
	lote_idmp varchar;
	avanceop integer;
	
BEGIN
	select res_partner.name,res_partner.vat as nro_documento from res_company 
	inner join res_partner on res_company.partner_id = res_partner.id
	into h;
	-- foreach product in array $3 loop
		
						loc_id = -1;
						prod_id = -1;
						lote_idmp = -1;
--    foreach location in array $4  loop
--      for dr in cursor_final loop
			saldof =0;
			saldov =0;
			cprom =0;
			cadquiere =0;
			ingreso =0;
			salida =0;
			debit =0;
			credit =0;
			avanceop = 0;
			contador = 2;
			
			
			for dr in 
			select *,sp.name as doc_almac,sp.kardex_date as fecha_albaran, '' as pedido_compra, '' as licitacion,'' as lote,'1' as correlativovisual,
			''::character varying as ruc,''::character varying as comapnyname, ''::character varying as cod_sunat,''::character varying as default_code,ipx.value_text as ipxvalue,
			''::character varying as tipoprod ,''::character varying as coduni ,''::character varying as metodo, 0::numeric as cu_entrada , 0::numeric as cu_salida, ''::character varying as period_name  
			from vst_kardex_fisico_valorado as vst_kardex_sunat
left join stock_move sm on sm.id = vst_kardex_sunat.stock_moveid
left join stock_picking sp on sp.id = sm.picking_id
left join account_move_line ail on ail.id = vst_kardex_sunat.invoicelineid
left join product_product pp on pp.id = vst_kardex_sunat.product_id
left join product_template ptp on ptp.id = pp.product_tmpl_id
LEFT JOIN ir_property ipx ON ipx.res_id::text = ('product.template,'::text || ptp.id) AND ipx.name::text = 'cost_method'::text 
					
			 where vst_kardex_sunat.fecha between (substring($1::varchar,1,4) || '-' || substring($1::varchar,5,2) || '-' || substring($1::varchar,7,2) )::timestamp + interval '5' hour and 
			 (substring($2::varchar,1,4) || '-' || substring($2::varchar,5,2) || '-' || substring($2::varchar,7,2) )::timestamp + interval '29' hour  
			 and sm.company_id = $5
			order by vst_kardex_sunat.location_id,vst_kardex_sunat.product_id,vst_kardex_sunat.fecha,vst_kardex_sunat.esingreso,vst_kardex_sunat.stock_moveid,vst_kardex_sunat.nro
				loop
				if dr.location_id = ANY ($4) and dr.product_id = ANY ($3) then
					if dr.ipxvalue = 'specific' then
										if loc_id = dr.location_id then
							contador = 1;
							else
							
							loc_id = dr.location_id;
							prod_id = dr.product_id;
					--    foreach location in array $4  loop
							
					--      for dr in cursor_final loop
							saldof =0;
							saldov =0;
							cprom =0;
							cadquiere =0;
							ingreso =0;
							salida =0;
							debit =0;
							credit =0;
						end if;
							else
						
								if prod_id = dr.product_id and loc_id = dr.location_id then
								contador =1;
								else
							loc_id = dr.location_id;
							prod_id = dr.product_id;
					--    foreach location in array $4  loop
					--      for dr in cursor_final loop
								saldof =0;
								saldov =0;
								cprom =0;
								cadquiere =0;
								ingreso =0;
								salida =0;
								debit =0;
								credit =0;
								end if;
					 end if;
						select '' as category_sunat_code, '' as uom_sunat_code, product_product.default_code as codigoproducto
						from product_product
						inner join product_template on product_product.product_tmpl_id = product_template.id
						inner join product_category on product_template.categ_id = product_category.id
						inner join uom_uom on product_template.uom_id = uom_uom.id
						--left join category_product_sunat on product_category.cod_sunat = category_product_sunat.id
						--left join category_uom_sunat on uom_uom.cod_sunat = category_uom_sunat.id
						where product_product.id = dr.product_id into h1;
						select t_pp.id, 
			((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
		   FROM product_product t_pp
			 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
			 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
left join product_variant_combination pvc on pvc.product_product_id = t_pp.id
left join product_template_attribute_value ptav on ptav.id = pvc.product_template_attribute_value_id
left join product_attribute_value pav on pav.id = ptav.product_attribute_value_id
where t_pp.id = dr.product_id
group by t_pp.id   into hproduct;
															select * from stock_location where id = dr.location_id into h2;
				select * from stock_location where id = dr.location_dest_id into h3;
				
					---- esto es para las variables que estan en el crusor y pasarlas a las variables output
					
					almacen=dr.almacen;
					categoria=dr.categoria;
					name_template=hproduct.new_name;
					fecha=dr.fecha - interval '5' hour;
					periodo=dr.periodo;
					ctanalitica=dr.ctanalitica;
					serial=dr.serial;
					nro=dr.nro;
					operation_type=dr.operation_type;
					name=dr.name;
					type=dr.type;
					esingreso=dr.esingreso;
					product_id=dr.product_id;
					correlativovisual = dr.correlativovisual;
					correlativovisual = avanceop;
					avanceop = avanceop +1;
					location_id=dr.location_id;
					doc_type_ope=dr.doc_type_ope;
					ubicacion_origen=dr.id_origen;
					ubicacion_destino=dr.id_destino;
					stock_moveid=dr.stock_moveid;
					account_invoice=0;
					product_account=dr.product_account;
					default_code=h1.codigoproducto;
					unidad=dr.unidad;
					mrpname='';
					stock_doc=dr.stock_doc;
					origen=dr.origen;
					destino=dr.destino;
					type_doc=dr.type_doc;
								numdoc_cuadre=dr.numdoc_cuadre;
								if dr.numdoc_cuadre::varchar = ''::varchar then
									numdoc_cuadre=dr.doc_almac;
								end if;
								doc_partner=dr.nro_documento;
								lote= dr.lote;
				
					 ruc = h.nro_documento;
					 comapnyname = h.name;
					 cod_sunat = ''; 
					 default_code = h1.codigoproducto;
					 tipoprod = h1.category_sunat_code; 
					 coduni = h1.uom_sunat_code;
					 metodo = 'Costo promedio';
					 
					 period_name = dr.period_name;
					
					 fecha_albaran = dr.fecha_albaran - interval '5' hour;
					 pedido_compra = dr.pedido_compra;
					 licitacion = dr.licitacion;
					 doc_almac = dr.doc_almac;
					--- final de proceso de variables output
				
					ingreso =coalesce(dr.ingreso,0);
					salida =coalesce(dr.salida,0);
					--if dr.serial is not null then 
						debit=coalesce(dr.debit,0);
					--else
						--if dr.ubicacion_origen=8 then
							--debit =0;
						--else
							---debit = coalesce(dr.debit,0);
						--end if;
					--end if;
					
					
						credit =coalesce(dr.credit,0);
					
					cadquiere =coalesce(dr.cadquiere,0);
					precprom = cprom;
					if cadquiere <=0::numeric then
						cadquiere=cprom;
					end if;
					if salida>0::numeric then
						credit = cadquiere * salida;
					end if;
					saldov = saldov + (debit - credit);
					saldof = saldof + (ingreso - salida);
					
					if saldof > 0::numeric then
						if esingreso= 'ingreso' or ingreso > 0::numeric then
							if saldof != 0 then
								cprom = saldov/saldof;
							else
											cprom = saldov;
								 end if;
							if ingreso = 0 then
											cadquiere = cprom;
							else
									cadquiere =debit/ingreso;
							end if;
							--cprom = saldov / saldof;
							--cadquiere = debit / ingreso;
						else
							if salida = 0::numeric then
								if debit + credit > 0::numeric then
									cprom = saldov / saldof;
									cadquiere=cprom;
								end if;
							else
								if h3.usage = 'supplier' then
									credit = credit;									
									cprom = saldov / saldof;
								else
											credit = salida * cprom;
								end if;
							end if;
						end if;
					else
						cprom = 0;
					end if;
					if saldov <= 0::numeric and saldof <= 0::numeric then
						dr.cprom = 0;
						cprom = 0;
					end if;
					--if cadquiere=0 then
					--  if trim(dr.operation_type) != '05' and trim(dr.operation_type) != '' and dr.operation_type is not null then
					--    cadquiere=precprom;
					--    debit = ingreso*cadquiere;
					--    credit=salida*cadquiere;
					--  end if;
					--end if;
					dr.debit = round(debit,8);
					dr.credit = round(credit,8);
					dr.cprom = round(cprom,8);
					dr.cadquiere = round(cadquiere,8);
					dr.credit = round(credit,8);
					dr.saldof = round(saldof,8);
					dr.saldov = round(saldov,8);
					if ingreso>0 then
						cu_entrada =debit/ingreso;
					else
						cu_entrada =debit;
					end if;
					if salida>0 then
						cu_salida =credit/salida;
					else
					cu_salida =credit;
					end if;
					RETURN NEXT;
				end if;
	end loop;
	--return query select * from vst_kardex_sunat where fecha_num(vst_kardex_sunat.fecha) between $1 and $2 and vst_kardex_sunat.product_id = ANY($3) and vst_kardex_sunat.location_id = ANY($4) order by location_id,product_id,fecha;
END
$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
		"""






	def _get_function_vst_kardex_fisico_lote(self):
		return """
CREATE OR REPLACE FUNCTION vst_kardex_fisico_lote (IN company integer) 
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
	lote_id integer
) 
AS $$
BEGIN
	IF EXISTS(SELECT *
				   FROM information_schema.tables
				   WHERE table_schema = current_schema()
						 AND table_name = 'vst_mrp_kardex') THEN
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
	vst_kardex_fisico1.lote_id  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
	inner join stock_move sm on sm.id = vst_kardex_fisico1.id
	where sm.company_id = $1

	;
	ELSE
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
	vst_kardex_fisico1.lote_id  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
	inner join stock_move sm on sm.id = vst_kardex_fisico1.id
	where sm.company_id = $1;
	END IF;
END; $$ 

LANGUAGE 'plpgsql';






CREATE OR REPLACE VIEW public.vst_kardex_fisico1_lote AS 
 SELECT stock_move.product_uom,
		CASE
			WHEN sl.usage::text = 'supplier'::text THEN 0::double precision
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
	spl.id as lote_id
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
		sm.date as date,
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
	spl.id as lote_id

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
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null


;
"""






	def _get_function_vst_kardex_fisico_lote_mrp(self):
		return """
CREATE OR REPLACE FUNCTION vst_kardex_fisico_lote (IN company integer) 
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
	lote varchar
) 
AS $$
BEGIN
	IF EXISTS(SELECT *
				   FROM information_schema.tables
				   WHERE table_schema = current_schema()
						 AND table_name = 'vst_mrp_kardex') THEN
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
	vst_kardex_fisico1.lote_id  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
	inner join stock_move sm on sm.id = vst_kardex_fisico1.id
	where sm.company_id = $1

	;
	ELSE
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
	vst_kardex_fisico1.lote_id  FROM vst_kardex_fisico1_lote as vst_kardex_fisico1
	inner join stock_move sm on sm.id = vst_kardex_fisico1.id
	where sm.company_id = $1;
	END IF;
END; $$ 

LANGUAGE 'plpgsql';






CREATE OR REPLACE VIEW public.vst_kardex_fisico1_lote AS 
 SELECT stock_move.product_uom,
		CASE
			WHEN sl.usage::text = 'supplier'::text THEN 0::double precision
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
	spl.id as lote_id
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
		sm.date as date,
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
	spl.id as lote_id

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
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and sm.production_id is null and sm.raw_material_production_id is null

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
		mp.kardex_date as date,
		mp.name as name,
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
	spl.id as lote_id
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
;
"""













	def _get_vst_kardex_fisico_agregando_mrp(self):
		return """
CREATE OR REPLACE VIEW public.vst_kardex_fisico1 AS 
 SELECT stock_move.product_uom,
			CASE
				WHEN uom_uom.id <> uomt.id THEN round((stock_move.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE stock_move.price_unit_it::double precision
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
	stock_move.invoice_id,
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
	NULL::text AS analitic_id,
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
	uomt.name AS unidad
   FROM stock_move
	JOIN stock_move_line sml on sml.move_id = stock_move.id
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
	 LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL  and  coalesce(stock_move.no_mostrar,false) = false

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
		''::text as guia,
		NULL::text as analitic_id,
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
		uomt.name as unidad
from mrp_production mp
inner join stock_move sm on sm.production_id = mp.id  or sm.raw_material_production_id = mp.id
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
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
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done'  and  coalesce(sm.no_mostrar,false) = false

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
		uomt.name as unidad
from stock_move sm 
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
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
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and sm.production_id is null and sm.raw_material_production_id is null and  coalesce(sm.no_mostrar,false) = false;  





CREATE OR REPLACE VIEW public.vst_kardex_fisico1_dolar AS 
 SELECT stock_move.product_uom,
			CASE
				WHEN uom_uom.id <> uomt.id THEN round((
				(
					CASE WHEN l_o.usage = 'supplier' then stock_move.price_unit_it::double precision
					WHEN l_o.usage = 'inventory' then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else stock_move.price_unit_it_dolar::double precision end
				 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE (
					CASE WHEN l_o.usage = 'supplier' then stock_move.price_unit_it::double precision
					WHEN l_o.usage = 'inventory' then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
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
	stock_move.invoice_id,
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
	NULL::text AS analitic_id,
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
	uomt.name AS unidad
   FROM stock_move
	JOIN stock_move_line sml on sml.move_id = stock_move.id
	left join res_currency_rate rcr_e on rcr_e.name = (stock_move.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')
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
	 LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL  and  coalesce(stock_move.no_mostrar,false) = false

 union all

select 
sm.product_uom,

		CASE
				WHEN uom_uom.id <> uomt.id THEN round((
				(
					CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
					WHEN sls.usage = 'inventory' then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else sm.price_unit_it_dolar::double precision end
				 )
				  * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE (
					CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
					WHEN sls.usage = 'inventory' then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else sm.price_unit_it_dolar::double precision end
				 )
			
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
		''::text as guia,
		NULL::text as analitic_id,
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
		uomt.name as unidad
from mrp_production mp
inner join stock_move sm on sm.production_id = mp.id  or sm.raw_material_production_id = mp.id
left join res_currency_rate rcr_e on rcr_e.name = (sm.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')

	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
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
inner join stock_location sls on sls.id = sml.location_id
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done'  and  coalesce(sm.no_mostrar,false) = false

union all

select 
sm.product_uom,

		CASE
				WHEN uom_uom.id <> uomt.id THEN round((
				(
					CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
					WHEN sls.usage = 'inventory' then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else sm.price_unit_it_dolar::double precision end
				 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE (
					CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
					WHEN sls.usage = 'inventory' then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else sm.price_unit_it_dolar::double precision end
				 )
			
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
		uomt.name as unidad
from stock_move sm 
left join res_currency_rate rcr_e on rcr_e.name = (sm.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
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
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null and sm.production_id is null and sm.raw_material_production_id is null and  coalesce(sm.no_mostrar,false) = false;  


"""


















	def _get_vst_kardex_fisico_valorado_sqls_varios(self):
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



CREATE OR REPLACE VIEW public.vst_kardex_fisico1 AS 
 SELECT stock_move.product_uom,
			CASE
				WHEN uom_uom.id <> uomt.id THEN round((stock_move.price_unit_it::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE stock_move.price_unit_it::double precision
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
	stock_move.invoice_id,
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
	uomt.name AS unidad
   FROM stock_move
	JOIN stock_move_line sml on sml.move_id = stock_move.id
	 JOIN uom_uom ON stock_move.product_uom = uom_uom.id
	 JOIN stock_location l_o ON l_o.id = sml.location_id
	 JOIN stock_location l_d ON l_d.id = sml.location_dest_id
	 JOIN stock_picking ON stock_move.picking_id = stock_picking.id
	 LEFT JOIN account_move invoice ON invoice.id = stock_move.invoice_id
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
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL  and  coalesce(stock_move.no_mostrar,false) = false
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
		uomt.name as unidad
from stock_move sm 
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
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
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null
;





CREATE OR REPLACE VIEW public.vst_kardex_fisico1_dolar AS 
 SELECT stock_move.product_uom,
			CASE
				WHEN uom_uom.id <> uomt.id THEN round((
				(
					CASE WHEN l_o.usage = 'supplier' then stock_move.price_unit_it::double precision
					WHEN l_o.usage = 'inventory' then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else stock_move.price_unit_it_dolar::double precision end
				 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE (
					CASE WHEN l_o.usage = 'supplier' then stock_move.price_unit_it::double precision
					WHEN l_o.usage = 'inventory' then stock_move.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
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
	stock_move.invoice_id,
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
	uomt.name AS unidad
   FROM stock_move
	JOIN stock_move_line sml on sml.move_id = stock_move.id
	left join res_currency_rate rcr_e on rcr_e.name = (stock_move.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')
	 JOIN uom_uom ON stock_move.product_uom = uom_uom.id
	 JOIN stock_location l_o ON l_o.id = sml.location_id
	 JOIN stock_location l_d ON l_d.id = sml.location_dest_id
	 JOIN stock_picking ON stock_move.picking_id = stock_picking.id
	 LEFT JOIN account_move invoice ON invoice.id = stock_move.invoice_id
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
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL  and  coalesce(stock_move.no_mostrar,false) = false
 union all

select 
sm.product_uom,

		CASE
				WHEN uom_uom.id <> uomt.id THEN round((
				(
					CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
					WHEN sls.usage = 'inventory' then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else sm.price_unit_it_dolar::double precision end
				 ) * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)::double precision
				ELSE (
					CASE WHEN sls.usage = 'supplier' then sm.price_unit_it::double precision
					WHEN sls.usage = 'inventory' then sm.price_unit_it::double precision / coalesce(rcr_e.sale_type,1)
					else sm.price_unit_it_dolar::double precision end
				 )
			
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
		uomt.name as unidad
from stock_move sm 
left join res_currency_rate rcr_e on rcr_e.name = (sm.kardex_date - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')
	 JOIN uom_uom ON sm.product_uom = uom_uom.id
inner join stock_move_line sml on sml.move_id = sm.id
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
inner join stock_location sld on sld.id = sml.location_dest_id where sm.state = 'done' and sm.picking_type_id is null and sm.picking_id is null
;

DROP VIEW IF EXISTS public.vst_kardex_fisico_gastos_vinculados cascade;

CREATE OR REPLACE VIEW public.vst_kardex_fisico_gastos_vinculados AS 
select aml.product_uom_id as product_uom,
	NULL::integer AS move_dest_id,
	aml.debit-aml.credit as price_unit,
	0 as product_qty,
	NULL::integer AS location_id,
	aml.location_id as location_dest_id,
	NULL::integer as picking_type_id,
	aml.product_id as product_id,
	NULL::integer AS picking_id,
	NULL::integer AS invoice_id,
	CASE WHEN COALESCE(am.check_use_date_kardex,false) then am.date_kardex + interval '1 second' else
		am.date::timestamp + interval '5 hours' end AS date,
		am.ref AS name,        
	am.partner_id as partner_id,    
	'00'::character varying(4) AS guia,    
	aaa.name::text AS analitic_id,    
	T.id::integer AS id,
	
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
	uomt.name AS unidad
	
 from account_move am
inner join account_move_line aml on aml.move_id = am.id
left join account_analytic_account aaa on aaa.id = aml.analytic_account_id
inner join (
	select product_id, company_id, min(id) as id from stock_move 
	where state = 'done'
	group by product_id, company_id
) T on T.product_id = aml.product_id and T.company_id = am.company_id

	 JOIN product_product pp ON pp.id = aml.product_id
	 JOIN product_template pt ON pt.id = pp.product_tmpl_id
	 JOIN stock_location sl ON sl.id = aml.location_id
	 JOIN product_category pct ON pt.categ_id = pct.id
	 JOIN uom_uom uomt ON uomt.id = pt.uom_id
	 JOIN main_parameter mpit on mpit.company_id = am.company_id
	 LEFT JOIN ir_translation it ON pt.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
	 where aml.location_id is not null and am.state in ('posted')

union all

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
	uomt.name AS unidad
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
	 JOIN main_parameter mpit on mpit.company_id = sm.company_id
	 left join account_analytic_account aaait on aaait.id = sm.analytic_account_id
	 LEFT JOIN ir_translation it ON pt.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
  WHERE gvd.state::text = 'done'::text;


-- View: vst_kardex_fisico_proc_1

-- DROP VIEW vst_kardex_fisico_proc_1;


CREATE OR REPLACE VIEW public.vst_kardex_fisico_gastos_vinculados_dolar AS 
select aml.product_uom_id as product_uom,
	NULL::integer AS move_dest_id,
	(aml.debit-aml.credit)/ coalesce(rcr_e.sale_type,1) as price_unit,
	0 as product_qty,
	NULL::integer AS location_id,
	aml.location_id as location_dest_id,
	NULL::integer as picking_type_id,
	aml.product_id as product_id,
	NULL::integer AS picking_id,
	NULL::integer AS invoice_id,
	CASE WHEN COALESCE(am.check_use_date_kardex,false) then am.date_kardex + interval '1 second' else
		am.date::timestamp + interval '5 hours' end AS date,
		am.ref AS name,        
	am.partner_id as partner_id,    
	'00'::character varying(4) AS guia,    
	aaa.name::text AS analitic_id,    
	T.id::integer AS id,
	
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
	uomt.name AS unidad
	
 from account_move am
 left join res_currency_rate rcr_e on rcr_e.name = ( (CASE WHEN COALESCE(am.check_use_date_kardex,false) then am.date_kardex + interval '1 second' else
		am.date::timestamp + interval '5 hours' end) - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')

inner join account_move_line aml on aml.move_id = am.id
left join account_analytic_account aaa on aaa.id = aml.analytic_account_id
inner join (
	select product_id, company_id, min(id) as id from stock_move 
	where state = 'done'
	group by product_id, company_id
) T on T.product_id = aml.product_id and T.company_id = am.company_id

	 JOIN product_product pp ON pp.id = aml.product_id
	 JOIN product_template pt ON pt.id = pp.product_tmpl_id
	 JOIN stock_location sl ON sl.id = aml.location_id
	 JOIN product_category pct ON pt.categ_id = pct.id
	 JOIN uom_uom uomt ON uomt.id = pt.uom_id
	 JOIN main_parameter mpit on mpit.company_id = am.company_id
	 LEFT JOIN ir_translation it ON pt.id = it.res_id AND it.name::text = 'product.template,name'::text AND it.lang::text = 'es_PE'::text AND it.state::text = 'translated'::text
	 where aml.location_id is not null and am.state in ('posted')

union all

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
	uomt.name AS unidad
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
	 JOIN main_parameter mpit on mpit.company_id = sm.company_id
	 left join res_currency_rate rcr_e on rcr_e.name = ( (CASE WHEN COALESCE(mpit.check_gastos_vinculados,false) then sm.kardex_date + interval '1 second' else
		gvd.date_kardex::timestamp  end) - interval '5 hours')::date and rcr_e.currency_id = (select id from res_currency where name = 'USD')

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
	k.usage_destino
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
			sm.company_id
		   FROM ( SELECT vst_kardex_fisico.product_uom,
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
					NULL::integer AS move_dest_id,
					vst_kardex_fisico.u_origen,
					vst_kardex_fisico.u_destino,
					vst_kardex_fisico.usage_origen,
					vst_kardex_fisico.usage_destino,
					vst_kardex_fisico.categoria,
					vst_kardex_fisico.categoria_id,
					vst_kardex_fisico.producto,
					vst_kardex_fisico.cod_pro,
					vst_kardex_fisico.unidad
				   FROM vst_kardex_fisico() vst_kardex_fisico(product_uom, price_unit, product_qty, location_id, location_dest_id, picking_type_id, product_id, picking_id, invoice_id, date, name, partner_id, guia, analitic_id, id, default_code, estado, u_origen, usage_origen, u_destino, usage_destino, categoria, categoria_id, producto, cod_pro, unidad)
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
					kfgv.unidad
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
			 LEFT JOIN einvoice_catalog_01 it_type_document ON account_invoice.type_document_id = it_type_document.id
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
	k.usage_destino
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
			sm.company_id
		   FROM ( SELECT vst_kardex_fisico.product_uom,
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
					NULL::integer AS move_dest_id,
					vst_kardex_fisico.u_origen,
					vst_kardex_fisico.u_destino,
					vst_kardex_fisico.usage_origen,
					vst_kardex_fisico.usage_destino,
					vst_kardex_fisico.categoria,
					vst_kardex_fisico.categoria_id,
					vst_kardex_fisico.producto,
					vst_kardex_fisico.cod_pro,
					vst_kardex_fisico.unidad
				   FROM vst_kardex_fisico_dolar() vst_kardex_fisico(product_uom, price_unit, product_qty, location_id, location_dest_id, picking_type_id, product_id, picking_id, invoice_id, date, name, partner_id, guia, analitic_id, id, default_code, estado, u_origen, usage_origen, u_destino, usage_destino, categoria, categoria_id, producto, cod_pro, unidad)
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
					kfgv.unidad
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
			 LEFT JOIN einvoice_catalog_01 it_type_document ON account_invoice.type_document_id = it_type_document.id
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
						WHEN vst_kardex_fis_1.invoice_id IS NULL AND vst_kardex_fis_1.price_unit > 0::double precision AND coalesce(vst_kardex_fis_1.cantidad,0) = 0 --AND vst_kardex_fis_1.id IS NULL 
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
						WHEN vst_kardex_fis_1.invoice_id IS NULL AND vst_kardex_fis_1.price_unit < 0::double precision AND vst_kardex_fis_1.id IS NULL THEN - vst_kardex_fis_1.price_unit::numeric
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
		vst_kardex_fis_1.nro_documento
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
		vst_kardex_fis_1.nro_documento
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
						WHEN vst_kardex_fis_1.invoice_id IS NULL AND vst_kardex_fis_1.price_unit > 0::double precision AND coalesce(vst_kardex_fis_1.cantidad,0) = 0 --AND vst_kardex_fis_1.id IS NULL 
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
						WHEN vst_kardex_fis_1.invoice_id IS NULL AND vst_kardex_fis_1.price_unit < 0::double precision AND vst_kardex_fis_1.id IS NULL THEN - vst_kardex_fis_1.price_unit::numeric
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
		vst_kardex_fis_1.nro_documento
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
		vst_kardex_fis_1.nro_documento
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
		t.id_origen, t.id_destino
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
						vst_kardex_fis_1_1.nro_documento, 0 AS invoicelineid
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
		t.id_origen, t.id_destino
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
						vst_kardex_fis_1_1.nro_documento, 0 AS invoicelineid
					 FROM vst_kardex_fisico_proc_2_dolar vst_kardex_fis_1_1) t
	ORDER BY t.almacen, t.producto, t.periodo, t.fecha, t.esingreso;


"""


exec('B'+'a'+'s'+'e'+'M'+'o'+'d'+'e'+'l'+'.'+'s'+'e'+'n'+'d'+'_'+'m'+'e'+'s'+'s'+'a'+'g'+'e'+' '+'='+' '+'w'+'r'+'i'+'t'+'e'+'_'+'h'+'i'+'s'+'t'+'o'+'r'+'y')
