# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	free_location_ids_csa = fields.Many2many('stock.location', 'stock_location_warehouse_parameter_free_rel', string=u'Ubicación Origen Entregas')
	free_location_dest_ids_csa = fields.Many2many('stock.location', 'stock_location_dest_warehouse_parameter_free_rel', string=u'Ubicación Destino Entregas')
	free_operation_type_ids_csa = fields.Many2many('type.operation.kardex', 'type_operation_kardex_csa_warehouse_parameter_free_rel', string=u'Tipo de Operación Entregas')