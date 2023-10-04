# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError


class AccountAccountTag(models.Model):
	_inherit = 'account.account.tag'

	record_shop = fields.Selection([
									('1',u'Base imponible destinadas a operaciones de gravadas y/o de exportación.'),
									('2',u'Base imponible destinadas a operaciones gravadas y/o de exportación y a operaciones no gravadas.'),
									('3',u'Base imponible destinadas a operaciones no gravadas.'),
									('4',u'Compras no gravadas.'),
									('5',u'Impuesto selectivo al consumo.'),
									('6',u'Otros.'),
									('7',u'Impuesto para base imponible destinadas a operaciones de gravadas y/o de exportación.'),
									('8',u'Impuesto para base imponible destinadas a operaciones gravadas y/o de exportación y a operaciones no gravadas.'),
									('9',u'Impuesto para base imponible destinadas a operaciones no gravadas.'),
									('10',u'icbper.')
									],string='Registro de Compra')
	record_sale = fields.Selection([
									('1',u'Valor de Exportación.'),
									('2',u'Base Imponible Ventas.'),
									('3',u'Ventas Inafectas.'),
									('4',u'Ventas Exoneradas.'),
									('5',u'Impuesto Selectivo al Consumo.'),
									('6',u'Otros.'),
									('7',u'Impuesto para Base Imponible Ventas.'),
									('8',u'icbper.')
									],string='Registro de Venta')
	record_fees = fields.Selection([
									('1',u'Renta de Cuarta'),
									('2',u'Retencion'),
									],string='Libro de Honorarios')
	sequence = fields.Integer(string='Secuencia')
	col_pdb = fields.Char(string='PDB')

