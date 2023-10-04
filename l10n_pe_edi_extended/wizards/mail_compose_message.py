# -*- coding: utf-8 -*-

import base64
import requests
import re

from odoo import _, api, fields, models, SUPERUSER_ID, tools
from odoo.tools import pycompat
from odoo.tools.safe_eval import safe_eval

import logging
log = logging.getLogger(__name__)


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        res = super(MailComposer, self).onchange_template_id(
            template_id, composition_mode, model, res_id)
        if model == 'account.move':
            invoice = self.env[model].browse(res_id)
            if invoice.l10n_pe_dte_is_einvoice:
                conf = self.env['ir.config_parameter']
                pdf_format_odoo = bool(conf.get_param('account.l10n_pe_dte_pdf_use_odoo_%s' % invoice.company_id.id,False))
                einvoice_attachments = []
                attachment_old = res['value']['attachment_ids'][0][2]
                if invoice.l10n_pe_dte_pdf_file and not pdf_format_odoo:
                    if invoice.l10n_pe_dte_pdf_file.type=="url":
                        r = requests.get(invoice.l10n_pe_dte_pdf_file.url)
                        data_content = r.content
                        invoice.l10n_pe_dte_pdf_file.write({
                            'type': 'binary',
                            'datas': base64.encodebytes(data_content)
                        })
                    einvoice_attachments.append(invoice.l10n_pe_dte_pdf_file.id)
                    attachment_old = []
                if invoice.l10n_pe_dte_cdr_file:
                    if invoice.l10n_pe_dte_cdr_file.type=="url":
                        r = requests.get(invoice.l10n_pe_dte_cdr_file.url)
                        data_content = r.content
                        invoice.l10n_pe_dte_cdr_file.write({
                            'name': invoice.l10n_pe_dte_cdr_file.name.replace('.xml','.zip'),
                            'type': 'binary',
                            'datas': base64.encodebytes(data_content)
                        })
                    einvoice_attachments.append(invoice.l10n_pe_dte_cdr_file.id)
                if invoice.l10n_pe_dte_file:
                    if invoice.l10n_pe_dte_file.type=="url":
                        r = requests.get(invoice.l10n_pe_dte_file.url)
                        data_content = r.content
                        invoice.l10n_pe_dte_file.write({
                            'type': 'binary',
                            'datas': base64.encodebytes(data_content)
                        })
                    einvoice_attachments.append(invoice.l10n_pe_dte_file.id)
                    res['value']['attachment_ids'] = [(6, 0, attachment_old + einvoice_attachments)]
        return res