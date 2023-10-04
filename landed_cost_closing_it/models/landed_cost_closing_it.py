# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class LandedCostClosingIt(models.Model):
	_name = 'landed.cost.closing.it'
	_description = 'Landed Cost Closing It'		

	@api.depends('period_id')
	def _get_name(self):
		for i in self:
			i.name = i.period_id.name

	name = fields.Char(compute=_get_name,store=True)
	period_id = fields.Many2one('account.period',string='Periodo',required=True)
	date_start = fields.Date(string='Fecha de Inicio',related='period_id.date_start')
	date_end = fields.Date(string='Fecha de Fin',related='period_id.date_end')
	state = fields.Selection([('draft','Abierto'),('done','Cerrado')],string='Estado',default='draft')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	_sql_constraints = [
		('company_period_uniq', 'unique(period_id, company_id)',
		 'Ya existe el Cierre GV en este periodo para esta Compañia'),
	]

	def close_period(self):
		for period in self:
			self.env.cr.execute("""SELECT id from landed_cost_it where company_id = %d
			and ((date_kardex::timestamp - interval '5' hour)::date between '%s' and '%s') 
			and state = 'draft'"""%(period.company_id.id,period.period_id.date_start.strftime('%Y/%m/%d'),
			period.period_id.date_end.strftime('%Y/%m/%d')))
			res = self.env.cr.dictfetchall()
			if len(res)>0:
				raise UserError('Para cerrar un periodo, primero debe establecer como "Finalizado" todos los Gastos Vinculados relacionados con el periodo.')
			period.state = 'done'

	def open_period(self):
		for period in self:
			period.state = 'draft'