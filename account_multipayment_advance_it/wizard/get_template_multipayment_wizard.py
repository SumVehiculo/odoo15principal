# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class GetTemplateMultipaymentWizard(models.TransientModel):
	_name = "get.template.multipayment.wizard"
	
	multipayment_id = fields.Many2one('multipayment.advance.it',string=u'P. Múltiple')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	template = fields.Many2many('account.template.multipayment','account_get_template_multipayment_wizard_rel',string=u'Lineas para importar', required=True, 
	domain="[('company_id','=',company_id)]")
		
	def insert(self):
		vals=[]
		for temp in self.template:
			line = self.multipayment_id.lines_ids.filtered(lambda l: l.account_id.id == temp.account_id.id)
			if line:
				line.analytic_account_id = temp.analytic_account_id.id
				line.analytic_tag_id = temp.analytic_tag_id.id
			else:
				vals = {
					'main_id': self.multipayment_id.id,
					'account_id': temp.account_id.id,
					'analytic_account_id': temp.analytic_account_id.id,
					'analytic_tag_id': temp.analytic_tag_id.id,
				}
				self.env['multipayment.advance.it.line2'].create(vals)