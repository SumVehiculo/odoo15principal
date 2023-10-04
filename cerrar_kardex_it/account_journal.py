# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
from datetime import timedelta


class kardex_cerrado_config(models.Model):
	_name = 'kardex.cerrado.config'

	name = fields.Char('Nombre',required=True)
	fecha_inicio = fields.Date('Fecha Inicio',required=True)
	fecha_fin = fields.Date('Fecha Final',required=True)
	listado_locaciones = fields.Many2many('stock.location','kardex_cerrador_locaciones_rel','kardex_cc_id','location_id','Ubicaciones')
	company_id = fields.Many2one('res.company','Compania',required=True, default=lambda self: self.env.company,readonly=True)




	def agregar_krdx_parameter(self):
		for i in self:
			parameter = i.env["kardex.parameter"].sudo().search([('company_id','=',i.env.company.id)],limit=1)
			if not parameter.id:
				parameter = i.env["kardex.parameter"].sudo().create({
					'picking_type_salida':i.env["stock.picking.type"].sudo().search([('company_id','=',i.env.company.id)],limit=1).id,
					'picking_type_ingreso':i.env["stock.picking.type"].sudo().search([('company_id','=',i.env.company.id)],limit=1).id,
					'company_id':i.env.company.id
				})
			wzard = i.env["kardex.parameter.guardar.anio"].create({
					'fecha_inicio':i.fecha_inicio,
					'fecha_final':i.fecha_fin
				})
			vs = wzard.guardar()
			return vs



	


class gastos_vinculados_it(models.Model):
	_inherit = 'landed.cost.it'


	@api.model
	def create(self,vals):
		t = super(gastos_vinculados_it,self).create(vals)
		t.verifycrd()
		return t

	def verifycrd(self):
		for t in self:
			if t.date_kardex:
				for i in self.env['kardex.cerrado.config'].sudo().search([('company_id','=',self.env.company.id)]):
					if str(t.date_kardex - timedelta(hours=5) if t.date_kardex else t.date_kardex)[:10] >= str(i.fecha_inicio) and str(t.date_kardex - timedelta(hours=5) if t.date_kardex else t.date_kardex)[:10] <= str(i.fecha_fin):
						raise UserError("Alerta! El kardex fue cerrado para este fecha y Ubicación")
	
	def copy(self,default=None):
		t = super(gastos_vinculados_it,self).copy(default)
		t.verifycrd()
		return t


	
	def write(self,vals):
		for i in self:
			i.verifycrd()
		t = super(gastos_vinculados_it,self).write(vals)
		for i in self:
			i.verifycrd()
		return t

	
	def unlink(self):
		for i in self:
			i.verifycrd()
		return super(gastos_vinculados_it,self).unlink()

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	cerrado_krdx = fields.Boolean(string="Periodo Cerrado",store=False,compute="get_crrado_verify")

	def get_crrado_verify(self):
		for stock in self:
			cerrado_krdx=False
			for t in stock.move_ids_without_package:
				if t.kardex_date:
					if cerrado_krdx!=False:
						break
					for i in self.env['kardex.cerrado.config'].sudo().search([('company_id','=',self.env.company.id)]):
						if str(t.kardex_date - timedelta(hours=5) if t.kardex_date else t.kardex_date)[:10] >= str(i.fecha_inicio) and str(t.kardex_date - timedelta(hours=5) if t.kardex_date else t.kardex_date)[:10] <= str(i.fecha_fin):
							cerrado_krdx=True
							break
			stock.cerrado_krdx = cerrado_krdx





	def nohacernada(self):
		return

	@api.model
	def create(self,vals):		
		t = super(stock_picking,self).create(vals)
		if len(vals.keys() )== 1:
			if 'invoice_id' in vals:
				return t
		else:
			t.verifycrd()
		return t

	def verifycrd(self):
		for t in self:
			if t.kardex_date  and t.state =='done':
				for i in self.env['kardex.cerrado.config'].search([('company_id','=',self.env.company.id)]):
					if str(t.kardex_date - timedelta(hours=5) if t.kardex_date else t.kardex_date)[:10] >= str(i.fecha_inicio) and str(t.kardex_date - timedelta(hours=5) if t.kardex_date else t.kardex_date)[:10] <= str(i.fecha_fin):
						raise UserError("Alerta! El kardex fue cerrado para este fecha y Ubicación")

	
	def copy(self,default=None):
		t = super(stock_picking,self).copy(default)
		t.verifycrd()
		return t

	
	def write(self,vals):
		m = super(stock_picking,self).write(vals)
		if len(vals.keys() )== 1:
			if 'invoice_id' in vals:
				return m
		for i in self:
			i.verifycrd()
		return m

	
	def unlink(self):
		for i in self:
			i.verifycrd()
		return super(stock_picking,self).unlink()




class stock_move(models.Model):
	_inherit = 'stock.move'


	@api.model
	def create(self,vals):		
		t = super(stock_move,self).create(vals)
		t.verifycrd()
		return t

	def verifycrd(self):
		for picking in self:
			if picking.kardex_date and picking.state =='done':
				for i in self.env['kardex.cerrado.config'].search([('company_id','=',self.env.company.id)]):
					if str(picking.kardex_date - timedelta(hours=5) if picking.kardex_date else picking.kardex_date)[:10] >= str(i.fecha_inicio) and str(picking.kardex_date - timedelta(hours=5) if picking.kardex_date else picking.kardex_date)[:10] <= str(i.fecha_fin):
						raise UserError("Alerta! El kardex fue cerrado para este fecha y Ubicación")

	
	def copy(self,default=None):
		t = super(stock_move,self).copy(default)
		t.verifycrd()
		return t

	
	def write(self,vals):
		m = super(stock_move,self).write(vals)
		for i in self:
			i.verifycrd()
		return m

	
	def unlink(self):
		for i in self:
			i.verifycrd()
		return super(stock_move,self).unlink()
