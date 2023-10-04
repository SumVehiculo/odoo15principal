# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPeriod(models.Model):
	_name = 'hr.period'
	_description = 'Hr Period'
	_inherit = ['mail.thread']
	
	code = fields.Char(string='Codigo',tracking=True)
	name = fields.Char(string='Nombre',tracking=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',tracking=True)
	date_start = fields.Date(string='Fecha de Inicio',tracking=True)
	date_end = fields.Date(string='Fecha de Fin',tracking=True)

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search(['|',('code', '=', name),('name','=',name)] + args, limit=limit)
		if not recs:
			recs = self.search(['|',('code', operator, name),('name',operator,name)] + args, limit=limit)
		return recs.name_get()

	# def name_get(self):
	# 	result = []
	# 	for einv in self:
	# 		result.append([einv.id,einv.code])
	# 	return result

	@api.constrains('code')
	def _verify_code(selfs):
		for self in selfs:
			if len(self.env['hr.period'].search([('code','=',self.code)],limit=2)) > 1:
				raise UserError('No pueden existir dos periodos con el mismo codigo')