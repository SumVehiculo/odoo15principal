# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
import logging
log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    l10n_pe_dte_is_detraction = fields.Boolean('Sujeto a detraccion?', default=False)
    l10n_pe_dte_detraction_code = fields.Selection(
        selection=[
            ("001", "Azúcar y melaza de caña (10%)"),
            ("002", "Arroz"),
            ("003", "Alcohol etílico (10%)"),
            ("004", "Recursos hidrobiológicos (4%)"),
            ("005", "Maíz amarillo duro (4%)"),
            ("007", "Caña de azúcar (10%)"),
            ("008", "Madera (4%)"),
            ("009", "Arena y piedra. (10%)"),
            ("010", "Residuos, subproductos, desechos, recortes y desperdicios"),
            ("011", "Bienes gravados con el IGV, o renuncia a la exoneración (10%)"),
            ("012", "Intermediación laboral y tercerización (12%)"),
            ("013", "Animales vivos"),
            ("014", "Carnes y despojos comestibles"),
            ("015", "Abonos, cueros y pieles de origen animal"),
            ("016", "Aceite de pescado (10%)"),
            ("017", "Harina, polvo y “pellets” de pescado, crustáceos, moluscos y demás invertebrados acuáticos"),
            ("019", "Arrendamiento de bienes muebles (10%)"),
            ("020", "Mantenimiento y reparación de bienes muebles (12%)"),
            ("021", "Movimiento de carga (10%)"),
            ("022", "Otros servicios empresariales (12%)"),
            ("023", "Leche (4%)"),
            ("024", "Comisión mercantil (10%)"),
            ("025", "Fabricación de bienes por encargo (10%)"),
            ("026", "Servicio de transporte de personas (10%)"),
            ("027", "Servicio de transporte de carga"),
            ("028", "Transporte de pasajeros"),
            ("030", "Contratos de construcción (4%)"),
            ("031", "Oro gravado con el IGV (10%)"),
            ("032", "Paprika y otros frutos de los generos capsicum o pimienta (10%)"),
            ("034", "Minerales metálicos no auríferos (10%)"),
            ("035", "Bienes exonerados del IGV (1.5%)"),
            ("036", "Oro y demás minerales metálicos exonerados del IGV (1.5%)"),
            ("037", "Demás servicios gravados con el IGV (12%)"),
            ("039", "Minerales no metálicos (10%)"),
            ("040", "Bien inmueble gravado con IGV"),
            ("041", "Plomo (15%)"),
            ("099", "Ley 30737"),
        ], string='Tipo detraccion')
    l10n_pe_dte_detraction_payment_method = fields.Selection(
        selection=[
            ("001","Depósito en cuenta"),
            ("002","Giro"),
            ("003","Transferencia de fondos"),
            ("004","Orden de pago"),
            ("005","Tarjeta de débito"),
            ("006","Tarjeta de crédito emitida en el país por una empresa del sistema financiero "),
            ("007","Cheques con la cláusula de \"NO NEGOCIABLE\", \"INTRANSFERIBLES\", \"NO A LA ORDEN\" u otra equivalente, a que se refiere el inciso g) del artículo 5° de la ley"),
            ("008","Efectivo, por operaciones en las que no existe obligación de utilizar medio de pago"),
            ("009","Efectivo, en los demás casos"),
            ("010","Medios de pago usados en comercio exterior "),
            ("011","Documentos emitidos por las EDPYMES y las cooperativas de ahorro y crédito no autorizadas a captar depósitos del público"),
            ("012","Tarjeta de crédito emitida en el país o en el exterior por una empresa no perteneciente al sistema financiero, cuyo objeto principal sea la emisión y administración de tarjetas de crédito"),
            ("013","Tarjetas de crédito emitidas en el exterior por empresas bancarias o financieras no domiciliadas"),
            ("101","Transferencias – Comercio exterior"),
            ("102","Cheques bancarios - Comercio exterior"),
            ("103","Orden de pago simple - Comercio exterior"),
            ("104","Orden de pago documentario - Comercio exterior"),
            ("105","Remesa simple - Comercio exterior"),
            ("106","Remesa documentaria - Comercio exterior"),
            ("107","Carta de crédito simple - Comercio exterior"),
            ("108","Carta de crédito documentario - Comercio exterior"),
            ("999","Otros medios de pago"),
        ], string='Medio de pago detraccion')
    l10n_pe_dte_detraction_percent = fields.Float(string='Porcentaje detraccion')
    l10n_pe_dte_detraction_base = fields.Float(string='Base detraccion')
    l10n_pe_dte_detraction_amount = fields.Float(string='Importe detraccion')

    @api.onchange('l10n_pe_dte_detraction_code')
    def _onchange_detraction_code(self):
        if self.l10n_pe_dte_detraction_code != None and self.l10n_pe_dte_is_detraction:
            porcentajes = {"001": 10,
                           "003": 10,
                           "004": 4,
                           "005": 4,
                           "007": 10,
                           "008": 4,
                           "009": 10,
                           "011": 10,
                           "012": 12,
                           "016": 10,
                           "019": 10,
                           "020": 12,
                           "021": 10,
                           "022": 12,
                           "023": 4,
                           "024": 10,
                           "025": 10,
                           "026": 10,
                           "030": 4,
                           "031": 10,
                           "032": 10,
                           "034": 10,
                           "035": 1.5,
                           "036": 1.5,
                           "037": 12,
                           "039": 10,
                           "041": 15, }
            self.l10n_pe_dte_detraction_percent = porcentajes.get(self.l10n_pe_dte_detraction_code, 0)
            self._onchange_detraction_percent()

    @api.onchange('l10n_pe_dte_detraction_percent')
    def _onchange_detraction_percent(self):
        currency_rate_tmp = 1
        total_untaxed = 0.0
        total_untaxed_currency = 0.0
        for line in self.line_ids:
            if not line.exclude_from_invoice_tab and any(tax.l10n_pe_edi_tax_code in ['1000'] for tax in line.tax_ids):
                # Untaxed amount.
                total_untaxed += line.balance
                total_untaxed_currency += line.amount_currency
        if self.currency_id.name!='PEN':
            currency_rate_tmp = abs(total_untaxed/total_untaxed_currency) if total_untaxed_currency!=0 else 1
        self.l10n_pe_dte_detraction_base = self.amount_total if self.currency_id.name == 'PEN' else self.amount_total*currency_rate_tmp
        self.l10n_pe_dte_detraction_amount = round(self.l10n_pe_dte_detraction_percent*self.l10n_pe_dte_detraction_base/100,2)

    def l10n_pe_dte_credit_amount_single_fee(self):
        res = super(AccountInvoice, self).l10n_pe_dte_credit_amount_single_fee()
        currency_rate_tmp = 1
        total_untaxed = 0.0
        total_untaxed_currency = 0.0
        for line in self.line_ids:
            if not line.exclude_from_invoice_tab and any(tax.l10n_pe_edi_tax_code in ['1000'] for tax in line.tax_ids):
                # Untaxed amount.
                total_untaxed += line.balance
                total_untaxed_currency += line.amount_currency
        if self.currency_id.name!='PEN':
            currency_rate_tmp = abs(total_untaxed/total_untaxed_currency) if total_untaxed_currency!=0 else 1
        res+=-self.l10n_pe_dte_detraction_amount/currency_rate_tmp
        return res

    def _l10n_pe_prepare_dte(self):
        res = super(AccountInvoice, self)._l10n_pe_prepare_dte()
        if self.l10n_pe_dte_is_detraction:
            res["detraction"]=True
            res["detraction_amount"]=self.l10n_pe_dte_detraction_amount
            res["detraction_percent"]=self.l10n_pe_dte_detraction_percent
            res["detraction_code"]=self.l10n_pe_dte_detraction_code
            res["detraction_payment_method_code"]=self.l10n_pe_dte_detraction_payment_method or '001'
        return res
