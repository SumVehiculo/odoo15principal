# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from datetime import date
import calendar

PERIODS_CODES = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13']
PERIODS_NAMES = ['APERTURA','ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE','CIERRE']

class period_generator_kardex(models.TransientModel):
	_name = "period.generator.kardex"

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		if not fiscal_year:
			raise UserError(u'No existe un año fiscal con el año actual.')
		else:
			return fiscal_year.id

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())

	def generate_periods(self):
		if not self.fiscal_year_id:
			raise UserError('El año fiscal es un campo Obligatorio')
		log = []
		for c,code in enumerate(PERIODS_CODES):
			fiscal_year = self.fiscal_year_id.name
			period_code = fiscal_year + code
			period_name = PERIODS_NAMES[c] + '-' + fiscal_year
			if code == '00':
				date_start = date(int(fiscal_year),1,1)
				date_end = date(int(fiscal_year),1,1)
			elif code == '13':
				date_start = date(int(fiscal_year),12,31)
				date_end = date(int(fiscal_year),12,31)
			else:
				date_start = date(int(fiscal_year),c,1)
				date_end = date(int(fiscal_year),c,calendar.monthrange(int(fiscal_year),c)[1])
			account_period = self.env['account.period.kardex'].search([('code','=',period_code),('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)
			if account_period:
				continue
			else:
				if code == '00' or code == '13':
					self.env['account.period.kardex'].with_context({'generar_periodos':1}).create({'code':period_code,
												   'name':period_name,
												   'fiscal_year_id':self.fiscal_year_id.id,
												   'date_start':date_start,
												   'date_end':date_end,
												   'close':True})
				else:
					self.env['account.period.kardex'].with_context({'generar_periodos':1}).create({'code':period_code,
													'name':period_name,
													'fiscal_year_id':self.fiscal_year_id.id,
													'date_start':date_start,
													'date_end':date_end})
				log.append(period_name)
		return self.env['popup.it'].get_message('SE GENERARON LOS SIGUIENTES PERIODOS DE MANERA CORRECTA: \n %s' % ('\n'.join(log)))





#class account_period_kardex(models.Model):
#	_inherit = 'account.period.kardex'


#	@api.model
#	def create(self,vals):
#		if "generar_periodos" in self.env.context:
#			t = super(account_period_kardex,self).create(vals)
#			return t
#		else:
#			raise UserError("La creación de periodos se genera desde el menu 'Generar periodos kardex'")


#	def write(self,vals):
#		if "generar_periodos" in self.env.context:
#			t = super(account_period_kardex,self).write(vals)
#			return t
#		else:
#			raise UserError("La Modificación de periodos se genera desde el menu 'Generar periodos kardex'")


#	def unlink(self):
#		if self.env.user.has_group('kardex_save_period_valorized.group_generator'):
#			for i in self:
#				srch = self.env["kardex.save"].sudo().search([("name","=",i.id),("state","!=","draft")])
#				if len(srch)>0:
#					raise UserError("No Puede Eliminar Periodos Seleccionados en cierre de kardex")
#			t = super(account_period_kardex,self).unlink()
#			return t
#		else:
#			raise UserError("La Eliminación de periodos se genera desde el menu 'Generar periodos kardex'")




























class KardexSave(models.Model):
	_inherit = 'kardex.save'




	def save_valorized(self):
		self.state="valorized"
		vals={
			"fecha_inicio":self.name.date_start,
			"fecha_final":self.name.date_end
		}
		wizard = self.env["valor.unitario.kardex"].create(vals)
		msg = wizard.sudo().do_valor()
		return msg

	def save_valorized_dol(self):
		self.state="valorized_dol"
		vals={
			"fecha_inicio":self.name.date_start,
			"fecha_final":self.name.date_end
		}
		wizard = self.env["valor.unitario.kardex"].create(vals)
		msg = wizard.sudo().do_valor_dolar()
		return msg



	@api.model
	def create(self,vals):
		if vals:
			vals["fecha_creacion"]=datetime.now()
		t = super(KardexSave,self).create(vals)
		return t


	def agregar_krdx_parameter(self):
		t = super(KardexSave,self).agregar_krdx_parameter()
		fechasave = datetime.now()
		for i in self:
			i.fecha_finalizado = fechasave
		return t

	def draft(self):
		if 'draft_all' in self.env.context:
			for i in self:
				i.check_procecenvalorizado_once=False
				i.corriovalorizado = False
				i.fecha_finalizado = False
				i.user_aprob_costo_cero_id = False
				i.fecha_aprob_costo_cero = False
				i.fecha_aprob_sunat_oper = False
				i.user_aprob_sunat_oper = False
				t = super(KardexSave,self).draft()
				return t
		t = super(KardexSave,self).draft()
		self.check_procecenvalorizado_once=False
		self.corriovalorizado = False
		self.fecha_finalizado = False
		self.user_aprob_costo_cero_id = False
		self.fecha_aprob_costo_cero = False
		self.fecha_aprob_sunat_oper = False
		self.user_aprob_sunat_oper = False
		for i in self:
			for draftear in i.env["kardex.save"].sudo().search([("company_id","=",i.company_id.id),("name.date_start",">=",i.name.date_end)]):
				draftear.sudo().with_context({'draft_all':1}).draft()
		return t



	def aprobar_costo_cero(self):
		if self.env.user.has_group('kardex_save_period_valorized.group_aprob_costo_cero'):
			fecha = datetime.now()
			for i in self:
				if not i.check_procecenvalorizado_once:
					raise UserError("Validar Valorizado primero para luego ver si existe casos de costo 0 y aprobar dichos costos")
				i.state = 'val_sol'
				i.user_aprob_costo_cero_id = self.env.user.id
				i.fecha_aprob_costo_cero = fecha
		else:
			raise UserError("Aprobaciones permitidas para el grupo 'Cierre Kardex - Aprobar Costo 0'")



	def aprobar_costo_cero_dolar(self):
		if self.env.user.has_group('kardex_save_period_valorized.group_aprob_costo_cero'):
			fecha = datetime.now()
			for i in self:
				if not i.corriovalorizado:
					raise UserError("Validar Valorizado Dolar primero para luego ver si existe casos de costo Dolar 0 y aprobar dichos costos")
				i.state = 'val_dol'
				i.user_aprob_costo_cero_id_dolar = self.env.user.id
				i.fecha_aprob_costo_cero_dolar = fecha
		else:
			raise UserError("Aprobaciones permitidas para el grupo 'Cierre Kardex - Aprobar Costo 0'")










	def aprobar_oper_sunat(self):
		if self.env.user.has_group('kardex_save_period_valorized.group_aprob_sunat_oper'):
			if len(self.lineas_cero)>0:
				raise UserError("No se puede aprobar al siguiente estado, Presentan Saldos Negativos")
			if len(self.lineas)==0:
				raise UserError("No se Validar Fisico desde Aqui")
			fecha = datetime.now()
			for i in self:
				i.state = 'first'
				i.user_aprob_sunat_oper = self.env.user.id
				i.fecha_aprob_sunat_oper = fecha
		else:
			raise UserError("Aprobaciones permitidas para el grupo 'Cierre Kardex - Aprobar Operación Sunat'")





#kardex_fields_it