# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class ExchangeDiffConfig(models.Model):
	_name = 'exchange.diff.config'		

	name = fields.Char(default='Configuracion Diferencias de Cambio')
	profit_account_id = fields.Many2one('account.account', string='Cuenta Ganancia')
	loss_account_id = fields.Many2one('account.account', string='Cuenta Perdida')
	line_ids = fields.One2many('exchange.diff.config.line', 'line_id', 'Lineas')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.constrains('company_id')
	def _check_unique_exchange(self):
		self.env.cr.execute("""select id from exchange_diff_config where company_id = %s""" % (str(self.company_id.id)))
		res = self.env.cr.dictfetchall()
		if len(res) > 1:
			raise UserError(u"Ya existen Tipos de Cambio de Cierre para esta Compañía")
	
class ExchangeDiffConfigLine(models.Model):
	_name='exchange.diff.config.line'
	
	line_id = fields.Many2one('exchange.diff.config', 'Header')
	period_id = fields.Many2one('account.period', string='Periodo')
	compra = fields.Float(string='Compra', digits=(12,3))
	venta = fields.Float(string='Venta',digits=(12,3))
	move_id_global = fields.Many2one('account.move', string='Asiento Global')
	move_id_document = fields.Many2one('account.move', string='Asiento por Documento')

	#CREAR CONSTRAINT PARA SOLO UN PERIODO POR COMPAÑIA
	@api.constrains('period_id')
	def _check_unique_exchange(self):
		for line in self:
			line.env.cr.execute("""select period_id from exchange_diff_config_line where line_id = %s and period_id = %s""" % (str(line.line_id.id),str(line.period_id.id)))
			res = line.env.cr.dictfetchall()
			if len(res) > 1:
				raise UserError(u"Ya existe el periodo "+line.period_id.code+u" en los Tipos de Cambio de Cierre para esta Compañía")