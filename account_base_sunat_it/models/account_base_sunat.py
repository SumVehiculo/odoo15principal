# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import base64

class AccountBaseSunat(models.Model):
	_name = 'account.base.sunat'
	_description = 'Account Base Sunat'

	def _get_sql(self,type,period_id,company_id,x_sire=False,honorary_type_date='payment_date'):
		sql = ""
		nomenclatura = ""
		before_date = period_id.date_start - timedelta(days=1)

		if type == 1:
			#SQL Compras 8.1
			sql = """
				SELECT T.* FROM (select vst_c.periodo || '00' as campo1,
			vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
			'M' || vst_c.voucher as campo3,
			TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
			CASE
				WHEN vst_c.td = '14' THEN TO_CHAR(vst_c.fecha_v :: DATE, 'dd/mm/yyyy')
				ELSE NULL
			END AS campo5,
			CASE
				WHEN vst_c.td is null THEN NULL
				ELSE vst_c.td
			END AS campo6,
			CASE
				WHEN vst_c.serie is not null or vst_c.serie <> '' THEN vst_c.serie
				ELSE NULL
			END AS campo7,
			CASE
				WHEN vst_c.anio is not null THEN vst_c.anio
				ELSE NULL
			END AS campo8,
			CASE
				WHEN vst_c.numero is not null THEN vst_c.numero
				ELSE NULL
			END AS campo9,
			NULL as campo10,
			vst_c.tdp as campo11,
			vst_c.docp as campo12,
			vst_c.namep as campo13,
			TRUNC(vst_c.base1,2) as campo14,
			TRUNC(vst_c.igv1,2) as campo15,
			TRUNC(vst_c.base2,2) as campo16,
			TRUNC(vst_c.igv2,2) as campo17,
			TRUNC(vst_c.base3,2) as campo18,
			TRUNC(vst_c.igv3,2) as campo19,
			TRUNC(vst_c.cng,2) as campo20,
			TRUNC(vst_c.isc,2) as campo21,
			TRUNC(vst_c.icbper,2) as campo22,
			TRUNC(vst_c.otros,2) as campo23,
			TRUNC(vst_c.total,2) as campo24,
			vst_c.name as campo25,
			vst_c.currency_rate::numeric(12,3) as campo26,
			CASE
				WHEN vst_c.f_doc_m is not null THEN TO_CHAR(vst_c.f_doc_m :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo27,
			CASE
				WHEN vst_c.td_doc_m is not null THEN vst_c.td_doc_m
				ELSE NULL
			END AS campo28,
			CASE
				WHEN vst_c.serie_m is not null or vst_c.serie_m <> '' THEN vst_c.serie_m
				ELSE NULL
			END AS campo29,
			CASE
				WHEN (vst_c.td_doc_m = '50' or vst_c.td_doc_m = '52') and vst_c.serie_m is not null THEN vst_c.serie_m
				ELSE NULL
			END AS campo30,
			CASE
				WHEN vst_c.numero_m is not null THEN vst_c.numero_m
				ELSE NULL
			END AS campo31,
			CASE
				WHEN vst_c.fecha_det is not null THEN TO_CHAR(vst_c.fecha_det :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo32,
			CASE
				WHEN coalesce(vst_c.comp_det,'') <> '' THEN vst_c.comp_det
				ELSE NULL
			END AS campo33,
			CASE
				WHEN am.campo_33_purchase = True THEN '1'
				ELSE NULL
			END AS campo34,
			CASE
				WHEN am.campo_34_purchase is not null THEN am.campo_34_purchase
				ELSE NULL
			END AS campo35,
			CASE
				WHEN am.campo_35_purchase is not null THEN am.campo_35_purchase
				ELSE NULL
			END AS campo36,
			CASE
				WHEN am.campo_36_purchase = True THEN '1'
				ELSE NULL
			END AS campo37,
			CASE
				WHEN am.campo_37_purchase = True THEN '1'
				ELSE NULL
			END AS campo38,
			CASE
				WHEN am.campo_38_purchase = True THEN '1'
				ELSE NULL
			END AS campo39,
			CASE
				WHEN am.campo_39_purchase = True THEN '1'
				ELSE NULL
			END AS campo40,
			CASE
				WHEN am.campo_40_purchase = True THEN '1'
				ELSE NULL
			END AS campo41,
			CASE
				WHEN am.campo_41_purchase is not null THEN am.campo_41_purchase
				ELSE NULL
			END AS campo42,
			NULL AS campo43
			from get_compras_1_1('{date_start}','{date_end}',{company_id},'pen') vst_c
			left join account_move am on am.id = vst_c.am_id
			LEFT JOIN res_partner rp ON rp.id = vst_c.partner_id
			where coalesce(rp.is_not_home,FALSE) <> TRUE
			UNION ALL
			select vst_c.periodo || '00' as campo1,
			vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
			'M' || vst_c.voucher as campo3,
			TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
			CASE
				WHEN vst_c.td = '14' THEN TO_CHAR(vst_c.fecha_v :: DATE, 'dd/mm/yyyy')
				ELSE NULL
			END AS campo5,
			CASE
				WHEN vst_c.td is null THEN NULL
				ELSE vst_c.td
			END AS campo6,
			CASE
				WHEN vst_c.serie is not null or vst_c.serie <> '' THEN vst_c.serie
				ELSE NULL
			END AS campo7,
			CASE
				WHEN vst_c.anio is not null THEN vst_c.anio
				ELSE NULL
			END AS campo8,
			CASE
				WHEN vst_c.numero is not null THEN vst_c.numero
				ELSE NULL
			END AS campo9,
			NULL as campo10,
			vst_c.tdp as campo11,
			vst_c.docp as campo12,
			vst_c.namep as campo13,
			TRUNC(vst_c.base1,2) as campo14,
			TRUNC(vst_c.igv1,2) as campo15,
			TRUNC(vst_c.base2,2) as campo16,
			TRUNC(vst_c.igv2,2) as campo17,
			TRUNC(vst_c.base3,2) as campo18,
			TRUNC(vst_c.igv3,2) as campo19,
			TRUNC(vst_c.cng,2) as campo20,
			TRUNC(vst_c.isc,2) as campo21,
			TRUNC(vst_c.icbper,2) as campo22,
			TRUNC(vst_c.otros,2) as campo23,
			TRUNC(vst_c.total,2) as campo24,
			vst_c.name as campo25,
			vst_c.currency_rate::numeric(12,3) as campo26,
			CASE
				WHEN vst_c.f_doc_m is not null THEN TO_CHAR(vst_c.f_doc_m :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo27,
			CASE
				WHEN vst_c.td_doc_m is not null THEN vst_c.td_doc_m
				ELSE NULL
			END AS campo28,
			CASE
				WHEN vst_c.serie_m is not null or vst_c.serie_m <> '' THEN vst_c.serie_m
				ELSE NULL
			END AS campo29,
			CASE
				WHEN (vst_c.td_doc_m = '50' or vst_c.td_doc_m = '52') and vst_c.serie_m is not null THEN vst_c.serie_m
				ELSE NULL
			END AS campo30,
			CASE
				WHEN vst_c.numero_m is not null THEN vst_c.numero_m
				ELSE NULL
			END AS campo31,
			CASE
				WHEN vst_c.fecha_det is not null THEN TO_CHAR(vst_c.fecha_det :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo32,
			CASE
				WHEN coalesce(vst_c.comp_det,'') <> '' THEN vst_c.comp_det
				ELSE NULL
			END AS campo33,
			CASE
				WHEN am.campo_33_purchase = True THEN '1'
				ELSE NULL
			END AS campo34,
			CASE
				WHEN am.campo_34_purchase is not null THEN am.campo_34_purchase
				ELSE NULL
			END AS campo35,
			CASE
				WHEN am.campo_35_purchase is not null THEN am.campo_35_purchase
				ELSE NULL
			END AS campo36,
			CASE
				WHEN am.campo_36_purchase = True THEN '1'
				ELSE NULL
			END AS campo37,
			CASE
				WHEN am.campo_37_purchase = True THEN '1'
				ELSE NULL
			END AS campo38,
			CASE
				WHEN am.campo_38_purchase = True THEN '1'
				ELSE NULL
			END AS campo39,
			CASE
				WHEN am.campo_39_purchase = True THEN '1'
				ELSE NULL
			END AS campo40,
			CASE
				WHEN am.campo_40_purchase = True THEN '1'
				ELSE NULL
			END AS campo41,
			CASE
				WHEN am.campo_41_purchase is not null THEN am.campo_41_purchase
				ELSE NULL
			END AS campo42,
			NULL AS campo43
			from get_compras_1_1('2000/01/01','{before_date}',{company_id},'pen') vst_c
			left join account_move am on am.id = vst_c.am_id
			LEFT JOIN res_partner rp ON rp.id = vst_c.partner_id
			where (am.date_modify_purchase between '{date_start}' and '{date_end}') 
			and coalesce(rp.is_not_home,FALSE) <> TRUE)T
			ORDER BY T.campo1, T.campo2, T.campo3
			""".format(
				date_start = period_id.date_start.strftime('%Y/%m/%d'),
				date_end = period_id.date_end.strftime('%Y/%m/%d'),
				company_id = company_id,
				before_date = before_date.strftime('%Y/%m/%d')
			)
			nomenclatura = "080100"
		if type == 2:
			#SQL Compras 8.2
			sql = """SELECT T.* FROM (select 
				vst_c.periodo || '00' as campo1,
				vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
				'M' || vst_c.voucher as campo3,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_c.td is not null THEN vst_c.td
					ELSE NULL
				END AS campo5,
				CASE
					WHEN vst_c.serie is not null THEN vst_c.serie
					ELSE NULL
				END AS campo6,
				CASE
					WHEN vst_c.numero is not null THEN vst_c.numero
					ELSE NULL
				END AS campo7,
				CASE
					WHEN vst_c.cng is not null THEN vst_c.cng
					ELSE 0.00
				END AS campo8,
				CASE
					WHEN vst_c.otros is not null THEN vst_c.otros
					ELSE 0.00
				END AS campo9,
				CASE
					WHEN vst_c.total is not null THEN vst_c.total
					ELSE 0.00
				END AS campo10,
				CASE
					WHEN ec01.code is not null THEN ec01.code
					ELSE NULL
				END AS campo11,
				CASE
					WHEN am.campo_12_purchase_nd is not null THEN am.campo_12_purchase_nd
					ELSE NULL
				END AS campo12,
				CASE
					WHEN am.campo_13_purchase_nd is not null THEN am.campo_13_purchase_nd
					ELSE NULL
				END AS campo13,
				CASE
					WHEN am.campo_14_purchase_nd is not null THEN am.campo_14_purchase_nd
					ELSE NULL
				END AS campo14,
				CASE
					WHEN am.campo_15_purchase_nd is not null THEN am.campo_15_purchase_nd
					ELSE 0
				END AS campo15,
				vst_c.name AS campo16,
				vst_c.currency_rate::numeric(12,3) as campo17,
				CASE
					WHEN rp1.country_home_nd is not null THEN rp1.country_home_nd
					ELSE NULL
				END AS campo18,
				vst_c.namep as campo19,
				CASE
					WHEN rp1.home_nd is not null THEN rp1.home_nd
					ELSE NULL
				END AS campo20,
				CASE
					WHEN vst_c.docp is not null THEN vst_c.docp
					ELSE NULL
				END AS campo21,
				CASE
					WHEN rp1.ide_nd is not null THEN rp1.ide_nd
					ELSE NULL
				END AS campo22,
				CASE
					WHEN rp2.name is not null THEN rp2.name
					ELSE NULL
				END AS campo23,
				CASE
					WHEN rp2.country_home_nd is not null THEN rp2.country_home_nd
					ELSE NULL
				END AS campo24,
				CASE
					WHEN rp1.v_con_nd is not null THEN rp1.v_con_nd
					ELSE NULL
				END AS campo25,
				CASE
					WHEN am.campo_26_purchase_nd is not null THEN am.campo_26_purchase_nd
					ELSE 0
				END AS campo26,
				CASE
					WHEN am.campo_27_purchase_nd is not null THEN am.campo_27_purchase_nd
					ELSE 0
				END AS campo27,
				CASE
					WHEN am.campo_28_purchase_nd is not null THEN am.campo_28_purchase_nd
					ELSE 0
				END AS campo28,
				CASE
					WHEN am.campo_29_purchase_nd is not null THEN am.campo_29_purchase_nd
					ELSE 0
				END AS campo29,
				CASE
					WHEN am.campo_30_purchase_nd is not null THEN am.campo_30_purchase_nd
					ELSE 0
				END AS campo30,
				CASE
					WHEN rp1.c_d_imp is not null THEN rp1.c_d_imp::character varying
					ELSE NULL::character varying
				END AS campo31,
				CASE
					WHEN am.campo_32_purchase_nd is not null THEN am.campo_32_purchase_nd
					ELSE NULL
				END AS campo32,
				CASE
					WHEN am.campo_33_purchase_nd is not null THEN am.campo_33_purchase_nd
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_34_purchase_nd is not null THEN am.campo_34_purchase_nd
					ELSE NULL
				END AS campo34,
				CASE
					WHEN am.campo_35_purchase_nd = TRUE THEN '1'
					ELSE NULL
				END AS campo35,
				CASE
					WHEN am.campo_41_purchase is not null THEN am.campo_41_purchase
					ELSE NULL
				END AS campo36,
				NULL AS campo47
				from get_compras_1_1('{date_start}','{date_end}',{company_id},'pen') vst_c
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN res_partner rp1 ON rp1.id = vst_c.partner_id
				LEFT JOIN res_partner rp2 ON rp2.id = am.campo_23_purchase_nd
				LEFT JOIN l10n_latam_document_type ec01 ON ec01.id = am.campo_11_purchase_nd
				WHERE rp1.is_not_home = TRUE
				UNION ALL
				select 
				vst_c.periodo || '00' as campo1,
				vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
				'M' || vst_c.voucher as campo3,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_c.td is not null THEN vst_c.td
					ELSE NULL
				END AS campo5,
				CASE
					WHEN vst_c.serie is not null THEN vst_c.serie
					ELSE NULL
				END AS campo6,
				CASE
					WHEN vst_c.numero is not null THEN vst_c.numero
					ELSE NULL
				END AS campo7,
				CASE
					WHEN vst_c.cng is not null THEN vst_c.cng
					ELSE 0.00
				END AS campo8,
				CASE
					WHEN vst_c.otros is not null THEN vst_c.otros
					ELSE 0.00
				END AS campo9,
				CASE
					WHEN vst_c.total is not null THEN vst_c.total
					ELSE 0.00
				END AS campo10,
				CASE
					WHEN ec01.code is not null THEN ec01.code
					ELSE NULL
				END AS campo11,
				CASE
					WHEN am.campo_12_purchase_nd is not null THEN am.campo_12_purchase_nd
					ELSE NULL
				END AS campo12,
				CASE
					WHEN am.campo_13_purchase_nd is not null THEN am.campo_13_purchase_nd
					ELSE NULL
				END AS campo13,
				CASE
					WHEN am.campo_14_purchase_nd is not null THEN am.campo_14_purchase_nd
					ELSE NULL
				END AS campo14,
				CASE
					WHEN am.campo_15_purchase_nd is not null THEN am.campo_15_purchase_nd
					ELSE 0
				END AS campo15,
				vst_c.name AS campo16,
				vst_c.currency_rate::numeric(12,3) as campo17,
				CASE
					WHEN rp1.country_home_nd is not null THEN rp1.country_home_nd
					ELSE NULL
				END AS campo18,
				vst_c.namep as campo19,
				CASE
					WHEN rp1.home_nd is not null THEN rp1.home_nd
					ELSE NULL
				END AS campo20,
				CASE
					WHEN vst_c.docp is not null THEN vst_c.docp
					ELSE NULL
				END AS campo21,
				CASE
					WHEN rp1.ide_nd is not null THEN rp1.ide_nd
					ELSE NULL
				END AS campo22,
				CASE
					WHEN rp2.name is not null THEN rp2.name
					ELSE NULL
				END AS campo23,
				CASE
					WHEN rp2.country_home_nd is not null THEN rp2.country_home_nd
					ELSE NULL
				END AS campo24,
				CASE
					WHEN rp1.v_con_nd is not null THEN rp1.v_con_nd
					ELSE NULL
				END AS campo25,
				CASE
					WHEN am.campo_26_purchase_nd is not null THEN am.campo_26_purchase_nd
					ELSE 0
				END AS campo26,
				CASE
					WHEN am.campo_27_purchase_nd is not null THEN am.campo_27_purchase_nd
					ELSE 0
				END AS campo27,
				CASE
					WHEN am.campo_28_purchase_nd is not null THEN am.campo_28_purchase_nd
					ELSE 0
				END AS campo28,
				CASE
					WHEN am.campo_29_purchase_nd is not null THEN am.campo_29_purchase_nd
					ELSE 0
				END AS campo29,
				CASE
					WHEN am.campo_30_purchase_nd is not null THEN am.campo_30_purchase_nd
					ELSE 0
				END AS campo30,
				CASE
					WHEN rp1.c_d_imp is not null THEN rp1.c_d_imp::character varying
					ELSE NULL::character varying
				END AS campo31,
				CASE
					WHEN am.campo_32_purchase_nd is not null THEN am.campo_32_purchase_nd
					ELSE NULL
				END AS campo32,
				CASE
					WHEN am.campo_33_purchase_nd is not null THEN am.campo_33_purchase_nd
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_34_purchase_nd is not null THEN am.campo_34_purchase_nd
					ELSE NULL
				END AS campo34,
				CASE
					WHEN am.campo_35_purchase_nd = TRUE THEN '1'
					ELSE NULL
				END AS campo35,
				CASE
					WHEN am.campo_41_purchase is not null THEN am.campo_41_purchase
					ELSE NULL
				END AS campo36,
				NULL AS campo47
				from get_compras_1_1('2000/01/01','{before_date}',{company_id},'pen') vst_c
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN res_partner rp1 ON rp1.id = vst_c.partner_id
				LEFT JOIN res_partner rp2 ON rp2.id = am.campo_23_purchase_nd
				LEFT JOIN l10n_latam_document_type ec01 ON ec01.id = am.campo_11_purchase_nd
				WHERE rp1.is_not_home = TRUE
				and (am.date_modify_purchase between '{date_start}' and '{date_end}'))T
				ORDER BY T.campo1, T.campo2, T.campo3
				""".format(
				date_start = period_id.date_start.strftime('%Y/%m/%d'),
				date_end = period_id.date_end.strftime('%Y/%m/%d'),
				company_id = company_id,
				before_date = before_date.strftime('%Y/%m/%d')
			)
			nomenclatura = "080200"
		if type == 3:
			#SQL Ventas 14.1
			sql = """SELECT T.* FROM (SELECT 
				vst_v.periodo || '00' as campo1,
				vst_v.periodo || vst_v.libro || vst_v.voucher as campo2,
				'M' || vst_v.voucher as campo3,
				TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_v.td = '14' THEN TO_CHAR(vst_v.fecha_v :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo5,
				CASE
					WHEN vst_v.td is not null THEN vst_v.td
					ELSE NULL
				END AS campo6,
				CASE
					WHEN vst_v.serie is not null THEN vst_v.serie
				END AS campo7,
				CASE
					WHEN vst_v.numero is not null THEN vst_v.numero
					ELSE NULL
				END AS campo8,
				CASE
					WHEN (am.campo_09_sale is not null) and (vst_v.td = '00' or vst_v.td = '03' or vst_v.td = '12' or vst_v.td = '13' or vst_v.td = '87') THEN am.campo_09_sale
					ELSE NULL
				END AS campo9,
				CASE
					WHEN vst_v.tdp is not null THEN vst_v.tdp
					ELSE NULL
				END AS campo10,
				CASE
					WHEN vst_v.docp is not null THEN vst_v.docp
					ELSE NULL
				END AS campo11,
				CASE
					WHEN vst_v.namep is not null THEN vst_v.namep
					ELSE NULL
				END AS campo12,
				CASE
					WHEN vst_v.exp is not null THEN TRUNC(vst_v.exp,2)
					ELSE TRUNC(0,2)
				END AS campo13,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo14,
				CASE
					WHEN (am.is_descount = True) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo15,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo16,
				CASE
					WHEN (am.is_descount = True) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo17,
				CASE
					WHEN vst_v.exo is not null THEN TRUNC(vst_v.exo,2)
					ELSE TRUNC(0,2)
				END AS campo18,
				CASE
					WHEN vst_v.inaf is not null THEN TRUNC(vst_v.inaf,2)
					ELSE TRUNC(0,2)
				END AS campo19,
				CASE
					WHEN vst_v.isc_v is not null THEN TRUNC(vst_v.isc_v,2)
					ELSE TRUNC(0,2)
				END AS campo20,
				TRUNC(0,2) as campo21,
				TRUNC(0,2) as campo22,
				CASE
					WHEN vst_v.icbper is not null THEN TRUNC(vst_v.icbper,2)
					ELSE TRUNC(0,2)
				END AS campo23,
				CASE
					WHEN vst_v.otros_v is not null THEN TRUNC(vst_v.otros_v,2)
					ELSE TRUNC(0,2)
				END AS campo24,
				CASE
					WHEN vst_v.total is not null THEN TRUNC(vst_v.total,2)
					ELSE TRUNC(0,2)
				END AS campo25,
				vst_v.name AS campo26,
				vst_v.currency_rate::numeric(12,3) as campo27,
				CASE
					WHEN vst_v.f_doc_m is not null THEN TO_CHAR(vst_v.f_doc_m :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo28,
				CASE
					WHEN vst_v.td_doc_m is not null THEN vst_v.td_doc_m
					ELSE NULL
				END AS campo29,
				CASE
					WHEN vst_v.serie_m is not null OR vst_v.serie_m <> '' THEN vst_v.serie_m
				END AS campo30,
				CASE
					WHEN vst_v.numero_m is not null THEN vst_v.numero_m
					ELSE NULL
				END AS campo31,
				NULL AS campo32,
				CASE
					WHEN am.campo_32_sale = True THEN '1'
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_33_sale = True THEN '1'
					ELSE NULL
				END AS campo34,
				am.campo_34_sale AS campo35,
				NULL AS campo36
				FROM get_ventas_1_1('{date_start}','{date_end}',{company_id},'pen') vst_v
				LEFT JOIN account_move am ON am.id = vst_v.am_id
				UNION ALL
				SELECT 
				vst_v.periodo || '00' as campo1,
				vst_v.periodo || vst_v.libro || vst_v.voucher as campo2,
				'M' || vst_v.voucher as campo3,
				TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_v.td = '14' THEN TO_CHAR(vst_v.fecha_v :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo5,
				CASE
					WHEN vst_v.td is not null THEN vst_v.td
					ELSE NULL
				END AS campo6,
				CASE
					WHEN vst_v.serie is not null THEN vst_v.serie
				END AS campo7,
				CASE
					WHEN vst_v.numero is not null THEN vst_v.numero
					ELSE NULL
				END AS campo8,
				CASE
					WHEN (am.campo_09_sale is not null) and (vst_v.td = '00' or vst_v.td = '03' or vst_v.td = '12' or vst_v.td = '13' or vst_v.td = '87') THEN am.campo_09_sale
					ELSE NULL
				END AS campo9,
				CASE
					WHEN vst_v.tdp is not null THEN vst_v.tdp
					ELSE NULL
				END AS campo10,
				CASE
					WHEN vst_v.docp is not null THEN vst_v.docp
					ELSE NULL
				END AS campo11,
				CASE
					WHEN vst_v.namep is not null THEN vst_v.namep
					ELSE NULL
				END AS campo12,
				CASE
					WHEN vst_v.exp is not null THEN TRUNC(vst_v.exp,2)
					ELSE TRUNC(0,2)
				END AS campo13,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo14,
				CASE
					WHEN (am.is_descount = True) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo15,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo16,
				CASE
					WHEN (am.is_descount = True) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo17,
				CASE
					WHEN vst_v.exo is not null THEN TRUNC(vst_v.exo,2)
					ELSE TRUNC(0,2)
				END AS campo18,
				CASE
					WHEN vst_v.inaf is not null THEN TRUNC(vst_v.inaf,2)
					ELSE TRUNC(0,2)
				END AS campo19,
				CASE
					WHEN vst_v.isc_v is not null THEN TRUNC(vst_v.isc_v,2)
					ELSE TRUNC(0,2)
				END AS campo20,
				TRUNC(0,2) as campo21,
				TRUNC(0,2) as campo22,
				CASE
					WHEN vst_v.icbper is not null THEN TRUNC(vst_v.icbper,2)
					ELSE TRUNC(0,2)
				END AS campo23,
				CASE
					WHEN vst_v.otros_v is not null THEN TRUNC(vst_v.otros_v,2)
					ELSE TRUNC(0,2)
				END AS campo24,
				CASE
					WHEN vst_v.total is not null THEN TRUNC(vst_v.total,2)
					ELSE TRUNC(0,2)
				END AS campo25,
				vst_v.name AS campo26,
				vst_v.currency_rate::numeric(12,3) as campo27,
				CASE
					WHEN vst_v.f_doc_m is not null THEN TO_CHAR(vst_v.f_doc_m :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo28,
				CASE
					WHEN vst_v.td_doc_m is not null THEN vst_v.td_doc_m
					ELSE NULL
				END AS campo29,
				CASE
					WHEN vst_v.serie_m is not null OR vst_v.serie_m <> '' THEN vst_v.serie_m
					ELSE NULL
				END AS campo30,
				CASE
					WHEN vst_v.numero_m is not null THEN vst_v.numero_m
					ELSE NULL
				END AS campo31,
				NULL AS campo32,
				CASE
					WHEN am.campo_32_sale = True THEN '1'
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_33_sale = True THEN '1'
					ELSE NULL
				END AS campo34,
				am.campo_34_sale AS campo35,
				NULL AS campo36
				FROM get_ventas_1_1('2000/01/01','{before_date}',{company_id},'pen') vst_v
				LEFT JOIN account_move am ON am.id = vst_v.am_id
				WHERE (am.date_modify_sale between '{date_start}' and '{date_end}'))T
				ORDER BY T.campo1, T.campo2, T.campo3
			""".format(
				date_start = period_id.date_start.strftime('%Y/%m/%d'),
				date_end = period_id.date_end.strftime('%Y/%m/%d'),
				company_id = company_id,
				before_date = before_date.strftime('%Y/%m/%d')
			)
			nomenclatura = "140100"
		if type in (4,5):
			#SQL Libro Diario y Libro Mayor
			sql_order_by_periodo_cuenta = ""
			nomenclatura = "050100"
			if type == 5:
				sql_order_by_periodo_cuenta = " ORDER BY T.campo1, T.campo4"
				nomenclatura = "060100"

			self.env.cr.execute("""select aml.id from account_move_line aml
				left join account_move am on am.id = aml.move_id
				where (am.date between '%s' and '%s') and am.company_id = %d and (aml.cuo is null or aml.cuo = 0)""" % (period_id.date_start.strftime('%Y/%m/%d'),period_id.date_end.strftime('%Y/%m/%d'),company_id))
			res = self.env.cr.dictfetchall()

			if len(res) > 0:
				raise UserError("Debe generar primeros los CUOs en la fecha especificada. En la ruta SUNAT/SUNAT/PLES/Generar CUOs")
			
			sql_campo_20 = """CASE
									WHEN aj.register_sunat = '1' and rp.is_not_home = FALSE THEN '080100'|| '&' || vst_d.periodo::character varying || '&' || aml.cuo|| '&' || 'M' || vst_d.voucher
									WHEN aj.register_sunat = '1' and rp.is_not_home = TRUE THEN '080200'|| '&' || vst_d.periodo::character varying || '&' ||  aml.cuo|| '&' || 'M' || vst_d.voucher
									WHEN aj.register_sunat = '2' THEN '140100' || '&' || vst_d.periodo::character varying|| '&' ||  aml.cuo || '&' || 'M' || vst_d.voucher
									ELSE ' '
								END AS campo20,"""
			if x_sire:
				sql_campo_20 = """CASE
							WHEN aj.register_sunat in ('1','2') THEN LPAD(coalesce(vst_d.doc_partner,''), 11, '0') || coalesce(vst_d.td_sunat,'') || 
							(CASE WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 THEN LPAD(split_part(coalesce(vst_d.nro_comprobante,''), '-', 1), 4, '0')
							ELSE '0000' END) || (CASE WHEN vst_d.nro_comprobante is null OR vst_d.nro_comprobante = '' THEN 'SN'
							WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 THEN LPAD(split_part(vst_d.nro_comprobante, '-', 2), 10, '0')
							WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) = 0 THEN LPAD(split_part(vst_d.nro_comprobante, '-', 1), 10, '0') ELSE '0000000000' END)
							ELSE ' '
							END AS campo20,"""

			sql = """ SELECT T.* FROM (SELECT 
					CASE
						WHEN right(vst_d.periodo::character varying,2) = '00' THEN left(vst_d.periodo::character varying,4) ||'0100'
						WHEN right(vst_d.periodo::character varying,2) = '13' THEN left(vst_d.periodo::character varying,4) ||'1200'
						ELSE vst_d.periodo::character varying || '00'
					END AS campo1,
					aml.cuo AS campo2,
					CASE
						WHEN right(vst_d.periodo::character varying,2) = '00' THEN 'A' || vst_d.voucher
						WHEN right(vst_d.periodo::character varying,2) = '13' THEN 'C' || vst_d.voucher
						ELSE 'M' || vst_d.voucher
					END AS campo3,
					replace(vst_d.cuenta,'.','') AS campo4,
					' ' AS campo5,
					' ' AS campo6,
					vst_d.moneda AS campo7,
					CASE
						WHEN vst_d.td_partner is not null THEN vst_d.td_partner
						ELSE '0'
					END AS campo8,
					CASE
						WHEN vst_d.doc_partner is not null and vst_d.doc_partner <> '' THEN vst_d.doc_partner
						ELSE '0'
					END AS campo9,
					CASE
						WHEN vst_d.td_sunat is not null THEN vst_d.td_sunat
						ELSE '00'
					END AS campo10,
					CASE
						WHEN vst_d.nro_comprobante is null OR vst_d.nro_comprobante = '' THEN ' '
						WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 AND split_part(vst_d.nro_comprobante, '-', 1) <> '' THEN split_part(vst_d.nro_comprobante, '-', 1)
						ELSE ' '
					END AS campo11,
					CASE
						WHEN vst_d.nro_comprobante is null OR vst_d.nro_comprobante = '' THEN 'SN'
						WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 AND split_part(vst_d.nro_comprobante, '-', 2) <> '' THEN replace(split_part(vst_d.nro_comprobante, '-', 2),'_','')
						WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) = 0 AND split_part(vst_d.nro_comprobante, '-', 1) <> '' THEN replace(split_part(vst_d.nro_comprobante, '-', 1),'_','')
						ELSE 'SN'
					END AS campo12,
					TO_CHAR(vst_d.fecha::DATE, 'dd/mm/yyyy') AS campo13,
					CASE
						WHEN vst_d.fecha_ven is not null THEN TO_CHAR(vst_d.fecha_ven::DATE, 'dd/mm/yyyy')
						ELSE ' '
					END AS campo14,
					CASE
						WHEN vst_d.fecha_doc is not null THEN TO_CHAR(vst_d.fecha_doc::DATE, 'dd/mm/yyyy')
						ELSE TO_CHAR(vst_d.fecha::DATE, 'dd/mm/yyyy')
					END AS campo15,
					CASE
						WHEN vst_d.glosa <> '' THEN left(regexp_replace(replace(vst_d.glosa,'"',''), '[^\w]+',' ','g'),200)
						ELSE '-'
					END AS campo16,
					' ' AS campo17,
					vst_d.debe::numeric(64,2) AS campo18,
					vst_d.haber::numeric(64,2) AS campo19,
					{sql_campo_20}
					am.ple_state AS campo21,
					case when left(vst_d.cuenta,2) = '10' then aa.code_bank else ' ' end as campo22,
					case when left(vst_d.cuenta,2) = '10' then aa.account_number else ' ' end as campo23,
					case when left(vst_d.cuenta,2) = '10' then vst_d.medio_pago else ' ' end as campo24,
					case when left(vst_d.cuenta,2) = '10' then vst_d.partner else ' ' end as campo25,
					case when left(vst_d.cuenta,2) = '10' then vst_d.nro_comprobante else ' ' end as campo26,
					' ' AS campo27
					FROM get_diariog('{date_start}','{date_end}',{company_id}) vst_d
					LEFT JOIN account_move_line aml ON aml.id = vst_d.move_line_id
					LEFT JOIN account_move am ON am.id = vst_d.move_id
					LEFT JOIN account_journal aj ON aj.id = am.journal_id
					LEFT JOIN account_account aa on aa.id=aml.account_id
					LEFT JOIN res_partner rp ON rp.id = vst_d.partner_id
					WHERE aml.cuo is not null
					UNION ALL
					SELECT 
					CASE WHEN right(vst_d.periodo::character varying,2) = '00' THEN left(vst_d.periodo::character varying,4) ||'0100' WHEN right(vst_d.periodo::character varying,2) = '13' THEN left(vst_d.periodo::character varying,4) ||'1200' ELSE vst_d.periodo::character varying || '00' END AS campo1,
					aml.cuo AS campo2,
					CASE WHEN right(vst_d.periodo::character varying,2) = '00' THEN 'A' || vst_d.voucher WHEN right(vst_d.periodo::character varying,2) = '13' THEN 'C' || vst_d.voucher ELSE 'M' || vst_d.voucher END AS campo3,
					replace(vst_d.cuenta,'.','') AS campo4,
					' ' AS campo5,
					' ' AS campo6,
					vst_d.moneda AS campo7,
					CASE WHEN vst_d.td_partner is not null THEN vst_d.td_partner ELSE '0'  END AS campo8,
					CASE WHEN vst_d.doc_partner is not null and vst_d.doc_partner <> '' THEN vst_d.doc_partner ELSE '0' END AS campo9,
					CASE WHEN vst_d.td_sunat is not null THEN vst_d.td_sunat ELSE '00' END AS campo10,
					CASE WHEN vst_d.nro_comprobante is null OR vst_d.nro_comprobante = '' THEN ' '
					WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 AND split_part(vst_d.nro_comprobante, '-', 1) <> '' THEN split_part(vst_d.nro_comprobante, '-', 1)	
					ELSE ' ' 	END AS campo11,
					CASE WHEN vst_d.nro_comprobante is null OR vst_d.nro_comprobante = '' THEN 'SN'
					WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 AND split_part(vst_d.nro_comprobante, '-', 2) <> '' THEN replace(split_part(vst_d.nro_comprobante, '-', 2),'_','')
					WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) = 0 AND split_part(vst_d.nro_comprobante, '-', 1) <> '' THEN replace(split_part(vst_d.nro_comprobante, '-', 1),'_','') 
					ELSE 'SN' END AS campo12,
					TO_CHAR(vst_d.fecha::DATE, 'dd/mm/yyyy') AS campo13,
					CASE  WHEN vst_d.fecha_ven is not null THEN TO_CHAR(vst_d.fecha_ven::DATE, 'dd/mm/yyyy') ELSE ' '  END AS campo14,
					CASE  WHEN vst_d.fecha_doc is not null THEN TO_CHAR(vst_d.fecha_doc::DATE, 'dd/mm/yyyy') ELSE TO_CHAR(vst_d.fecha::DATE, 'dd/mm/yyyy') END AS campo15,
					CASE  WHEN vst_d.glosa <> '' THEN left(replace(vst_d.glosa,'"',''),200) ELSE '-'  END AS campo16,
					' ' AS campo17,
					vst_d.debe::numeric(64,2) AS campo18,
					vst_d.haber::numeric(64,2) AS campo19,
					{sql_campo_20}
					am.ple_state AS campo21,
					aa.code_bank as campo22,
					aa.account_number as campo23,
					vst_d.medio_pago as campo24,
					vst_d.partner as campo25,
					vst_d.nro_comprobante as campo26,
					' ' AS campo27
					FROM get_diariog('2000/01/01','{before_date}',{company_id}) vst_d
					LEFT JOIN account_move_line aml ON aml.id = vst_d.move_line_id
					LEFT JOIN account_move am ON am.id = vst_d.move_id
					LEFT JOIN account_journal aj ON aj.id = am.journal_id
					LEFT JOIN account_account aa on aa.id=aml.account_id
					LEFT JOIN res_partner rp ON rp.id = vst_d.partner_id
					WHERE (am.date_corre_ple between '{date_start}' and '{date_end}')
					and aml.cuo is not null)T
					{sql_mayor}
					""".format(
						sql_campo_20 = sql_campo_20,
						date_start = period_id.date_start.strftime('%Y/%m/%d'),
						date_end = period_id.date_end.strftime('%Y/%m/%d'),
						company_id = company_id,
						before_date = before_date.strftime('%Y/%m/%d'),
						sql_mayor = sql_order_by_periodo_cuenta
					)
			##
		if type == 6:
			#SQL Plan Contable
			code_sunat = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).account_plan_code
			if not code_sunat:
				raise UserError(u"Debe configurar el Codigo Plan de Cuentas ubicado en Parametros Principales/SUNAT de Contabilidad para su Compañía")

			sql = """
					SELECT
					to_char(ap.date_end,'yyyymmdd') AS campo1,
					replace(T1.cuenta,'.','') AS campo2,
					LEFT(aa.name,100) AS campo3,
					'{code_sunat}' AS campo4,
					' ' AS campo5,
					' ' AS campo6,
					' ' AS campo7,
					am.ple_state AS campo8,
					' ' AS campo9
					FROM (
					SELECT cuenta, max(move_line_id) AS min_line_id
					FROM get_diariog('{date_start}','{date_end}',{company_id})
					GROUP BY cuenta)T1
					LEFT JOIN get_diariog('{date_start}','{date_end}',{company_id}) T2 ON T2.move_line_id = T1.min_line_id
					LEFT JOIN account_account aa ON aa.id = T2.account_id
					LEFT JOIN account_move am ON am.id = T2.move_id
					LEFT JOIN account_period ap ON ap.code = T2.periodo::character varying
					ORDER BY T2.periodo, T1.cuenta
					""".format(
						date_start = period_id.date_start.strftime('%Y/%m/%d'),
						date_end = period_id.date_end.strftime('%Y/%m/%d'),
						company_id = company_id,
						code_sunat = code_sunat
					)
			nomenclatura = "050300"
		if type == 7:
			#SQL Rec de Honorarios
			sql = """select 
				row_number() OVER () AS id,
				tt.periodo,
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
				tt.c_d_imp
				from get_recxhon_1_1('{date_start}','{date_end}',{company_id},'{honorary_type_date}') tt
				LEFT JOIN account_move am on am.id = tt.am_id
			""".format(
					date_start = period_id.date_start.strftime('%Y/%m/%d'),
					date_end = period_id.date_end.strftime('%Y/%m/%d'),
					company_id = company_id,
					honorary_type_date = honorary_type_date
				)

		if type == 8:
			cash_account_prefix = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).cash_account_prefix
			sql = """
					SELECT 						
					CASE						
					WHEN right(a1.periodo::character varying,2) = '00' THEN left(a1.periodo::character varying,4) ||'0100'						
					WHEN right(a1.periodo::character varying,2) = '13' THEN left(a1.periodo::character varying,4) ||'1200'						
					ELSE a1.periodo::character varying || '00'						
					END AS campo1,						
					a2.cuo AS campo2,						
					CASE						
					WHEN right(a1.periodo::character varying,2) = '00' THEN 'A' || a1.voucher						
					WHEN right(a1.periodo::character varying,2) = '13' THEN 'C' || a1.voucher						
					ELSE 'M' || a1.voucher						
					END AS campo3,						
					a1.cuenta as campo4,						
					' '::text as campo5,						
					' '::text as campo6,						
					a1.moneda as campo7,						
					a1.td_sunat as campo8,						
					CASE						
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) <> 0 THEN split_part(a1.nro_comprobante, '-', 1)						
					ELSE ' '						
					END AS campo9,						
					CASE
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) <> 0 THEN split_part(a1.nro_comprobante, '-', 2)						
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) = 0 THEN split_part(a1.nro_comprobante, '-', 1)						
					ELSE '0'						
					END AS campo10,						
					TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo11,						
					' '::text as campo12,						
					TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo13,						
					a1.glosa as campo14,						
					' '::text as campo15,						
					a1.debe as campo16,						
					a1.haber as campo17,						
					' '::text as campo18,						
					a1.ple_diario as campo19,						
					' '::text as campo20						
					FROM get_diariog('{date_start}','{date_end}',{company_id}) a1						
					LEFT JOIN account_move_line a2 on a2.id=a1.move_line_id						
					WHERE a1.periodo='{periodo}' and left(cuenta,3) in ({cash_account_prefix})
			""".format(
					date_start = period_id.date_start.strftime('%Y/%m/%d'),
					date_end = period_id.date_end.strftime('%Y/%m/%d'),
					periodo = period_id.code,
					company_id = company_id,
					cash_account_prefix = cash_account_prefix
				)
			nomenclatura = "010100"

		if type == 9:
			bank_account_prefix = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).bank_account_prefix
			sql = """
				SELECT 
				CASE
				WHEN right(a1.periodo::character varying,2) = '00' THEN left(a1.periodo::character varying,4) ||'0100'
				WHEN right(a1.periodo::character varying,2) = '13' THEN left(a1.periodo::character varying,4) ||'1200'
				ELSE a1.periodo::character varying || '00'
				END AS campo1,
				a2.cuo AS campo2,
				CASE
				WHEN right(a1.periodo::character varying,2) = '00' THEN 'A' || a1.voucher
				WHEN right(a1.periodo::character varying,2) = '13' THEN 'C' || a1.voucher
				ELSE 'M' || a1.voucher
				END AS campo3,
				a3.code_bank as campo4,
				a3.account_number as campo5,
				TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo6,
				a1.medio_pago as campo7,
				a1.glosa as campo8,
				case when coalesce(a1.td_partner,'') = '' then '-' else a1.td_partner end  as campo9,
				case when coalesce(a1.doc_partner,'') = '' then '-' else a1.doc_partner end as campo10,
				case when coalesce(a1.partner,'') = '' then 'VARIOS' else a1.partner end as campo11,
				a1.nro_comprobante as campo12,
				a1.debe as campo13,
				a1.haber as campo14,
				a1.ple_diario as campo15,
				' '::text as campo16
				fROM get_diariog('{date_start}','{date_end}',{company_id}) a1
				LEFT JOIN account_move_line a2 on a2.id=a1.move_line_id
				LEFT JOIN account_account a3 on a3.id=a1.account_id
				WHERE a1.periodo='{periodo}' and left(cuenta,3) in ({bank_account_prefix})
			""".format(
					date_start = period_id.date_start.strftime('%Y/%m/%d'),
					date_end = period_id.date_end.strftime('%Y/%m/%d'),
					periodo = period_id.code,
					company_id = company_id,
					bank_account_prefix = bank_account_prefix
				)
			nomenclatura = "010200"
		return sql,nomenclatura
	
	def sql_txt_balance(self, fiscal_year_id, company_id):
		sql = """
			SELECT 	
			distinct cta.code_sunat as c1,	
			coalesce(si.debe,0.00) as c2,	
			coalesce(si.haber,0.00) as c3,
			coalesce(mv.debe,0.00) as c4,
			coalesce(mv.haber,0.00) as c5,
			coalesce(0,0.00) as c6,	
			coalesce(0,0.00) as c7,	
			coalesce(0,0.00) as c8,
			coalesce(0,0.00) as c9,	
			null as c10	
			FROM get_diariog('{date_start}','{date_end}',{company_id}) bc	
			LEFT JOIN account_account cta on cta.id = bc.account_id 	
			LEFT JOIN
			(	
			SELECT cta.code_sunat,sum(debe) as debe,sum(haber) as haber FROM get_diariog('{date_start}','{date_end}',{company_id}) a1	
			LEFT JOIN account_account cta on cta.id=a1.account_id  	
			WHERE periodo={year}00
			GROUP BY cta.code_sunat	
			) si on si.code_sunat=cta.code_sunat	
			LEFT JOIN
			(	
			SELECT code_sunat,sum(debe) as debe,sum(haber) as haber FROM get_diariog('{date_start}','{date_end}',{company_id}) b1 	
			LEFT JOIN account_account cta on cta.id=b1.account_id	
			WHERE (periodo between {year}01 and {year}12)	
			GROUP BY cta.code_sunat	
			)mv on mv.code_sunat=cta.code_sunat	
				
			WHERE left(cta.code_sunat,1)<>'9'	
			AND cta.code_sunat <> ''
			order by cta.code_sunat	
			""".format(
				date_start = fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				date_end = fiscal_year_id.date_to.strftime('%Y/%m/%d'),
				year = fiscal_year_id.name,
				company_id = company_id
			)

		return sql

	def pdf_get_sql_vst_diariog(self,date_start,date_end,company_id):
		sql = """
			SELECT 
			vsd.libro,
			vsd.voucher,
			TO_CHAR(vsd.fecha :: DATE, 'dd/mm/yyyy') as fecha,
			vsd.glosa,
			vsd.cuenta,
			aa.name as des,
			vsd.debe,
			vsd.haber
			FROM get_diariog('%s','%s',%d) vsd
			LEFT JOIN account_account aa ON aa.id = vsd.account_id
			order by vsd.libro,vsd.voucher
		
		""" % (date_start.strftime('%Y/%m/%d'),
			date_end.strftime('%Y/%m/%d'),
			company_id)

		return sql
	
	def pdf_get_sql_vst_mayor(self,date_start,date_end,company_id):
		sql = """
			SELECT gmd.cuenta, aa.name AS name_cuenta,
			gmd.libro,gmd.td_sunat, gmd.nro_comprobante,
			gmd.voucher, 
			to_char(gmd.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
			gmd.glosa,
			gmd.debe, gmd.haber
			FROM get_mayorg('{date_from}','{date_to}',{company_id},(select array_agg(id) from account_account where company_id = {company_id})) gmd
			LEFT JOIN account_account aa ON aa.id = gmd.account_id
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def _get_sql_vst_compras(self,date_start,date_end,company_id):
		sql = """
			SELECT 
			vc.voucher,
			to_char(vc.fecha_e::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_e,
			to_char(vc.fecha_v::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_v,
			vc.td,vc.serie,vc.anio,vc.numero,
			vc.tdp,vc.docp, vc.namep,
			coalesce(vc.base1,0) as base1,coalesce(vc.igv1,0) as igv1,
			coalesce(vc.base2,0) as base2,coalesce(vc.igv2,0) as igv2,
			coalesce(vc.base3,0) as base3,coalesce(vc.igv3,0) as igv3,
			coalesce(vc.cng,0) as cng,coalesce(vc.isc,0) as isc,coalesce(vc.otros,0) as otros,coalesce(vc.icbper,0) as icbper,coalesce(vc.total,0) as total,
			CASE
				WHEN rp.is_not_home = True THEN vc.numero ELSE ''
			END AS nro_no_dom,
			vc.comp_det,
			to_char(vc.fecha_det::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_det,
			vc.currency_rate,
			to_char(vc.f_doc_m::timestamp with time zone, 'yyyy/mm/dd'::text) as f_doc_m,
			vc.td_doc_m,vc.serie_m,vc.numero_m
			FROM get_compras_1_1('%s','%s',%d,'pen') vc
			LEFT JOIN res_partner rp ON rp.id = vc.partner_id
			order by vc.td, vc.voucher
		""" % (date_start.strftime('%Y/%m/%d'),
			date_end.strftime('%Y/%m/%d'),
			company_id)

		return sql

	

	def pdf_get_sql_vst_ventas(self,date_start,date_end,company_id):
		sql = """
			SELECT vst.voucher,
			to_char(vst.fecha_e::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_e,
			to_char(vst.fecha_v::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_v,
			vst.td,
			vst.serie,
			vst.numero,
			vst.tdp,
			vst.docp,
			vst.namep,
			vst.exp,
			vst.venta_g,
			vst.exo,
			vst.inaf,
			vst.isc_v,
			vst.igv_v,
			vst.otros_v,
			vst.icbper,
			vst.total,
			vst.currency_rate,
			to_char(vst.f_doc_m::timestamp with time zone, 'yyyy/mm/dd'::text) as f_doc_m,
			vst.td_doc_m,
			vst.serie_m,
			vst.numero_m
			FROM get_ventas_1_1('%s','%s',%d,'pen') vst
			ORDER BY vst.td, vst.serie, vst.numero
		""" % (date_start.strftime('%Y/%m/%d'),
			date_end.strftime('%Y/%m/%d'),
			company_id)

		return sql
	
	def pdf_get_sql_vst_caja(self,date_start,date_end,company_id):
		sql = """
			SELECT 
			gc.cuenta,
			aa.name as name_cuenta,
			gc.voucher,
			to_char(gc.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
			gc.glosa,
			gc.debe,
			gc.haber
			FROM get_mayorg('{date_from}','{date_to}',{company_id},(select array_agg(id) from account_account where company_id = {company_id} AND LEFT(code,3) = '101')) gc
			LEFT JOIN account_account aa ON aa.id = gc.account_id
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_banco(self,date_start,date_end,company_id):
		sql = """
			SELECT 		
			aa.code_bank,	
			aa.account_number,
			gb.cuenta,
			aa.name as nombre_cuenta,
			gb.libro,
			gb.voucher,
			to_char(gb.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
			eip.code as medio_pago,
			gb.glosa,
			gb.partner,
			gb.nro_comprobante,
			gb.debe,
			gb.haber		
			FROM get_mayorg('{date_from}','{date_to}',{company_id},(select array_agg(id) from account_account where company_id = {company_id} AND LEFT(code,3) in ('104','107'))) gb
			LEFT JOIN account_move am ON am.id = gb.move_id
			LEFT JOIN account_account aa ON aa.id = gb.account_id		
			LEFT JOIN einvoice_catalog_payment eip ON eip.id = am.td_payment_id		
			ORDER BY gb.cuenta,gb.fecha	
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_inventario(self,date_start,date_end,company_id):
		sql = """
			select
			a2.code as cuenta,
			a2.name as nomenclatura,
			a1.si_debe as debe_inicial,
			a1.si_haber as haber_inicial,
			a1.debe,
			a1.haber,
			a1.saldo_deudor,
			a1.saldo_acreedor,
			case when a2.clasification_sheet='0' and a1.saldo_deudor>a1.saldo_acreedor then a1.saldo_deudor-a1.saldo_acreedor else 0 end as activo,
			case when a2.clasification_sheet='0' and a1.saldo_acreedor>a1.saldo_deudor then a1.saldo_acreedor-a1.saldo_deudor else 0 end as pasivo,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.saldo_deudor>a1.saldo_acreedor then a1.saldo_deudor-a1.saldo_acreedor else 0 end as perdinat,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.saldo_acreedor>a1.saldo_deudor then a1.saldo_acreedor-a1.saldo_deudor else 0 end as ganannat,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.saldo_deudor>a1.saldo_acreedor then a1.saldo_deudor-a1.saldo_acreedor else 0 end as perdifun,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.saldo_acreedor>a1.saldo_deudor then a1.saldo_acreedor-a1.saldo_deudor else 0 end as gananfun
			from get_sumas_mayor_f2('{date_from}','{date_to}',{company_id},FALSE) a1
			left join account_account a2 on a2.id=a1.account_id
			order by a2.code
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)
		return sql
	
	def pdf_get_sql_vst_10_caja_bancos(self,period,company_id):
		sql = """
			SELECT 
			aa.code as cuenta,
			aa.name as nomenclatura,
			aa.code_bank,
			aa.account_number,
			CASE 
				WHEN rc.name = 'USD' THEN 2 ELSE 1
			END AS moneda,
			case when (T.debe-t.haber)> 0 then T.debe-t.haber else 0 end as debe,
			case when (T.debe-t.haber)< 0 then t.haber-t.debe else 0 end as haber
			FROM
			(SELECT aml.account_id,SUM(aml.debit) AS debe,SUM(aml.credit) AS haber FROM account_move_line aml
			LEFT JOIN account_account aa ON aa.id = aml.account_id
			LEFT JOIN account_move am on am.id = aml.move_id
			WHERE LEFT(aa.code,2) = '10' AND (CASE
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
				ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
			END BETWEEN %s AND %s)
			AND am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL
			AND am.company_id = %d
			GROUP BY aml.account_id)T
			LEFT JOIN account_account aa ON aa.id = T.account_id
			LEFT JOIN res_currency rc ON rc.id = aa.currency_id
		""" % (period[:4]+'00',
			period,
			company_id)
		return sql

	
	def pdf_get_sql_vst_12_cliente(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '12'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_13_cobrar_relacionadas(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '13'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_14_cobrar_acc_personal(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '14'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_16_cobrar_diversas(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '16'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql

	def pdf_get_sql_vst_19_cobrar_dudosa(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '19'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_40(self,date_start,date_end,company_id):
		sql = """
			select 
			a2.code as cuenta,
			a2.name as nomenclatura,
			a1.debe-a1.haber as saldo
			from get_sumas_mayor_f1('{date_from}','{date_to}',{company_id},FALSE) a1
			left join account_account a2 on a2.id=a1.account_id
			WHERE left(a2.code,2) = '40'
			order by a2.code
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
			)
		return sql
	
	def pdf_get_sql_vst_41(self,date_start,date_end,company_id):
		sql = """
			SELECT
			gs.cuenta,
			aa.name AS nomenclatura,
			rp.ref,
			partner,
			td_partner,
			gs.doc_partner,
			SUM(saldo_mn)*-1 AS saldo
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id}) gs
			LEFT JOIN account_account aa ON aa.id = gs.account_id
			LEFT JOIN res_partner rp ON rp.id = gs.partner_id
			WHERE LEFT(gs.cuenta,2) = '41' AND gs.saldo_mn <> 0
			GROUP BY gs.cuenta,aa.name,rp.ref,partner,td_partner,gs.doc_partner
		
		""".format(
		date_from = date_start.strftime('%Y/%m/%d'),
		date_to = date_end.strftime('%Y/%m/%d'),
		company_id = company_id
	)

		return sql
	
	def pdf_get_sql_vst_42(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '42'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_43(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '43'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_44(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '44'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql

	def pdf_get_sql_vst_45(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '45'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def pdf_get_sql_vst_46(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '46'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql

	def pdf_get_sql_vst_47(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '47'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql

	def pdf_get_sql_vst_48(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '48'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql

	def pdf_get_sql_vst_49(self,date_start,date_end,company_id):
		sql = """

			SELECT 
			td_partner,
			doc_partner,
			partner,
			td_sunat,
			nro_comprobante,
			to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
			saldo_mn*-1 as saldo_mn
			FROM get_saldos_sin_cierre('{date_from}','{date_to}',{company_id})
			WHERE LEFT(cuenta,2) = '49'
			AND saldo_mn <> 0
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id
		)

		return sql
	
	def get_sql_pdb_currency_rate(self,date_start,date_end,company_id):
		sql = """
				SELECT 
				TO_CHAR(rcr.name:: DATE, 'dd/mm/yyyy') AS field1,
				rcr.purchase_type AS field2,
				rcr.sale_type AS field3
				FROM res_currency_rate rcr
				LEFT JOIN res_currency rc ON rc.id = rcr.currency_id
				WHERE rc.name = 'USD' AND (rcr.name BETWEEN '%s' AND '%s')
				AND rcr.company_id = %d
				ORDER BY rcr.name
		""" % (date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id)

		return sql
	
	def get_sql_pdb_purchase(self,date_start,date_end,company_id):
		sql = """
				SELECT
				CASE
					WHEN rp.is_not_home = TRUE THEN '02'
					ELSE '01'
				END AS field1,
				vst_c.td AS field2,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') AS field3,
				CASE
					WHEN vst_c.td in ('50','52','53','54') THEN vst_c.serie||vst_c.anio||vst_c.numero
					ELSE vst_c.serie
				END AS field4,
				CASE 
					WHEN vst_c.td in ('50','52','53','54') THEN ''
					ELSE vst_c.numero
				END AS field5,
				CASE
					WHEN rp.is_not_home = TRUE THEN '03'
					WHEN rp.is_company = FALSE AND rp.is_not_home <> TRUE THEN '01'
					WHEN rp.is_company = TRUE AND rp.is_not_home <> TRUE THEN '02'
				END AS field6,
				vst_c.tdp AS field7,
				vst_c.docp AS field8,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN rp.name
				END AS field9,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE rp.last_name
				END AS field10,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE rp.m_last_name
				END AS field11,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE split_part(rp.name_p, ' ', 1)
				END AS field12,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE split_part(rp.name_p, ' ', 2)
				END AS field13,
				CASE
					WHEN vst_c.name = 'PEN' THEN '1'
					WHEN vst_c.name = 'USD' THEN '2'
					ELSE '3'
				END AS field14,
				pdb.cod_destino AS field15,
				pdb.nro_destino AS field16,
				abs(pdb.base) AS field17,
				abs(pdb.isc) AS field18,
				abs(pdb.igv) AS field19,
				abs(pdb.otros) AS field20,
				CASE
					WHEN am.linked_to_detractions = TRUE THEN '1'
					ELSE '0'
				END AS field21,
				CASE
					WHEN am.linked_to_detractions = TRUE THEN dcp.code
				END AS field22,
				CASE
					WHEN am.linked_to_detractions = TRUE THEN am.voucher_number
				END AS field23,
				CASE
					WHEN am.campo_33_purchase = TRUE THEN '1'
					ELSE '0'
				END AS field24,
				ei.code AS field25,
				CASE
					WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)
				END
				AS field26,
				CASE
					WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)
					ELSE split_part(dr.nro_comprobante, '-', 1)
				END
				AS field27,
				TO_CHAR(dr.date :: DATE, 'dd/mm/yyyy') AS field28,
				CASE
					WHEN vst_c.name = 'PEN' THEN abs(dr.bas_amount)
					ELSE dr.bas_amount/am.currency_rate
				END AS field29,
				CASE
					WHEN vst_c.name = 'PEN' THEN abs(dr.tax_amount)
					ELSE dr.tax_amount/am.currency_rate
				END AS field30
				FROM get_pdb_compras_2('%s','%s',%d) pdb
				LEFT JOIN get_compras_1_1('%s','%s',%d,'pen') vst_c ON vst_c.am_id = pdb.move_id
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN detractions_catalog_percent dcp on dcp.id = am.detraction_percent_id
				LEFT JOIN res_partner rp ON rp.id = am.partner_id
				LEFT JOIN ( SELECT a2.type_document_id,
									a2.date,
									a2.nro_comprobante,
									a2.amount_currency,
									a2.amount,
									a2.bas_amount,
									a2.tax_amount,
									a2.id,
									a2.move_id
								FROM doc_rela_pri a1
									LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = vst_c.am_id
				LEFT JOIN l10n_latam_document_type ei ON ei.id = dr.type_document_id
				WHERE vst_c.td not in ('00','02','09','19','20','31','40','96','99')
		""" % (date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id,
				date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id)

		return sql
	
	def get_sql_pdb_sale(self,date_start,date_end,company_id):
		sql = """
			SELECT
			CASE
				WHEN rp.is_not_home = TRUE THEN '02'
				ELSE '01'
			END AS field1,
			vst_v.td AS field2,
			TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') AS field3,
			vst_v.serie AS field4,
			vst_v.numero AS field5,
			CASE
				WHEN rp.is_not_home = TRUE THEN '03'
				WHEN rp.is_company = FALSE AND rp.is_not_home <> TRUE THEN '01'
				WHEN rp.is_company = TRUE AND rp.is_not_home <> TRUE THEN '02'
			END AS field6,
			vst_v.tdp AS field7,
			vst_v.docp AS field8,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN rp.name
			END AS field9,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
			ELSE rp.last_name
			END AS field10,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
				ELSE rp.m_last_name
			END AS field11,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
				ELSE split_part(rp.name_p, ' ', 1)
			END AS field12,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
				ELSE split_part(rp.name_p, ' ', 2)
			END AS field13,
			CASE
				WHEN vst_v.name = 'PEN' THEN '1'
				WHEN vst_v.name = 'USD' THEN '2'
				ELSE '3'
			END AS field14,
			pdb.cod_destino AS field15,
			pdb.nro_destino AS field16,
			abs(pdb.base) AS field17,
			abs(pdb.isc) AS field18,
			abs(pdb.igv) AS field19,
			abs(pdb.otros) AS field20,
			CASE
				WHEN am.linked_to_perception = TRUE THEN '1'
				ELSE '0'
			END AS field21,
			CASE
				WHEN am.linked_to_perception = TRUE THEN am.type_t_perception
			END AS field22,
			CASE
				WHEN am.linked_to_perception = TRUE AND split_part(am.number_perception, '-', 2) <> '' THEN split_part(am.number_perception, '-', 1)
			END AS field23,
			CASE
				WHEN am.linked_to_perception = TRUE AND split_part(am.number_perception, '-', 2) <> '' THEN split_part(am.number_perception, '-', 2)
				WHEN am.linked_to_perception = TRUE AND split_part(am.number_perception, '-', 2) = '' THEN split_part(am.number_perception, '-', 1)
			END AS field24,
			ei.code AS field25,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)
			END
			AS field26,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)
				ELSE split_part(dr.nro_comprobante, '-', 1)
			END
			AS field27,
			TO_CHAR(dr.date :: DATE, 'dd/mm/yyyy') AS field28,
			CASE
				WHEN vst_v.name = 'PEN' THEN abs(dr.bas_amount)
				ELSE round(dr.bas_amount/am.currency_rate,2)
			END AS field29,
			CASE
				WHEN vst_v.name = 'PEN' THEN abs(dr.tax_amount)
				ELSE round(dr.tax_amount/am.currency_rate,2)
			END AS field30
			FROM get_pdb_ventas_2('%s','%s',%d) pdb
			LEFT JOIN get_ventas_1_1('%s','%s',%d,'pen') vst_v ON vst_v.am_id = pdb.move_id
			LEFT JOIN account_move am ON am.id = vst_v.am_id
			LEFT JOIN res_partner rp ON rp.id = am.partner_id
			LEFT JOIN ( SELECT a2.type_document_id,
						a2.date,
						a2.nro_comprobante,
						a2.amount_currency,
						a2.amount,
						a2.bas_amount,
						a2.tax_amount,
						a2.id,
						a2.move_id
					FROM doc_rela_pri a1
					LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = vst_v.am_id
			LEFT JOIN l10n_latam_document_type ei ON ei.id = dr.type_document_id
		""" % (date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id,
				date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id)
		return sql
	
	def get_sql_pdb_payment(self,date_start,date_end,company_id):
		sql = """
				SELECT 
				CASE
					WHEN rp.is_not_home = TRUE THEN '02'
					ELSE '01'
				END AS field1,
				vst_c.td AS field2,
				CASE
					WHEN vst_c.td in ('50','52','53','54') THEN vst_c.serie||vst_c.anio||vst_c.numero
					ELSE vst_c.serie
				END AS field3,
				CASE 
					WHEN vst_c.td in ('50','52','53','54') THEN ''
					ELSE vst_c.numero
				END AS field4,
				CASE
					WHEN rp.is_not_home = TRUE THEN '03'
					WHEN rp.is_company = FALSE AND rp.is_not_home <> TRUE THEN '01'
					WHEN rp.is_company = TRUE AND rp.is_not_home <> TRUE THEN '02'
				END AS field5,
				vst_c.tdp AS field6,
				vst_c.docp AS field7,
				pay.medio_pago AS field8,
				CASE 
					WHEN pay.medio_pago not in ('009','011','013','014','098') THEN pay.code_bank
				END AS field9,
				pay.field10,
				CASE 
					WHEN pay.medio_pago not in ('009','098') THEN TO_CHAR(pay.fecha :: DATE, 'dd/mm/yyyy')
				END AS field11,
				pay.monto AS field12
				FROM get_compras_1_1('%s','%s',%d,'pen') vst_c
				LEFT JOIN res_partner rp ON rp.id = vst_c.partner_id
				INNER JOIN (
				SELECT  
				a1.partner_id,
				a1.account_id,
				a1.td_sunat,
				a1.nro_comprobante,
				a1.cuenta,
				a1.medio_pago,
				a4.code_bank,
				a4.account_number,
				CASE
					WHEN a1.medio_pago in ('009','011','013','014') THEN NULL
					WHEN a4.code_bank = '99' THEN a4.financial_entity
					WHEN a4.code_bank <> '99' THEN a5.glosa
				END AS field10,
				a1.fecha,
				a1.moneda,
				CASE
					WHEN a1.moneda<>'PEN' THEN importe_me 
					ELSE debe 
				END AS monto
				FROM get_diariog('1990/01/01','%s',%d) a1
				LEFT JOIN account_account a3 ON a3.id=a1.account_id
				LEFT JOIN account_move a5 ON a5.id = a1.move_id
				LEFT JOIN account_journal a2 ON a2.id=a5.journal_id
				LEFT JOIN account_account a4 ON a4.id=a2.default_account_id
				WHERE a2.type IN ('bank','cash') AND a3.internal_type='payable' AND a1.debe IS NOT null
				) pay ON pay.partner_id||pay.td_sunat||pay.nro_comprobante = vst_c.partner_id || vst_c.td  || CASE WHEN vst_c.serie is null THEN vst_c.numero ELSE vst_c.serie||'-'||vst_c.numero END
				AND vst_c.td not in ('00','02','09','19','20','31','40','96','99')
		""" % (date_start.strftime('%Y/%m/%d'),
				date_end.strftime('%Y/%m/%d'),
				company_id,
				date_end.strftime('%Y/%m/%d'),
				company_id)

		return sql
	
	def _get_sql_txt_percepciones(self,type,date_start,date_end,company_id,code):
		sql = ""
		if type == 0:
			sql = """select ruc_agente,serie_cp,numero_cp,to_char( fecha_com_per, 'dd/mm/yyyy'),
			percepcion,t_comp,serie_comp,numero_comp,to_char( fecha_cp, 'dd/mm/yyyy'),montof,null::text as campo
			from get_percepciones('%s','%s',%d) 
			where tipo_comp = '%s'""" % (date_start.strftime('%Y/%m/%d'),date_end.strftime('%Y/%m/%d'),company_id,code)

		else:
			sql = """select ruc_agente,tipo_comp,serie_cp,numero_cp,to_char( fecha_com_per, 'dd/mm/yyyy'),
			percepcion,null::text as campo
			from get_percepciones('%s','%s',%d) 
			where tipo_comp <> '%s'""" % (date_start.strftime('%Y/%m/%d'),date_end.strftime('%Y/%m/%d'),company_id,code)

		return sql