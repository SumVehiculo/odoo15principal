# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPeriod(models.Model):
	_name = 'account.period'

	code = fields.Char(string='Codigo')
	name = fields.Char(string='Nombre')
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal')
	date_start = fields.Date(string='Fecha de Inicio')
	date_end = fields.Date(string='Fecha de Fin')
	close = fields.Boolean(string='Cerrado', default=False)
	is_opening_close = fields.Boolean(string=u'Apertura/Cierre',default=False)

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search(['|',('code', '=', name),('name','=',name)] + args, limit=limit)
		if not recs:
			recs = self.search(['|',('code', operator, name),('name',operator,name)] + args, limit=limit)
		return recs.name_get()

	def name_get(self):
		result = []
		for einv in self:
			result.append([einv.id,einv.code])
		return result

	_sql_constraints = [
		('code_uniq_period', 'unique (code)', 'No pueden existir dos periodos con el mismo codigo.'),
	]