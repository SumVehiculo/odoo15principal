# -*- coding: utf-8 -*-

from mimetypes import init
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO

class LandedCostIt(models.Model):
	_inherit = 'landed.cost.it'

	use_existences = fields.Boolean(string='Existencias por Recibir',default=False,copy=False)
	move_id = fields.Many2one('account.move',string='Asiento',copy=False)
	picking_receivable_ids = fields.One2many('stock.picking','landed_receivable_id',string=u'Movimiento de Almacén')
	picking_type_id = fields.Many2one('stock.picking.type',string=u'Tipo de Operación')
	location_id = fields.Many2one('stock.location',string=u'Ubicación Origen')
	location_dest_id = fields.Many2one('stock.location',string=u'Ubicación Destino')
	receivable_date = fields.Datetime(string='Fecha Ingreso')
	visible_button = fields.Boolean(compute='compute_picking_receivable',store=True)
	count_picking_receivable_ids = fields.Integer(compute='compute_picking_receivable')

	@api.onchange('picking_type_id')
	def onchange_picking_type_id(self):
		for landed in self:
			landed.location_id = landed.picking_type_id.default_location_src_id.id
			landed.location_dest_id = landed.picking_type_id.default_location_dest_id.id

	@api.depends('picking_receivable_ids')
	def compute_picking_receivable(self):
		for landed in self:
			visible_button = False
			if landed.state == 'done' and landed.use_existences and len(self.picking_receivable_ids.filtered(lambda m: m.state in ('done'))) % 2 == 0:
				visible_button = True
			landed.visible_button = visible_button
			landed.count_picking_receivable_ids = len(self.picking_receivable_ids)
	
	def action_view_delivery(self):
		action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

		if len(self.picking_receivable_ids) > 1:
			action['domain'] = [('id', 'in', self.picking_receivable_ids.ids)]
		elif self.picking_receivable_ids:
			form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
			if 'views' in action:
				action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				action['views'] = form_view
			action['res_id'] = self.picking_receivable_ids.id
		picking_id = self.picking_receivable_ids[0]
		action['context'] = dict(self._context, default_picking_type_id=picking_id.picking_type_id.id, default_origin=self.name, default_group_id=picking_id.group_id.id, default_landed_receivable_id=self.id)
		return action

	def create_picking(self):
		#if len(self.picking_receivable_ids.filtered(lambda m: m.state not in ('done'))) > 0:
		#	raise UserError('Los movimientos deben de estar Validados')
		param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not param.partner_landed_cost_existences_id:
			raise UserError('Debe configurar parámetro de Contacto para Existencia por Recibir en Parámetros Principales de Contabilidad, Pestaña "Gasto Vinculado"')
		obj = self.env['stock.picking']
		picking_id = obj.create({
			'partner_id': param.partner_landed_cost_existences_id.id,
			'location_id': self.location_id.id,
			'location_dest_id': self.location_dest_id.id,
			'kardex_date': self.receivable_date,
			'user_id': self.env.uid,
			'origin': self.name,
			'picking_type_id': self.picking_type_id.id,
			'date': self.receivable_date,
			#'immediate_transfer': True,
			'company_id':self.company_id.id,
			'landed_receivable_id': self.id,
		})
		for move_line in self.detalle_ids:
			move = self.env['stock.move'].create(self._get_move_values(move_line.stock_move_id.product_id, move_line.stock_move_id.product_qty,
																		self.location_id.id, self.location_dest_id.id, picking_id,(move_line.total/move_line.stock_move_id.product_qty if move_line.total != 0 else 0)))
			move._action_confirm()
			move._action_assign()
		picking_id.action_confirm()
		picking_id.action_assign()
		picking_id.move_lines._set_quantities_to_reservation()
		picking_id.with_context(skip_immediate=True).button_validate()
		picking_id.write({'kardex_date': self.receivable_date})

	def _get_move_values(self, product, qty, location_id, location_dest_id, idmain, price_unit_it):
		return {
			'product_id': product.id,
			'product_uom': product.uom_id.id,
			'product_uom_qty': qty,
			#'quantity_done': qty,
			'date': self.receivable_date.date(),
			'location_id': location_id,
			'location_dest_id': location_dest_id,
			'picking_id': idmain.id,
			'origin': self.name,
			'picking_type_id': self.picking_type_id.id,
			#'date_expected': self.receivable_date.date(),
			'name': _('INV:') + (idmain.name or ''),
			'company_id':self.company_id.id,
			'price_unit_it': price_unit_it,
		}

	def create_account_move(self):
		stock_journal_id = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).stock_journal_id
		if not stock_journal_id:
			raise UserError(u'No existe Diario de Existencias en Parametros Principales de Contabilidad para su Compañía')
		lineas = []
		for elem in self.detalle_ids:
			if not elem.stock_move_id.product_id.categ_id.property_stock_valuation_account_id:
				raise UserError(u'No esta establecida la Cuenta de valoración de stock en la Categoría del Producto "%s"'%(elem.stock_move_id.product_id.display_name))
			if not elem.stock_move_id.product_id.categ_id.property_account_stock_receivable_categ_id:
				raise UserError(u'No esta establecida la Cuenta para Existencias por Recibir en la Categoría del Producto "%s"'%(elem.stock_move_id.product_id.display_name))
			
			vals = (0,0,{
				'account_id': elem.stock_move_id.product_id.categ_id.property_stock_valuation_account_id.id,
				'name': 'POR EL TRASPASO DE EXISTENCIAS POR RECIBIR AL ALMACEN "%s"'%(self.picking_type_id.warehouse_id.name),
				'debit': elem.total,
				'credit': 0,
				'product_id':elem.stock_move_id.product_id.id,
				'product_uom_id':elem.stock_move_id.product_id.uom_id.id,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)

			vals = (0,0,{
				'account_id': elem.stock_move_id.product_id.categ_id.property_account_stock_receivable_categ_id.id,
				'name': 'POR EL TRASPASO DE EXISTENCIAS POR RECIBIR AL ALMACEN "%s"'%(self.picking_type_id.warehouse_id.name),
				'debit': 0,
				'credit': elem.total,
				'product_id':elem.stock_move_id.product_id.id,
				'product_uom_id':elem.stock_move_id.product_id.uom_id.id,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': stock_journal_id.id,
			'date': self.receivable_date.date(),
			'line_ids':lineas,
			'ref': self.name,
			'glosa': 'POR EL TRASPASO DE EXISTENCIAS POR RECIBIR AL ALMACEN "%s"'%(self.picking_type_id.warehouse_id.name),
			'move_type':'entry'})
		
		move_id.action_post()
		self.move_id = move_id.id
	
	def borrador(self):
		if self.move_id:
			raise UserError(u'No puede establecer a borrador si tiene un Asiento Contable generado por Existencias')
		if  len(self.picking_receivable_ids.filtered(lambda m: m.state in ('done'))) % 2 != 0:
			raise UserError(u'No puede establecer a borrador si tiene una Transferencia generada por Existencias, genere una devolución si desea hacer algún cambio')
		t = super(LandedCostIt, self).borrador()
		return t
	
class ReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'
	
	def _prepare_picking_default_values(self):
		t = super(ReturnPicking, self)._prepare_picking_default_values()
		t['landed_receivable_id'] = self.picking_id.landed_receivable_id.id
		return t