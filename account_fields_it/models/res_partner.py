# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from psycopg2 import sql, DatabaseError
from odoo.exceptions import ValidationError,UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
	_inherit = 'res.partner'

	is_not_home = fields.Boolean(string='No Domiciliado', default=False)
	country_home_nd = fields.Char(help='Tabla 35 SUNAT', string='Pais Residencia del N.D.',size=4)
	home_nd = fields.Char(string='Domicilio en el Extranjero del N.D.',size=200)
	ide_nd = fields.Char(string='Numero de Identificacion del sujeto N.D.',size=50)
	v_con_nd = fields.Char(help='Tabla 27 SUNAT', string='Vinculo entre el Contribuyente y el Residente Extranjero',size=2)
	c_d_imp = fields.Char(help='Tabla 25 SUNAT', string='Convenio para Evitar Doble Imposicion',size=2)
	name_p = fields.Char(string='Nombres',size=200)
	last_name = fields.Char(string='Apellido Paterno',size=200)
	m_last_name = fields.Char(string='Apellido Materno',size=200)
	is_customer = fields.Boolean(string='Cliente',default=False)
	is_employee = fields.Boolean(string='Empleado',default=False)
	is_supplier = fields.Boolean(string='Proveedor', default=False)