# -*- encoding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import Warning
import logging
log = logging.getLogger(__name__)

class StockMove(models.Model):
	_inherit = 'stock.move'

	def get_despatch_product_name(self):
		return self.description_picking if self.description_picking else self.product_id.display_name

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	expedition_id = fields.Many2one('logistic.expedition', string='Expedition')
	despatch_id = fields.Many2one('logistic.despatch', string='Despatch', copy=False)

	def _prepare_despatch(self):
		picking = self
		partner_id = picking.partner_id.id
		delivery_address_id = picking.partner_id.id

		if picking.partner_id.parent_id:
			partner_id = picking.partner_id.parent_id.id
			delivery_address_id = picking.partner_id.parent_id.id

		if not picking.partner_id:
			delivery_address_id = picking.picking_type_id.warehouse_id.partner_id.id

		journal_id = self.env['account.journal'].search([('type','=','general'),('code','=like','T%')])
		if not journal_id:
			journal_id = self.env['account.journal'].search([('type','=','general')])

		if not journal_id:
			raise Warning('Journals not found for despatchs')

		origin_address_id = False
		delivery_address_id = False
		warehouse_id = False
		if picking.picking_type_id.code=='incoming':
			origin_address_id = picking.partner_id.id
			delivery_address_id = picking.picking_type_id.warehouse_id.partner_id.id
			warehouse_id = picking.picking_type_id.warehouse_id
		elif picking.picking_type_id.code=='outgoing':
			origin_address_id = picking.picking_type_id.warehouse_id.partner_id.id
			delivery_address_id = picking.partner_id.id
			warehouse_id = picking.picking_type_id.warehouse_id
		elif picking.picking_type_id.code=='internal':
			origin_address_id = picking.picking_type_id.warehouse_id.partner_id.id
			delivery_address_id = origin_address_id
			warehouse_id = picking.picking_type_id.warehouse_id
		despatch = {
			'warehouse_id': warehouse_id.id if warehouse_id else False,
			'journal_id': warehouse_id.despatch_journal_ids[0].id if warehouse_id.despatch_journal_ids else journal_id[0].id,
			'company_id':picking.company_id.id,
			'partner_id':partner_id,
			'origin_address_id':origin_address_id,
			'delivery_address_id':delivery_address_id,
			'line_ids':[],
			'picking_ids':[[6,0,[picking.id]]]
		}
		if picking.note:
			despatch['note'] = picking.note
		if self._context.get('force_issue_date', False):
			despatch['issue_date'] = self._context.get('force_issue_date')
		if self._context.get('force_start_date', False):
			despatch['start_date'] = self._context.get('force_start_date')
		if self._context.get('force_journal_id', False):
			despatch['journal_id'] = self._context.get('force_journal_id')
		if self._context.get('force_shipment_reason', False):
			despatch['shipment_reason'] = self._context.get('force_shipment_reason')
		if self._context.get('force_carrier_id', False):
			despatch['carrier_id'] = self._context.get('force_carrier_id')
		if self._context.get('force_vehicle_id', False):
			despatch['vehicle_id'] = self._context.get('force_vehicle_id')
		if self._context.get('force_driver_id', False):
			despatch['driver_id'] = self._context.get('force_driver_id')
		if self._context.get('force_origin_address_id', False):
			despatch['origin_address_id'] = self._context.get('force_origin_address_id')
		if self._context.get('force_delivery_address_id', False):
			despatch['delivery_address_id'] = self._context.get('force_delivery_address_id')
		if self._context.get('force_internal_number', False):
			despatch['internal_number'] = self._context.get('force_internal_number')
		
		weight_total = 0
		for line in picking.move_lines:
			product_name = line.get_despatch_product_name()
			'''if line.sale_line_id:
				product_name = line.sale_line_id.name'''
			despatch['line_ids'].append([0,0,{
				'product_id':line.product_id.id,
				'name':product_name,
				'quantity':line.product_uom_qty,
				'uom_id':line.product_uom.id,
				'weight':line.product_id.weight*line.product_uom_qty ,
				'volume': line.product_id.volume * line.product_uom_qty
				}])
		return despatch

	def generate_logistic_despatch(self):
		despatch_ids = []
		for picking in self:
			if picking.company_id.logistic_picking_done_restrict and picking.state!='done':
				raise Warning(_('Picking status is not done'))
			if picking.despatch_id:
				if picking.despatch_id.state=='open':
					raise Warning(_('This document already has a remission guide'))
			despatch = picking._prepare_despatch()
			_despatch = self.env['logistic.despatch'].create(despatch)
			picking.write({'despatch_id':_despatch.id})
			despatch_ids.append(_despatch.id)
		if self._context.get('force_return_array', False):
			return despatch_ids
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'logistic.despatch',
			'view_mode': 'form',
			'res_id': _despatch.id,
			'target': 'current',
			'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
		}