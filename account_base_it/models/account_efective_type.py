# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountEfectiveType(models.Model):
	_name = 'account.efective.type'

	code = fields.Char(string='Codigo')
	name = fields.Char(string='Concepto',required=True)
	group = fields.Selection([
							('E1',u'Ingresos de Operación'),
							('E2',u'Egresos de Operación'),
							('E3',u'Ingresos de Inversión'),
							('E4',u'Egresos de Inversión'),
							('E5',u'Ingresos de Financiamiento'),
							('E6',u'Engresos de Financiamiento'),
							('E7',u'Saldo Inicial'),
							('E8',u'Diferencia de Cambio')
							],string='Grupo')
	order = fields.Integer(string='Orden')

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
			result.append([einv.id,einv.name])
		return result