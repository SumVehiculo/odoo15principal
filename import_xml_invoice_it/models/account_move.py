# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
	_inherit = "account.move"

	xml_import_code = fields.Many2one('import.xml.invoice.it',string='Codigo Importacion XML',ondelete="cascade",copy=False)


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	xml_import_code = fields.Many2one('import.xml.invoice.it',string='Codigo Importacion XML',copy=False)