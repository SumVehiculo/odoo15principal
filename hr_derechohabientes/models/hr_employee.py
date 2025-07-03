# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_resource
import base64
import subprocess
import sys
from datetime import date
from dateutil.relativedelta import relativedelta

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from suds.client import Client
except:
	install('suds-py3')

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	derechohabientes_lines = fields.One2many('hr.derechohabientes','employee_id','Derechohabientes')

	def asignacion_familiar(self):
		for i in self.env['hr.employee'].sudo().search([]):
			count_hijos = 0 
			for l in i.derechohabientes_lines:
				if l.parents == "hij":
					if (l.age <= 18) or (l.age <= 24 and l.study == True):
						count_hijos += 1
			i.children = count_hijos		
		return 

	def asignacion_familiar_actual(self):
		for i in self:
			count_hijos = 0 
			for l in i.derechohabientes_lines:
				if l.parents == "hij":
					if (l.age <= 18) or (l.age <= 24 and l.study == True):
						count_hijos += 1
			i.children = count_hijos		
		return 


class HrDerechohabientes(models.Model):
	_name = 'hr.derechohabientes'
	_description = 'Hr Derechohabientes'

	name = fields.Char(string='Nombres y Apellidos')
	l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type', string="T. Doc", default=5)
	vat = fields.Char(string='Documento de Identidad')

	parents = fields.Selection([
		('conyuge', 'Conyuge'),
		('espos', 'Esposo/a'),
		('hij', 'Hijo/a'),
		('madre', 'Madre'),
		('padre', 'Padre')
	],string='Parentesco')
	birthday = fields.Date('Fecha de Nacimiento')
	age = fields.Integer(string='Edad', compute='_get_edad')
	study = fields.Boolean(string="Cursando Estudios", default=False)
	employee_id = fields.Many2one('hr.employee')

	@api.depends('birthday')
	def _get_edad(self):
		for record in self:
			if record.age or record.birthday:
				edad = date.today().year - record.birthday.year
				cumpleanios = record.birthday + relativedelta(years=edad)
				if cumpleanios > date.today():
					edad = edad - 1
				record.age = edad

	@api.model
	def create(self,vals):
		t = super(HrDerechohabientes, self).create(vals)
		t.employee_id.asignacion_familiar_actual()
		return t

	
	def write(self,vals):
		t = super(HrDerechohabientes, self).write(vals)
		self.employee_id.asignacion_familiar_actual()
		return t


