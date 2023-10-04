# -*- coding: utf-8 -*-
from odoo import models, fields

class CompanyBranchAddress(models.Model):
	_inherit = 'res.company.branch.address'

	l10n_pe_dte_itgrupo_serial_ids = fields.One2many('it.invoice.serie', 'company_branch_address_id', string='Series')
    
class ItInvoiceSerie(models.Model):
    _inherit = 'it.invoice.serie'

    company_branch_address_id = fields.Many2one('res.company.branch.address', string='Establecimiento anexo')