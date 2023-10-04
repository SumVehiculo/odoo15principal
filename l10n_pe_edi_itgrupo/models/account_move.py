# -*- coding: utf-8 -*-
from odoo import api, models, fields

import logging
log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_l10n_pe_dte_extra_fields(self):
        res = super(AccountMove, self)._get_l10n_pe_dte_extra_fields()
        if self.serie_id.company_branch_address_id:
            res['company_branch_address_id'] = self.serie_id.company_branch_address_id.id
        return res

    def _l10n_pe_prepare_dte(self):
        res = super(AccountMove, self)._l10n_pe_prepare_dte()
        seq_split = self.ref.split('-')
        if len(seq_split)==2:
            dte_serial = seq_split[0]
            dte_number = seq_split[1]
        res['dte_serial'] = dte_serial
        res['dte_number'] = dte_number
        res['currency_rate'] = self.currency_rate
        res['invoice_type_code'] = self.l10n_latam_document_type_id.code
        if res['invoice_type_code']=='07' or res['invoice_type_code']=='08':
            #res['credit_note_type'] = self.doc_invoice_relac[0].
            if res['invoice_type_code']=='07':
                res['credit_note_type'] = self.l10n_pe_dte_credit_note_type
            elif res['invoice_type_code']=='08':
                res['debit_note_type'] = self.l10n_pe_dte_debit_note_type
            res['rectification_ref_type'] = self.doc_invoice_relac[0].type_document_id.code
            res['rectification_ref_number'] = self.doc_invoice_relac[0].nro_comprobante

        res['partner_street_address'] = (self.partner_id.street_name or '') \
                                + (self.partner_id.street_number and (' ' + self.partner_id.street_number) or '') \
                                + (self.partner_id.street_number2 and (' ' + self.partner_id.street_number2) or '') \
                                + (self.partner_id.street2 and (' ' + self.partner_id.street2) or '') \
                                + (self.partner_id.district_id and ', ' + self.partner_id.district_id.name or '') \
                                + (self.partner_id.province_id and ', ' + self.partner_id.province_id.name or '') \
                                + (self.partner_id.state_id and ', ' + self.partner_id.state_id.name or '') \
                                + (self.partner_id.country_id and ', ' + self.partner_id.country_id.name or '')
        return res

    def _get_l10n_pe_dte_qrcode(self):
        res = super(AccountMove, self)._get_l10n_pe_dte_qrcode()
        if res != '':
            qr_string = ''
            dte_serial = ''
            dte_number = ''
            seq_split = self.ref.split('-')
            if len(seq_split)==2:
                dte_serial = seq_split[0]
                dte_number = seq_split[1]
            res = []
            res.append(self.company_id.vat or '')
            res.append(dte_serial)
            res.append(dte_number)
            res.append(str(round(0.0, 2)))
            res.append(str(round(self.l10n_pe_dte_amount_total, 2)))
            res.append(self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else '')
            res.append(self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or '')
            res.append(self.partner_id.vat or '')
            qr_string = '|'.join(res)
            return qr_string
        else:
            return res