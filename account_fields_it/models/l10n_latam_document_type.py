# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class L10nLatamDocumentType(models.Model):
	_inherit = 'l10n_latam.document.type'
	_order = 'code asc'

	digits_serie = fields.Integer(string='Digitos Serie')
	digits_number = fields.Integer(string='Digitos Numero')
	pse_code = fields.Char(string='Codigo de Facturador')