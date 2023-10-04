from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
class account_move(models.Model):
	_inherit = 'account.move'

	personalizadas_id = fields.Many2one(
		'account.personalizadas',
		string='Cuenta Personalizadas',
		)
	cuneta_p_p = fields.Boolean(string="Cuenta de pago personalizada")



	@api.onchange('personalizadas_id')
	def actulizar_cuentas_personalizadas(self):
		for i in self:			
			if i.state == "draft":
				if i.personalizadas_id:
					cuenta = self.env['account.personalizadas'].search([('id','=',i.personalizadas_id.id)],limit=1)			                     
					if i.move_type == 'out_invoice':   					
						if i.line_ids:  
							for lines in i.line_ids:
								if lines.account_id.internal_type == 'receivable':                               
									if i.currency_id.name == 'PEN':
										lines.account_id = cuenta.cuenta_mn_id.id
									else:
										lines.account_id = cuenta.cuenta_me_id.id
								
						else:
							raise UserError ("No cuenta con apuntes contables")
					if i.move_type == 'in_invoice':                    
						if i.line_ids:  
							for lines in i.line_ids:
								if lines.account_id.internal_type == 'payable':
									if i.currency_id.name == 'PEN':
										lines.account_id = cuenta.cuenta_mn_id.id
									else:
										lines.account_id = cuenta.cuenta_me_id.id
						else:
							raise UserError ("No cuenta con apuntes contables")
			else:
				raise UserError ("SOLO SE PUEDE ACTUALIZAR LA CUENTA EN EL ESTADO BORRADOR")
			
			#return self.env['popup.it'].get_message('SE REALIZÓ EL CAMBIO DE CUENTA')
