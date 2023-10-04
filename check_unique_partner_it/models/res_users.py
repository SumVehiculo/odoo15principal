# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ResUsers(models.Model):
	_inherit = 'res.users'

	def copy(self, default=None):
		default = dict(default or {})
		default['l10n_latam_identification_type_id'] = self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False).id
		default['vat'] = None
		return super(ResUsers, self).copy(default=default)