# -*- coding: utf-8 -*-
from odoo import api, fields, models, _ , exceptions
from odoo.exceptions import UserError

class make_kardex(models.TransientModel):
	_inherit = "make.kardex"

	@api.model
	def default_get(self, fields):
		res = super(make_kardex, self).default_get(fields)
		import datetime
		from datetime import timedelta
		posible_fecha = self.env["kardex.save"].sudo().search([("company_id","=",self.env.company.id),("state","=","done")], limit=1, order="date_fin_related desc")
		fecha = False
		if posible_fecha.id:
			fecha = posible_fecha.date_fin_related + timedelta(days=1)
		mes = str(fecha.month if fecha else (datetime.datetime.now() - timedelta(hours=5)).date().month)
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha if fecha else fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha if fecha else fecha_inicial})
		res.update({'ffin':fecha_hoy})
		return res

class make_kardex_lote(models.TransientModel):
	_inherit = "make.kardex.lote"

	@api.model
	def default_get(self, fields):
		res = super(make_kardex_lote, self).default_get(fields)
		import datetime
		from datetime import timedelta
		posible_fecha = self.env["kardex.save"].sudo().search([("company_id","=",self.env.company.id),("state","=","done")], limit=1, order="date_fin_related desc")
		fecha = False
		if posible_fecha.id:
			fecha = posible_fecha.date_fin_related + timedelta(days=1)
		mes = str(fecha.month if fecha else (datetime.datetime.now() - timedelta(hours=5)).date().month)
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'

		res.update({'fecha_ini_mod':fecha if fecha else fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha if fecha else fecha_inicial})
		res.update({'ffin':fecha_hoy})
		return res




class make_kardex_valorado_stock(models.TransientModel):
	_inherit = "make.kardex.valorado.stock"


	@api.model
	def default_get(self, fields):
		res = super(make_kardex_valorado_stock, self).default_get(fields)
		import datetime
		from datetime import timedelta
		posible_fecha = self.env["kardex.save"].sudo().search([("company_id","=",self.env.company.id),("state","=","done")], limit=1, order="date_fin_related desc")
		fecha = False
		if posible_fecha.id:
			fecha = posible_fecha.date_fin_related + timedelta(days=1)
		mes = str(fecha.month if fecha else (datetime.datetime.now() - timedelta(hours=5)).date().month)
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha if fecha else fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha if fecha else fecha_inicial})
		res.update({'ffin':fecha_hoy})
		return res