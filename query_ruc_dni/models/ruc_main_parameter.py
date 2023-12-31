# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class RucMainParameter(models.Model):
	_name = 'ruc.main.parameter'

	#_sql_constraints = [('unique_main_parameter', 'unique(id)', 'No se puede crear mas de un registro de Configuracion')]

	name = fields.Char(default='Parametros Principales')
	query_email = fields.Char(string='Email')
	query_token = fields.Char(string='Token')
	query_type = fields.Char(string='Tipo de Respuesta')
	query_dni_url = fields.Char(string='Direccion Consulta DNI')
	query_ruc_url = fields.Char(string='Direccion Consulta RUC')
	query_supplier = fields.Selection([('1','INSITE'),('2','MIGO'),('3','SUNAT')],string='Proveedor',default='1')
	migo_token = fields.Char(string='Token MIGO')

	def verify_query_parameters(self):
		res = self.search([],limit=1)
		if res.query_supplier == '1':
			if  not res.query_email or \
				not res.query_token or \
				not res.query_type or \
				not res.query_dni_url or \
				not res.query_ruc_url:
				raise UserError('Falta configurar parametros para Consulta RUC y DNI en Parametros Principales de RUC/DNI')
			else:
				return res
		elif res.query_supplier == '2':
			if not res.migo_token:
				raise UserError('Falta configurar parametros para Consulta RUC y DNI en Parametros Principales de RUC/DNI')
			else:
				return res
		else:
			return res
		

	@api.model
	def create(self,vals):
		if len(self.env['ruc.main.parameter'].search([])) > 0:
			raise UserError('No se puede crear mas de un Parametro Principal')
		return super(RucMainParameter,self).create(vals)