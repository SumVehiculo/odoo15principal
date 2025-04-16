from odoo import _, api, fields, models, tools
class account_asset_71_rep(models.TransientModel):

	_inherit = 'account.asset.71.rep'


	def _get_sql_71(self,date_fiscal_year_start,date_period_start,date_period_end,company_id,period_code=None):
		sql = """
				select row_number() OVER () AS id,
				T.campo1,
				T.campo2,
				T.campo3,
				T.campo4,
				T.campo5,
				T.campo6,
				T.campo7,
				T.campo8,
				T.campo9,
				T.campo10,
				T.campo11,
				(T.campo7+T.campo8+T.campo9+T.campo10+T.campo11) as campo12,
				T.campo13,
				(T.campo7+T.campo8+T.campo9+T.campo10+T.campo11+T.campo13) as campo14,
				T.campo15,
				T.campo16,
				T.campo17,
				T.campo18,
				T.campo19,
				T.campo20,
				T.campo21,
				T.campo22,
				T.campo23,
				(T.campo20+T.campo21+T.campo22+T.campo23) as campo24,
				T.campo25,
				(T.campo20+T.campo21+T.campo22+T.campo23+T.campo25) as campo26
				from
				(select asset.code as campo1,
				aa.code as campo2,
				asset.name as campo3,
				asset.brand as campo4,
				asset.model as campo5,
				asset.plaque as campo6,
				case
					when coalesce(asset.date_at,asset.date) < '%s' then asset.valor_at::numeric
					else 0::numeric
				end
				as campo7,
				case
					when coalesce(asset.date_at,asset.date) >= '%s' then asset.valor_at::numeric
					else 0::numeric
				end
				as campo8,
				0::numeric as campo9,
				0::numeric as campo10,
				0::numeric as campo11,
				0::numeric as campo13,
				coalesce(asset.date_at,asset.date) as campo15,
				asset.first_depreciation_manual_date as campo16,
				'Metodo Lineal' as campo17,
				asset.depreciation_authorization as campo18,
				asset.depreciation_rate as campo19,
				case 
				when t1.campo20 is not null then COALESCE(t1.campo20, 0)+COALESCE(asset.depreciacion_at, 0)::numeric
				else 0::numeric + COALESCE(asset.depreciacion_at, 0)::numeric
				end
				as campo20,
				case when '%s' = '00' then 0::numeric else coalesce(t2.campo21,0) end as campo21,
				0::numeric as campo22,
				0::numeric as campo23,
				0::numeric as campo25,
				asset.id as asset_id
				from account_asset_asset asset
				left join account_asset_category cat on cat.id = asset.category_id
				left join account_account aa on aa.id = cat.account_asset_id
				left join (select asset_id, sum(amount) as campo20 from account_asset_depreciation_line 
				where depreciation_date < '%s'
				group by asset_id)t1 on t1.asset_id = asset.id
				left join (select asset_id, sum(amount) as campo21 from account_asset_depreciation_line 
				where (depreciation_date between '%s' and '%s')
				group by asset_id)t2 on t2.asset_id = asset.id
				where asset.company_id = %d and (asset.only_format_74 = False or asset.only_format_74 is null) and asset.state <> 'draft'
				and coalesce(asset.date_at,asset.date) <= '%s' and (asset.f_baja is null or asset.f_baja > '%s'))T
		""" % (date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		period_code[4:],
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_period_end.strftime('%Y/%m/%d'),
		company_id,
		date_period_end.strftime('%Y/%m/%d'),
		date_period_start.strftime('%Y/%m/%d'))

		return sql
	