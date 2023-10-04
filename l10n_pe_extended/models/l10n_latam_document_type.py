# -*- coding: utf-8 -*-
from odoo import models, fields


class L10nLatamDocumentType(models.Model):

    _inherit = 'l10n_latam.document.type'

    l10n_pe_sequence_prefix = fields.Char(string='Prefijo Comprobante')

    '''def _format_document_number(self, document_number):
        """ Make validation of Import Dispatch Number
          * making validations on the document_number. If it is wrong it should raise an exception
          * format the document_number against a pattern and return it
        """
        self.ensure_one()
        if self.country_id.code != "PE":
            return super()._format_document_number(document_number)

        if not document_number:
            return False

        return document_number.zfill(8)'''