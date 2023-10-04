# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTypeIt(models.Model):
	_name = 'account.type.it'

	code = fields.Char(string='Codigo')
	name = fields.Char(string='Nombre')
	group_balance = fields.Selection([
									('B1','Activo Corriente.'),
									('B2','Activo no Corriente.'),
									('B3','Pasivo Corriente.'),
									('B4','Pasivo no Corriente.'),
									('B5','Patrimonio.')
									],string='Grupo Balance')
	group_nature = fields.Selection([
									('N1','Grupo 1'),
									('N2','Grupo 2'),
									('N3','Grupo 3'),
									('N4','Grupo 4'),
									('N5','Grupo 5'),
									('N6','Grupo 6'),
									('N7','Grupo 7'),
									('N8','Grupo 8')
									],string='Grupo Naturaleza')
	group_function = fields.Selection([
									('F1','Grupo 1'),
									('F2','Grupo 2'),
									('F3','Grupo 3'),
									('F4','Grupo 4'),
									('F5','Grupo 5'),
									('F6','Grupo 6')
									],string=u'Grupo Función')
	order_balance = fields.Integer(string='Orden de Balance')
	order_nature = fields.Integer(string='Orden de Naturaleza')
	order_function = fields.Integer(string=u'Orden de Función')

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
			name = einv.code + ' ' + einv.name
			result.append((einv.id, name))
		return result