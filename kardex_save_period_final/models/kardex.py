# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class KardexSave(models.Model):
	_inherit = 'kardex.save'

	periodo_automatico_id = fields.Many2one("kardex.cerrado.config",string="Periodo Cerrado",copy=False)

	def agregar_krdx_parameter(self):
		wiz = False
		for i in self:
			i.state="done"
			if i.periodo_automatico_id.id:
				wiz = i.periodo_automatico_id.agregar_krdx_parameter()
		return wiz



	def write(self, vals):
		if "state" in vals:
			for i in self:
				i.drop_periodo()
		t = super(KardexSave,self).write(vals)
		if "state" in vals:
			for i in self:
				i.crearperiodo_automatico()
		return t
#eliminar solo en draft ocultar botones

	def drop_periodo(self):
		for i in self:
			if i.state == 'done':
				if i.periodo_automatico_id.id:
					i.periodo_automatico_id.with_context({'permiso_eliminar_auto':1}).sudo().with_context({'permiso_eliminar_auto':1}).unlink()


	def crearperiodo_automatico(self):
		for i in self:
			if i.state == 'done':
				cerrado_auto = i.env["kardex.cerrado.config"].sudo().create({                                                                    
										'name':str(i.name.code),
										'company_id':i.company_id.id,
										'fecha_inicio':i.name.date_start,
										'fecha_fin':i.name.date_end
									})
				i.periodo_automatico_id = cerrado_auto.id
		
	def unlink(self):
		for i in self:
			if i.state != 'draft':
				raise UserError('No se puede eliminar un Guardado Kardex si este no esta en Borrador') 
		t = super(KardexSave, self).unlink()
		return t




class kardex_cerrado_config(models.Model):
	_inherit = 'kardex.cerrado.config'

	def write(self,vals):
		for i in self:
			relacion = i.env["kardex.save"].sudo().search([("company_id","=",i.company_id.id),("periodo_automatico_id","=",i.id)])
			if len(relacion)>0:
				raise UserError("Imposible Modificar Periodo, Generado Desde Un Guardado Kardex")
		t = super(kardex_cerrado_config,self).write(vals)
		return t

	def unlink(self):
		if not 'permiso_eliminar_auto' in self.env.context:
			for i in self:
				relacion = i.env["kardex.save"].sudo().search([("company_id","=",i.company_id.id),("periodo_automatico_id","=",i.id)])
				if len(relacion)>0:
					raise UserError("Imposible Eliminar Periodo, Generado Desde Un Guardado Kardex")
			
		t = super(kardex_cerrado_config,self).unlink()
		return t