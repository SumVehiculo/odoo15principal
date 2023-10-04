
from odoo import models, api

class AccountMove(models.Model):
	_inherit = 'account.move'

	def import_lines(self):
		wizard = self.env['import.move.line.wizard'].create({
			'move_id':self.id
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_move_line_wizard_form' % module)
		return {
			'name':u'Importar Apuntes Contables',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.move.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
