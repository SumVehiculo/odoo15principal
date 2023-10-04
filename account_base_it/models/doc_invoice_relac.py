# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DocInvoiceRelac(models.Model):
	_name = 'doc.invoice.relac'

	move_id = fields.Many2one('account.move')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='TD')
	date = fields.Date(string='Fecha de Emision')
	nro_comprobante = fields.Char(string='Comprobante',size=40)
	amount_currency = fields.Float(string='Monto Me',digits=(16, 2))
	amount = fields.Float(string='Total Mn',digits=(16, 2))
	bas_amount = fields.Float(string='Base Imponible',digits=(16, 2))
	tax_amount = fields.Float(string='IGV',digits=(16, 2))