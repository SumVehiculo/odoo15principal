# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AssetDepreciationConfirmationWizard(models.TransientModel):
	_name = "asset.depreciation.confirmation.wizard"
	_description = "asset.depreciation.confirmation.wizard"

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)
	period = fields.Many2one('account.period',string=u'Periodo',required=True)

	def asset_compute(self):
		destination_journal = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).destination_journal

		if not destination_journal:
			raise UserError(u'No existe un Diario Asiento Automático configurado en Parametros Generales de Contabilidad para su Compañía.')
		move_id = self.move_from_period(self.period,destination_journal)
		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move_id.id,
		}

	def move_from_period(self,period, destination_journal):
		self.env.cr.execute("""select account_analytic_id, account_analytic_tag_id, account_depreciation_expense_id as account_id, sum(valor_dep) as debit, 0 as credit, (select id from l10n_latam_document_type where code = '00' limit 1) as type_document_id
			from get_activos('%s','%s',%d)
			group by account_analytic_id, account_analytic_tag_id, account_depreciation_expense_id
			union all 
			select null as account_analytic_id, null as account_analytic_tag_id, account_depreciation_id as account_id, 0 as debit, sum(valor_dep) as credit, (select id from l10n_latam_document_type where code = '00' limit 1) as type_document_id
			from get_activos('%s','%s',%d)
			group by account_depreciation_id"""%(period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			self.company_id.id,
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			self.company_id.id))

		res = self.env.cr.dictfetchall()

		lineas = []

		for elemnt in res:
			tag_ids = []
			if elemnt['account_analytic_tag_id']:
				tag_ids.append(elemnt['account_analytic_tag_id'])

			vals = (0,0,{
				'analytic_account_id': elemnt['account_analytic_id'],
				'analytic_tag_ids':([(6,0,tag_ids)]),
				'account_id': elemnt['account_id'],
				'name': u'DEPRECIACIÓN '+str('{:02d}'.format(period.date_start.month))+'-'+period.fiscal_year_id.name,
				'debit': elemnt['debit'],
				'credit': elemnt['credit'],
				'type_document_id': elemnt['type_document_id'],
				'nro_comp': 'dep-'+str('{:02d}'.format(period.date_start.month))+period.fiscal_year_id.name,
				'tc':1,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)

		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': destination_journal.id,
			'date': period.date_end,
			'ref': 'dep-'+str('{:02d}'.format(period.date_start.month))+period.fiscal_year_id.name,
			'glosa': u'DEPRECIACIÓN DE ACTIVOS DE '+str('{:02d}'.format(period.date_start.month))+'-'+period.fiscal_year_id.name,
			'line_ids':lineas})

		move_id.post()

		asset_move = self.env['account.asset.move.it'].search([('period_id','=',period.id),('company_id','=',self.company_id.id)],limit=1)
		if asset_move:
			if asset_move.move_id:
				asset_move.move_id.button_cancel()
				asset_move.move_id.line_ids.unlink()
				asset_move.move_id.name = "/"
				asset_move.move_id.unlink()
			asset_move.move_id = move_id.id
		else:
			asset_move = self.env['account.asset.move.it'].create({
			'company_id': self.company_id.id,
			'period_id': period.id,
			'move_id': move_id.id})
		
		return move_id