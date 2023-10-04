# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime
class AccountMove(models.Model):
	_inherit = "account.move"
	

	updated_rate = fields.Boolean(compute="_compute_updated_rate")




	@api.depends('partner_id','l10n_latam_document_type_id','ref','glosa','invoice_date')
	def _compute_updated_rate(self):
		for record in self:				
			import datetime
			record.updated_rate = False			
			for companys in self.env['res.company'].sudo().search([]):
				fecha_actual = datetime.datetime.now()
				type_now=self.env['res.currency.rate'].sudo().search([('name','=',fecha_actual.date()),('company_id','=',companys.id)])
				if not type_now:
					if record.partner_id and record.l10n_latam_document_type_id and record.ref and record.glosa and record.invoice_date:			
						record.updated_rate = True
				

				
	
	def get_verify_type_change(self):
			for i in self:
				import datetime
				updated = True			
				for companys in self.env['res.company'].sudo().search([]):
					fecha_actual = datetime.datetime.now()
					type_now=self.env['res.currency.rate'].sudo().search([('name','=',fecha_actual.date()),('company_id','=',companys.id)])
					if not type_now:					
						updated = False
				if updated == False:							
					context = {'invoice_id': i.id,'default_company_ids': self.env['res.company'].sudo().search([]).ids}
					return {
								'name': 'Actualizar Tipo Cambio',
								'type': 'ir.actions.act_window',
								'res_model': 'currency.rate.update.all.now',
								'view_id': self.env.ref('update_currency_rate_it.currency_rate_update_all_now_form').id,
								'view_mode': 'form',
								'view_type': 'form',
								'context': context,
								'target':'new'
							}
				else:
					return True