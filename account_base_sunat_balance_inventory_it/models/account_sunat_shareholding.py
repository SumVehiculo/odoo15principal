# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountSunatShareholding(models.Model):
	_name = 'account.sunat.shareholding'
	_description = 'Account Sunat Shareholding'	

	@api.depends('date')
	def _get_name(self):
		for i in self:
			i.name = str(i.date)

	name = fields.Char(compute=_get_name,store=True)
	date = fields.Date(string='Periodo',required=True)
	partner_id = fields.Many2one('res.partner',string=u'Socio',required=True)
	type = fields.Selection([('01',u'ACCIONES CON DERECHO A VOTO'),
								('02',u'ACCIONES SIN DERECHO A VOTO'),
								('03',u'PARTICIPACIONES'),
								('04',u'OTROS')],string='Tipo',default='01')
	num_acciones = fields.Integer(string=u'Número de Acciones')
	percentage = fields.Float(string=u'Porcentaje de Participación')
	state = fields.Selection([('1',u'La operación corresponde al periodo.'),
								('8',u'La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
								('9',u'La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string='Estado PLE',default='1')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)