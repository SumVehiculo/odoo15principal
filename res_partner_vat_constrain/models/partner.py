# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class res_partner(models.Model):
	_inherit = 'res.partner'


	@api.constrains('l10n_latam_identification_type_id','vat','company_id','parent_id')
	def _verify_vat_unique_per_company(self):
		for i in self:
			if i.l10n_latam_identification_type_id.id and i.vat and not i.parent_id.id:
				if not i.company_id.id:
					for reps in i.env["res.partner"].sudo().search([("l10n_latam_identification_type_id","=",i.l10n_latam_identification_type_id.id),("vat","=",i.vat)]):
						if reps.id != i.id:
							raise UserError("Contactos con Tipo de identificacion repetido: "+str(reps.name))
				else:
					for reps in i.env["res.partner"].sudo().search([("l10n_latam_identification_type_id","=",i.l10n_latam_identification_type_id.id),("vat","=",i.vat),"|",("company_id","=",i.company_id.id),("company_id","=",False)]):
						if reps.id != i.id:
							raise UserError("Contactos con Tipo de identificacion repetido: "+str(reps.name))
