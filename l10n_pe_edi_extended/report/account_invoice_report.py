# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ReportEinvoice(models.AbstractModel):
    _name = 'report.l10n_pe_edi_extended.report_einvoice'
    _description = 'Account report with payment lines'
    _inherit = 'report.account.report_invoice_with_payments'

    @api.model
    def _get_report_values(self, docids, data=None):
        rslt = super()._get_report_values(docids, data)
        rslt['report_type'] = data.get('report_type') if data else ''
        return rslt