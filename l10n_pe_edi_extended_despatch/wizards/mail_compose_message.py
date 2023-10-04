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
        if model == 'logistic.despatch':
            despatch = self.env[model].browse(res_id)
            if despatch.l10n_pe_dte_is_einvoice:
                conf = self.env['ir.config_parameter']
                pdf_format_odoo = bool(conf.sudo().get_param('logistic.l10n_pe_dte_pdf_use_odoo_%s' % despatch.company_id.id,False))
                einvoice_attachments = []
                attachment_old = res['value']['attachment_ids'][0][2]
                if despatch.l10n_pe_dte_pdf_file and not pdf_format_odoo:
                    if despatch.l10n_pe_dte_pdf_file.type=="url":
                        r = requests.get(despatch.l10n_pe_dte_pdf_file.url)
                        data_content = r.content
                        despatch.l10n_pe_dte_pdf_file.write({
                            'type': 'binary',
                            'datas': base64.encodebytes(data_content)
                        })
                    einvoice_attachments.append(despatch.l10n_pe_dte_pdf_file.id)
                    attachment_old = []
                if despatch.l10n_pe_dte_cdr_file:
                    if despatch.l10n_pe_dte_cdr_file.type=="url":
                        r = requests.get(despatch.l10n_pe_dte_cdr_file.url)
                        data_content = r.content
                        despatch.l10n_pe_dte_cdr_file.write({
                            'name': despatch.l10n_pe_dte_cdr_file.name,
                            'type': 'binary',
                            'datas': base64.encodebytes(data_content)
                        })
                    einvoice_attachments.append(despatch.l10n_pe_dte_cdr_file.id)
                if despatch.l10n_pe_dte_file:
                    if despatch.l10n_pe_dte_file.type=="url":
                        r = requests.get(despatch.l10n_pe_dte_file.url)
                        data_content = r.content
                        despatch.l10n_pe_dte_file.write({
                            'type': 'binary',
                            'datas': base64.encodebytes(data_content)
                        })
                    einvoice_attachments.append(despatch.l10n_pe_dte_file.id)
                    res['value']['attachment_ids'] = [(6, 0, attachment_old + einvoice_attachments)]
        return res