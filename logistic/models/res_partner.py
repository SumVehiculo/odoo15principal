# -*- encoding: utf-8 -*-
from odoo import fields, api, models, _
import logging
log = logging.getLogger(__name__)


class ResPartner(models.Model):
	_inherit = 'res.partner'

	logistic_is_driver = fields.Boolean(string='Is Vehicle Driver?')
	logistic_license_number = fields.Char(string='Driver License')