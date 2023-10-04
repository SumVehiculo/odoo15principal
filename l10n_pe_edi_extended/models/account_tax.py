# -*- coding: utf-8 -*-

from odoo import fields, api, models

PE_EDI_ISC_TYPE = [
            ('01', 'Sistema al valor (Apéndice IV, lit. A – T.U.O IGV e ISC)'),
            ('02', 'Aplicación del Monto Fijo ( Sistema específico, bienes en el apéndice III, Apéndice IV, lit. B – T.U.O IGV e ISC)'),
            ('03', 'Sistema de Precios de Venta al Público (Apéndice IV, lit. C – T.U.O IGV e ISC)'),
        ]

class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_pe_edi_igv_type = fields.Selection(
        selection=[
            ('10', 'Gravado - Operación Onerosa'),
            ('11', 'Gravado – Retiro por premio'),
            ('12', 'Gravado – Retiro por donación'),
            ('13', 'Gravado – Retiro'),
            ('14', 'Gravado – Retiro por publicidad'),
            ('15', 'Gravado – Bonificaciones'),
            ('16', 'Gravado – Retiro por entrega a trabajadores'),
            ('17', 'Gravado - IVAP'),
            ('20', 'Exonerado - Operación Onerosa'),
            ('21', 'Exonerado - Transferencia gratuita'),
            ('30', 'Inafecto - Operación Onerosa'),
            ('31', 'Inafecto – Retiro por Bonificación'),
            ('32', 'Inafecto – Retiro'),
            ('33', 'Inafecto – Retiro por Muestras Médicas'),
            ('34', 'Inafecto - Retiro por Convenio Colectivo'),
            ('35', 'Inafecto – Retiro por premio'),
            ('36', 'Inafecto - Retiro por publicidad'),
            ('37', 'Inafecto - Transferencia gratuita'),
            ('40', 'Exportación de Bienes o Servicios'),
        ], string="EDI IGV Type")

    l10n_pe_edi_isc_type = fields.Selection(
        selection=PE_EDI_ISC_TYPE,
        string="EDI ISC Type")

    l10n_pe_edi_international_code = fields.Char(
        string="EDI International Code",
        compute='_compute_l10n_pe_edi_international_code')

    @api.depends('l10n_pe_edi_tax_code')
    def _compute_l10n_pe_edi_international_code(self):
        international_codes_mapping = {
            '1000': 'VAT',
            '1016': 'VAT',
            '2000': 'EXC',
            '7152': 'OTH',
            '9995': 'FRE',
            '9996': 'FRE',
            '9997': 'VAT',
            '9998': 'FRE',
            '9999': 'OTH',
        }
        for tax in self:
            tax.l10n_pe_edi_international_code = international_codes_mapping.get(tax.l10n_pe_edi_tax_code, 'VAT')

    def _get_l10n_pe_edi_affectation_reason(self):
        #dummy
        return self.l10n_pe_edi_igv_type
    
    def _get_l10n_pe_edi_isc_type_computation(self):
        #dummy
        return self.l10n_pe_edi_isc_type

class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    l10n_pe_edi_isc_type = fields.Selection(
        selection=PE_EDI_ISC_TYPE,
        string="EDI ISC Type")

    def _get_tax_vals(self, company, tax_template_to_tax):
        val = super()._get_tax_vals(company, tax_template_to_tax)
        val.update({
            'l10n_pe_edi_isc_type': self.l10n_pe_edi_isc_type,
        })
        return val


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    l10n_pe_edi_code = fields.Char('EDI Code', help="Peruvian EDI code to complement catalog 05")