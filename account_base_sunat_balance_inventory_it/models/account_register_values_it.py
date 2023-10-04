# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountRegisterValuesIt(models.Model):
	_name = 'account.register.values.it'
	_description = 'Account Register Values It'

	code = fields.Char(string='Codigo Titulo')
	name = fields.Char(string='Valor Nominal')
	qty = fields.Float(string=u'Cantidad de Títulos')
	costo = fields.Float(string=u'Valor en Libros - Costo total de los Títulos')
	provision = fields.Float(string=u'Valor en Libros - Provisión total de los Títulos')
	date = fields.Date(string='Fecha')
	partner_id = fields.Many2one('res.partner',string='Partner')
	move_id = fields.Many2one('account.move',string='Asiento')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	def crear_asiento(self):
		if self.move_id:
			raise UserError(u'Ya existe un asiento, primero tiene que eliminarlo.')

		miscellaneous_journal = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).destination_journal

		if not miscellaneous_journal:
			raise UserError(u'No existe un Diario Asientos Automáticos configurado en Parametros Generales de Contabilidad para su Compañía.')

		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': miscellaneous_journal.id,
			'date': self.date,
			'ref': self.code,
			'glosa': self.code,
		})

		self.move_id = move_id