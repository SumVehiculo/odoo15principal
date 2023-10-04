# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *
from datetime import timedelta


class sql_kardex(models.Model):
	_inherit ='sql.kardex'

	def _have_mrp(self):
		return True

class stock_move_line(models.Model):
	_inherit = 'stock.move.line'

	def edit_kardex_date(self):
		return {			
			'name':u'Editar Fecha Kardex',
			'res_id':self.id,
			'view_mode': 'form',
			'res_model': 'stock.move.line',
			'view_id': self.env.ref("mrp_kardex.move_line_fecha_kardex").id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}


	def edit_mostrar_no(self):
		return {			
			'name':u'Editar No Mostrar en Kardex',
			'res_id':self.id,
			'view_mode': 'form',
			'res_model': 'stock.move.line',
			'view_id': self.env.ref("mrp_kardex.move_line_no_mostrar").id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}


class MrpProduction(models.Model):
	_inherit = 'mrp.production'

	kardex_date = fields.Datetime(string="Fecha Kardex")
	no_mostrar = fields.Boolean('No Mostrar en Kardex', copy=False)
	operation_type_sunat_consume = fields.Many2one('type.operation.kardex', string="Tipo de Operacion Sunat Consumo")
	operation_type_sunat_fp = fields.Many2one('type.operation.kardex', string="Tipo de Operacion Sunat Producto Terminado")

	def update_kardex_dates(self):
		for i in self:
			i.kardex_date = datetime.now()
			move_line_ids = self.env['stock.move.line'].search(['|', ('move_id.raw_material_production_id', '=', i.id), ('move_id.production_id', '=', i.id)])
			for moves_line in move_line_ids:
				if moves_line.move_id.id:
					moves_line.move_id.with_context({'permitido':1}).write({'kardex_date': i.kardex_date })
			for elem in self.env['stock.move.line'].search([('move_id.production_id', '=', i.id)]):
				if elem.move_id.id:
					elem.move_id.with_context({'permitido':1}).write({'kardex_date':i.kardex_date + timedelta(seconds=1)})
			move_line_ids.with_context({'permitido':1}).write({'kardex_date': i.kardex_date })
			move_line_ids.refresh()
			for elem in self.env['stock.move.line'].search([('move_id.production_id', '=', i.id)]):
				elem.refresh()
				elem.with_context({'permitido':1}).write({'kardex_date':i.kardex_date + timedelta(seconds=1)})
			

	def button_mark_done(self):
		self.ensure_one()
		error = ''
		for line in self.move_raw_ids:
			if line.quantity_done == 0:
				error += '- %s.\n' % (line.product_id.name)
		#if error:
		#	raise UserError('Las cantidades consumidas no pueden quedar en cero en los siguientes productos:\n %s' % (error))

		t = super(MrpProduction, self).button_mark_done()

		self.update_kardex_dates()
		return t

class MRP_unbuild(models.Model):
	_inherit= 'mrp.unbuild'

	def action_validate(self):
		t = super(MRP_unbuild,self).action_validate()


		for i in self:
			move_line_ids = self.env['stock.move.line'].search(['|', ('move_id.consume_unbuild_id', '=', i.id), ('move_id.unbuild_id', '=', i.id)])
			move_line_ids.with_context({'permitido':1}).write({'kardex_date': datetime.now() })
			move_line_ids.refresh()
			for elem in self.env['stock.move.line'].search([('move_id.unbuild_id', '=', i.id)]):
				elem.refresh()
				elem.with_context({'permitido':1}).write({'kardex_date':datetime.now() - timedelta(seconds=1)})					

		return t


