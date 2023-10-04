
from odoo import models, api

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def import_lines(self):
		wizard = self.env['import.statement.line.wizard'].create({
			'statement_id':self.id
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_statement_line_wizard_form' % module)
		return {
			'name':u'Importador de Lineas de Extracto',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.statement.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
