# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class UpdateRateDolarsWizard(models.TransientModel):
	_name = 'update.rate.dolars.wizard'

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string='Periodo')

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		return fiscal_year.id if fiscal_year else None

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())
	update_rate = fields.Boolean(string='Actualizar Tipos de Cambio',default=False)

	def convert(self):
		param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		usd = self.env.ref('base.USD')

		self.env.cr.execute("""
		DELETE FROM account_move_line WHERE id in (
		SELECT aml.id
		FROM account_move_line aml
		LEFT JOIN account_move am on am.id = aml.move_id
		WHERE (am.date BETWEEN '{date_from}' AND '{date_to}') AND am.company_id = {company_id} 
		AND aml.is_adjustment = TRUE)
	""".format(
		company_id = self.company_id.id,
		date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
		date_to = self.period_id.date_end.strftime('%Y/%m/%d')))
		
		if self.update_rate:
			self.env.cr.execute("""
				UPDATE account_move SET currency_rate = T.tipo_cambio FROM (

				SELECT rc.sale_type AS tipo_cambio, am.id  AS move_id
				FROM account_move am
				LEFT JOIN (SELECT DISTINCT ON (name) name,currency_id, rate, sale_type FROM res_currency_rate where currency_id = {usd}
								ORDER BY name) rc on rc.name = (CASE WHEN am.type = 'entry' THEN am.date ELSE am.invoice_date END)
				WHERE (am.date BETWEEN '{date_from}' AND '{date_to}') AND am.company_id = {company_id}

				)T WHERE account_move.id = T.move_id AND account_move.currency_rate in (0,1)

			""".format(
				usd = usd.id,
				company_id = self.company_id.id,
				date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_id.date_end.strftime('%Y/%m/%d')
			))

			self.env.cr.execute("""
				UPDATE account_move_line SET tc = T.tipo_cambio FROM (

				SELECT am.currency_rate AS tipo_cambio, aml.id AS move_line_id
				FROM account_move_line aml
				LEFT JOIN account_move am on am.id = aml.move_id
				WHERE (am.date BETWEEN '{date_from}' AND '{date_to}') AND am.company_id = {company_id} {journal_ids}
				)T WHERE account_move_line.id = T.move_line_id AND account_move_line.tc in (0,1)

			""".format(
				company_id = self.company_id.id,
				date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_id.date_end.strftime('%Y/%m/%d'),
				journal_ids = (("AND am.journal_id not in (%s)"%(','.join(str(i.id) for i in param.journal_exchange_exclude))) if param.journal_exchange_exclude else "")
			))
			
		if param.journal_exchange_exclude:
			self.env.cr.execute("""
				UPDATE account_move_line SET amount_c = 0, tc = 1 WHERE id in (

				SELECT aml.id AS move_line_id
				FROM account_move_line aml
				LEFT JOIN account_move am on am.id = aml.move_id
				WHERE (am.date BETWEEN '{date_from}' AND '{date_to}') AND am.company_id = {company_id} AND am.journal_id in ({journal_ids}))
			""".format(
				usd = usd.id,
				company_id = self.company_id.id,
				date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_id.date_end.strftime('%Y/%m/%d'),
				journal_ids = ','.join(str(i.id) for i in param.journal_exchange_exclude)
			))

		self.env.cr.execute("""
			UPDATE account_move_line SET amount_c = round(T.amount_c,2) FROM (

			SELECT CASE WHEN aml.currency_id = {usd} THEN aml.amount_currency ELSE (coalesce(aml.debit,0)-coalesce(aml.credit,0))/aml.tc END AS amount_c, aml.id AS move_line_id
			FROM account_move_line aml
			LEFT JOIN account_move am on am.id = aml.move_id
			WHERE (am.date BETWEEN '{date_from}' AND '{date_to}') AND am.company_id = {company_id} {journal_ids} and (aml.amount_c is null or aml.amount_c = 0)
			)T WHERE account_move_line.id = T.move_line_id

		""".format(
			usd = usd.id,
			company_id = self.company_id.id,
			date_from = self.period_id.date_start.strftime('%Y/%m/%d'),
			date_to = self.period_id.date_end.strftime('%Y/%m/%d'),
			journal_ids = (("AND am.journal_id not in (%s)"%(','.join(str(i.id) for i in param.journal_exchange_exclude))) if param.journal_exchange_exclude else "")
		))
		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CORRECTAMENTE LOS MONTOS EN MONEDA EXTRANJERA.')
