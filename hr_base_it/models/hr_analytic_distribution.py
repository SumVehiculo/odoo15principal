# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrAnalyticDistribution(models.Model):
	_name = 'hr.analytic.distribution'
	_description = 'Analytic Distribution'

	name = fields.Char(string='Codigo', required=True)
	company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id, required=True)
	description = fields.Char(string='Descripcion')
	line_ids = fields.One2many('hr.analytic.distribution.line', 'distribution_id')

	@api.constrains('line_ids')
	def check_percent(self):
		if sum(self.line_ids.mapped('percent')) != 100:
			raise UserError('La suma de los porcentajes de las lineas debe ser siempre 100%')

	def name_get(self):
		result = []
		for distribution in self:
			name = '%s - %s' % ((distribution.name or '').strip(), (distribution.description or '').strip(),)
			result.append([distribution.id, name])
		return result

class HrAnalyticDistributionLine(models.Model):
	_name = 'hr.analytic.distribution.line'
	_description = 'Analytic Distribution Line'
	_rec_name = 'analytic_id'

	distribution_id = fields.Many2one('hr.analytic.distribution', ondelete='cascade')
	analytic_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica', required=True)
	percent = fields.Float(string='%', required=True)
