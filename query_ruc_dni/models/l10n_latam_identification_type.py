# -*- coding: utf-8 -*-

from odoo import models, fields, api
#SE ESTA COPIANDO LOS CAMPOS DEL account_base_it PARA QUE EL MODULO QUERY_RUC_DNI SEA LIBRE E INDEPENDIENTE

class L10nLatamIdentificationType(models.Model):
	_inherit = "l10n_latam.identification.type"

	code_sunat = fields.Char(string=u'Código SUNAT',size=2)