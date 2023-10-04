from odoo import models, fields, api
class EinvoiceCatalog13(models.Model):
	_name = 'einvoice.catalog.13'
	name = fields.Char(string='Nombre')
	code = fields.Char(string='Codigo',size=4)