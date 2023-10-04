# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	warehouse_ids_gs = fields.Many2many('stock.warehouse', 'stock_warehouse_parameter_rel', string='Omitir Almacenes')
	location_ids_csa = fields.Many2many('stock.location', 'stock_location_warehouse_parameter_rel', string=u'Ubicación Origen')
	location_dest_ids_csa = fields.Many2many('stock.location', 'stock_location_dest_warehouse_parameter_rel', string=u'Ubicación Destino')
	operation_type_ids_csa = fields.Many2many('type.operation.kardex', 'type_operation_kardex_csa_warehouse_parameter_rel', string=u'Tipo de Operación')