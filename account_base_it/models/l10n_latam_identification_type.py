# -*- coding: utf-8 -*-

from odoo import models, fields, api

class L10nLatamIdentificationType(models.Model):
	_inherit = "l10n_latam.identification.type"

	code_sunat = fields.Char(string=u'Código SUNAT',size=2)