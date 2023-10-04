# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
	_inherit = 'res.partner'

	##CONTROL DE DUPLICADOS##
	@api.constrains('vat','l10n_latam_identification_type_id','parent_id','company_id')
	def _check_unique_partner(self):
		for i in self:
			if not i.parent_id and i.vat:
				dom = [('vat', '=', i.vat), ('id', '!=', i.id)]
				if i.l10n_latam_identification_type_id:
					dom.append(('l10n_latam_identification_type_id','=',i.l10n_latam_identification_type_id.id))
				if i.company_id:
					dom.append('|')
					dom.append(('company_id','=',i.company_id.id))
					dom.append(('company_id','=',False))
				else:
					dom.append(('company_id','=',False))

				partners = self.env['res.partner'].sudo().search(dom)
				if len(partners) > 0:
					raise UserError('Error - VAT=%s ya es usado en contacto %s(%d)'%(i.vat, partners[0].name,partners[0].id))

	@api.model
	def create(self, values):
		# Add code here
		res = super(ResPartner, self).create(values)
		res._check_unique_partner()
		return res
	
	def write(self, vals):
		res = True
		for part in self:
			res |= super(ResPartner, part).write(vals)
			if 'vat' in vals or 'l10n_latam_identification_type_id' in vals or 'parent_id' in vals or 'company_id' in vals:
				part._check_unique_partner()
		return res
	
	#def copy_data(self, default=None):
	#	if default is None:
	#		default = {}
	#	default['vat'] = False
	#	default['l10n_latam_identification_type_id'] = self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False).id
	#	return super(ResPartner, self).copy_data(default)
	
	#@api.returns('self', lambda value: value.id)

	def copy(self, default=None):
		default = dict(default or {})
		default['l10n_latam_identification_type_id'] = self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False).id
		default['vat'] = None
		return super(ResPartner, self).copy(default=default)