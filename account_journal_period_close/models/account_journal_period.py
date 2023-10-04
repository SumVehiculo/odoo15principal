# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountJournalPeriod(models.Model):
	_name = 'account.journal.period'
	_description = 'Account Journal Period'		

	@api.depends('period_id')
	def _get_name(self):
		for i in self:
			i.name = i.period_id.name

	name = fields.Char(compute=_get_name,store=True)
	period_id = fields.Many2one('account.period',string='Periodo',required=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',related='period_id.fiscal_year_id')
	date_start = fields.Date(string='Fecha de Inicio',related='period_id.date_start')
	date_end = fields.Date(string='Fecha de Fin',related='period_id.date_end')
	line_ids = fields.One2many('account.journal.period.line', 'main_id', 'Lineas')
	state = fields.Selection([('draft','Abierto'),('done','Cerrado')],string='Estado',default='draft')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	_sql_constraints = [
		('company_period_uniq', 'unique(period_id, company_id)',
		 'Ya existe el Periodo para esta Compañia'),
	]

	def close_period(self):
		for period in self:
			draft_move_ids = self.env['account.move'].search([('date','>=',period.period_id.date_start),('date','<=',period.period_id.date_end),('state','=','draft'),('company_id','=',period.company_id.id)])
			if draft_move_ids:
				raise UserError('Para cerrar un periodo, primero debe publicar entradas de diario relacionadas con el periodo.')
			period.state = 'done'

	def open_period(self):
		for period in self:
			period.state = 'draft'

	def add_all_journals(self):
		for period in self:
			journals = []
			for line in period.line_ids:
				journals.append(line.journal_id.id)
			
			journal_append = self.env['account.journal'].search([('id','not in',journals),('company_id','=',period.company_id.id)])
			for journal in journal_append:
				self.env['account.journal.period.line'].create({
					'main_id': period.id,
					'journal_id': journal.id
				})

	
class ExchangeDiffConfigLine(models.Model):
	_name='account.journal.period.line'
	_description = 'Account Journal Period Line'	
	
	main_id = fields.Many2one('account.journal.period', 'Header')
	period_id = fields.Many2one('account.period', string='Periodo',related='main_id.period_id',store=True)
	journal_id = fields.Many2one('account.journal',string='Diario',required=True)
	type = fields.Selection(related='journal_id.type',string='Tipo')
	state = fields.Selection([('draft','Abierto'),('done','Cerrado')],string='Estado',default='draft')

	_sql_constraints = [
		('journal_period_uniq', 'unique(period_id, journal_id)',
		 'No puede haber el mismo diario en el mismo Periodo'),
	]

	def action_done(self):
		for line in self:
			draft_move_ids = self.env['account.move'].search([('date','>=',line.period_id.date_start),('date','<=',line.period_id.date_end),('state','=','draft'),('journal_id','=',line.journal_id.id),('company_id','=',line.main_id.company_id.id)])
			if draft_move_ids:
				raise UserError('Para cerrar un diario, primero debe publicar entradas de diario relacionadas.')

			line.state = 'done'

	def action_draft(self):
		for line in self:
			line.state = 'draft'