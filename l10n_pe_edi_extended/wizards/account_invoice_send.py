# -*- coding: utf-8 -*-
import requests
import base64

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange('template_id')
    def onchange_template_id(self):
        super(AccountInvoiceSend, self).onchange_template_id()
        for wizard in self:
            Attachment = self.env['ir.attachment']
            if wizard.template_id and wizard.composition_mode != 'mass_mail':
                invoice = self.env[wizard.composer_id.model].browse(wizard.composer_id.res_id)
                if invoice.l10n_pe_dte_is_einvoice:
                    conf = self.env['ir.config_parameter']
                    #pdf_format_odoo = bool(conf.sudo().get_param('account.l10n_pe_dte_pdf_use_odoo_%s' % invoice.company_id.id,False))
                    pdf_format_odoo = False
                    einvoice_attachments = []
                    attachment_old = wizard.composer_id.attachment_ids.ids
                    if invoice.l10n_pe_dte_pdf_file and not pdf_format_odoo:
                        if invoice.l10n_pe_dte_pdf_file.type=="url":
                            r = requests.get(invoice.l10n_pe_dte_pdf_file.url)
                            data_content = r.content
                            invoice.l10n_pe_dte_pdf_file.sudo().write({
                                'type': 'binary',
                                'datas': base64.encodebytes(data_content)
                            })
                        einvoice_attachments.append(invoice.l10n_pe_dte_pdf_file.id)
                        attachment_old = []
                    if invoice.l10n_pe_dte_cdr_file:
                        if invoice.l10n_pe_dte_cdr_file.type=="url":
                            r = requests.get(invoice.l10n_pe_dte_cdr_file.url)
                            data_content = r.content
                            invoice.l10n_pe_dte_cdr_file.sudo().write({
                                'name': invoice.l10n_pe_dte_cdr_file.name,
                                'type': 'binary',
                                'datas': base64.encodebytes(data_content)
                            })
                        einvoice_attachments.append(invoice.l10n_pe_dte_cdr_file.id)
                    if invoice.l10n_pe_dte_file:
                        if invoice.l10n_pe_dte_file.type=="url":
                            r = requests.get(invoice.l10n_pe_dte_file.url)
                            data_content = r.content
                            invoice.l10n_pe_dte_file.sudo().write({
                                'type': 'binary',
                                'datas': base64.encodebytes(data_content)
                            })
                        einvoice_attachments.append(invoice.l10n_pe_dte_file.id)

                    wizard.write({'attachment_ids': [(6, 0, attachment_old + einvoice_attachments)]})
