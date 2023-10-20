# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class Ubicacion(models.Model):
	_name = 'ubicacion'

	almacen = fields.Many2one('stock.location', string="Almacén: ")
	name = fields.Char(string="Rack: ")
	posicion = fields.Integer(string="Posición: ")
	product_id = fields.Many2one('product.template', string='Producto')

class Casepack(models.Model):
	_name = 'casepack'

	name = fields.Char(string="Unidades: ")
	product_id = fields.Many2one('product.template', string='Producto')

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	tabla_ubicacion = fields.One2many('ubicacion', 'product_id', string='Ubicación')
	cdg_barras_cm = fields.Char(string="Código de Barras Caja Máster ")
	t_caja_largo = fields.Float(string="Tamaño Caja Largo ")
	t_caja_ancho = fields.Float(string="Tamaño Caja Ancho ")
	t_caja_alto = fields.Float(string="Tamaño Caja Alto ")
	p_caja = fields.Float(string="Peso Caja ")
	c_pack = fields.Many2one('uom.uom', string='Case Pack ')
	conversion_litros = fields.Float(string="Conversión a litros ")
	img = fields.Char(string="Imagen url")
	fic_tec = fields.Char(string="Ficha técnica ")
	fic_seg = fields.Char(string="Ficha de Seguridad ")
