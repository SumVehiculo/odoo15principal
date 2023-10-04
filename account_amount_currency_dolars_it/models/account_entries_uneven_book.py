# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import decimal

class AccountEntriesUnevenBook(models.Model):
	_name = 'account.entries.uneven.book'
	_auto = False
	
	move_id = fields.Many2one('account.move',string='Asiento')
	date = fields.Date(string='Fecha',related='move_id.date')
	journal_id = fields.Many2one('account.journal',related='move_id.journal_id',string='Diario')
	amount = fields.Float(string='Descuadre')

	def view_account_move(self):
		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.move_id.id,
		}
	
	def action_fix_move(self):
		param = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		if not param.profit_account_ed:
			raise UserError(u'No esta Configurada la Cuenta de Ganancias Diferencia de Cambio en sus Parametros Principales.')
		if not param.loss_account_ed:
			raise UserError(u'No esta Configurada la Cuenta de Pérdidas Diferencia de Cambio en sus Parametros Principales.')
		for move in self:
			sql = u"""
				INSERT INTO account_move_line (move_id,move_name,date,ref,parent_state,journal_id,company_id,company_currency_id,
				account_id,account_internal_type,account_root_id,sequence,name,quantity,reconciled,blocked,tax_exigible,tc,amount_c,is_adjustment) VALUES 
				(%d,'%s','%s','%s','%s',%d,%d,%d,%d,'%s',%d,10,'AJUSTE POR REDONDEO EN CONVERSIÓN',1,False,False,True,%0.4f,%0.2f,True)""" % (
					move.move_id.id,
					move.move_id.name,
					move.move_id.date.strftime('%Y/%m/%d'),
					move.move_id.ref,
					move.move_id.state,
					move.move_id.journal_id.id,
					move.move_id.company_id.id,
					move.move_id.company_id.currency_id.id,
					param.profit_account_ed.id if move.amount>0 else param.loss_account_ed.id,
					param.profit_account_ed.internal_type if move.amount>0 else param.loss_account_ed.internal_type,
					param.profit_account_ed.root_id.id if move.amount>0 else param.loss_account_ed.root_id.id,
					move.move_id.currency_rate,
					move.amount*-1
				)

			self.env.cr.execute(sql)
		return self.env['popup.it'].get_message('SE ACTUALIZARON CORRECTAMENTE LOS ASIENTOS DESCUADRADOS')