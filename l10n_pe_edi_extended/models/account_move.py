# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import is_html_empty
from odoo.osv import expression
from num2words import num2words
from collections import defaultdict
import logging
log = logging.getLogger(__name__)

def format_float(amount, precision=2):
    ''' Helper to format monetary amount as a string with 2 decimal places. '''
    if amount is None or amount is False:
        return None
    return '%.*f' % (precision, amount)

def unit_amount(amount, quantity, currency):
    ''' Helper to divide amount by quantity by taking care about float division by zero. '''
    if quantity:
        return currency.round(amount / quantity)
    else:
        return 0.0

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('l10n_pe_dte_amount_total','currency_id')
    def _l10n_pe_dte_amount_in_words(self):
        """Transform the amount to text
        """
        for move in self:
            amount_base, amount = divmod(move.l10n_pe_dte_amount_total, 1)
            amount = round(amount, 2)
            amount = int(round(amount * 100, 2))

            lang_code = self.env.context.get('lang') or self.env.user.lang
            lang = self.env['res.lang'].search([('code', '=', lang_code)])
            words = num2words(amount_base, lang=lang.iso_code)
            result = _('%(words)s WITH %(amount)02d/100 %(currency_label)s') % {
                'words': words,
                'amount': amount,
                'currency_label': move.currency_id.name == 'PEN' and 'SOLES' or move.currency_id.currency_unit_label,
            }
            move.l10n_pe_dte_amount_in_words = result.upper()

    def _get_l10n_pe_dte_qrcode(self):
        qr_string = ''
        dte_serial = ''
        dte_number = ''
        if self.l10n_latam_use_documents and self.l10n_latam_document_number:
            seq_split = self.l10n_latam_document_number.split('-')
            if len(seq_split)==2:
                dte_serial = seq_split[0]
                dte_number = seq_split[1]
        else:
            seq_split = self.name.split('-')
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

    def _l10n_pe_edi_get_extra_report_values(self):
        self.ensure_one()
        return {
            "invoice_report_name": self.l10n_latam_document_type_id.report_name,
        }
    
    def l10n_pe_edi_get_extra_report_values(self):
        res = self._l10n_pe_edi_get_extra_report_values()
        return res

    l10n_pe_dte_credit_note_type = fields.Selection(
        selection=[
            ('01', 'Anulación de la operación'),
            ('02', 'Anulación por error en el RUC'),
            ('03', 'Corrección por error en la descripción'),
            ('04', 'Descuento global'),
            ('05', 'Descuento por ítem'),
            ('06', 'Devolución total'),
            ('07', 'Devolución por ítem'),
            ('08', 'Bonificación'),
            ('09', 'Disminución en el valor'),
            ('10', 'Otros Conceptos '),
            ('11', 'Ajustes de operaciones de exportación'),
            ('12', 'Ajustes afectos al IVAP'),
            ('13', 'Ajustes – montos y/o fechas de pago'),
        ],
        string="Credit Note Type")
    l10n_pe_dte_debit_note_type = fields.Selection(
        selection=[
            ('01', 'Intereses por mora'),
            ('02', 'Aumento en el valor'),
            ('03', 'Penalidades/ otros conceptos '),
            ('11', 'Ajustes de operaciones de exportación'),
            ('12', 'Ajustes afectos al IVAP'),
        ],
        string="Debit Note Type")
    l10n_pe_dte_rectification_ref_type = fields.Many2one('l10n_latam.document.type', string='Rectificativa - Tipo Comprobante')
    l10n_pe_dte_rectification_ref_number = fields.Char('Rectificativa - Serie-numero')
    l10n_pe_dte_rectification_ref_date = fields.Char('Rectificativa - Fecha comprobante')
    l10n_pe_dte_operation_type = fields.Selection(
        selection=[
            ('0101', 'Venta interna	Factura, Boletas'),
            ('0112', 'Venta Interna - Sustenta Gastos Deducibles Persona Natural	Factura '),
            ('0113', 'Venta Interna-NRUS	Boleta'),
            ('0200', 'Exportación de Bienes	Factura, Boletas'),
            ('0201', 'Exportación de Servicios – Prestación servicios realizados íntegramente en el país	Factura, Boletas'),
            ('0202', 'Exportación de Servicios – Prestación de servicios de hospedaje No Domiciliado	Factura'),
            ('0203', 'Exportación de Servicios – Transporte de navieras	Factura, Boletas'),
            ('0204', 'Exportación de Servicios – Servicios  a naves y aeronaves de bandera extranjera	Factura, Boletas'),
            ('0205', 'Exportación de Servicios  - Servicios que conformen un Paquete Turístico	Factura'),
            ('0206', 'Exportación de Servicios – Servicios complementarios al transporte de carga	Factura, Boletas'),
            ('0207', 'Exportación de Servicios – Suministro de energía eléctrica a favor de sujetos domiciliados en ZED	Factura, Boletas'),
            ('0208', 'Exportación de Servicios – Prestación servicios realizados parcialmente en el extranjero	Factura, Boletas'),
            ('0301', 'Operaciones con Carta de porte aéreo (emitidas en el ámbito nacional)	Factura, Boletas'),
            ('0302', 'Operaciones de Transporte ferroviario de pasajeros	Factura, Boletas'),
            ('0401', 'Ventas no domiciliados que no califican como exportación	Factura, Boletas'),
            ('0501', 'Compra interna	Liquidación de compra'),
            ('0502', 'Anticipos	Liquidación de compra'),
            ('0503', 'Compra de oro	Liquidación de compra'),
            ('1001', 'Operación Sujeta a Detracción	Factura, Boletas'),
            ('1002', 'Operación Sujeta a Detracción- Recursos Hidrobiológicos	Factura, Boletas'),
            ('1003', 'Operación Sujeta a Detracción- Servicios de Transporte Pasajeros	Factura, Boletas'),
            ('1004', 'Operación Sujeta a Detracción- Servicios de Transporte Carga	Factura, Boletas'),
            ('2001', 'Operación Sujeta a Percepción	Factura, Boletas'),
            ('2100', 'Créditos a empresas	Factura, Boletas'),
            ('2101', 'Créditos de consumo revolvente	Factura, Boletas'),
            ('2102', 'Créditos de consumo no revolvente 	Factura, Boletas'),
            ('2103', 'Otras operaciones no gravadas - Empresas del sistema financiero y cooperativas de ahorro y crédito no autorizadas a captar recursos del público	Factura, Boletas'),
            ('2104', 'Otras operaciones no  gravadas - Empresas del sistema de seguros	Factura, Boletas'),
        ],
        string="Operation Type",
        store=True, readonly=False, default='0101')
    l10n_pe_dte_status = fields.Selection([
        ('not_sent', 'Pending To Be Sent'),
        ('ask_for_status', 'Ask For Status'),
        ('accepted', 'Accepted'),
        ('objected', 'Accepted With Objections'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('manual', 'Manual'),
    ], default='not_sent', string='SUNAT DTE status', copy=False, tracking=True, help="""Status of sending the DTE to the SUNAT:
    - Not sent: the DTE has not been sent to SUNAT but it has created.
    - Ask For Status: The DTE is asking for its status to the SUNAT.
    - Accepted: The DTE has been accepted by SUNAT.
    - Accepted With Objections: The DTE has been accepted with objections by SUNAT.
    - Rejected: The DTE has been rejected by SUNAT.
    - Manual: The DTE is sent manually, i.e.: the DTE will not be sending manually.""")
    l10n_pe_dte_status_response = fields.Char(string='SUNAT DTE status response', copy=False)
    l10n_pe_dte_void_status = fields.Selection([
        ('not_sent', 'Pending To Be Sent'),
        ('ask_for_status', 'Ask For Status'),
        ('accepted', 'Accepted'),
        ('objected', 'Accepted With Objections'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('manual', 'Manual'),
    ], string='SUNAT DTE Void status', copy=False, tracking=True, help="""Status of sending the Void DTE to the SUNAT:
    - Not sent: the DTE has not been sent to SUNAT but it has created.
    - Ask For Status: The DTE is asking for its status to the SUNAT.
    - Accepted: The DTE has been accepted by SUNAT.
    - Accepted With Objections: The DTE has been accepted with objections by SUNAT.
    - Rejected: The DTE has been rejected by SUNAT.
    - Manual: The DTE is sent manually, i.e.: the DTE will not be sending manually.""")
    l10n_pe_dte_void_status_response = fields.Char(string='SUNAT DTE Void status response', copy=False)
    l10n_pe_dte_cancel_reason = fields.Char(
        string="Cancel Reason", copy=False,
        help="Reason given by the user to cancel this move")
    l10n_pe_dte_partner_status = fields.Selection([
        ('not_sent', 'Not Sent'),
        ('sent', 'Sent'),
    ], string='Partner DTE status', copy=False, help="""
    Status of sending the DTE to the partner:
    - Not sent: the DTE has not been sent to the partner but it has sent to SUNAT.
    - Sent: The DTE has been sent to the partner.""")
    l10n_pe_dte_file = fields.Many2one('ir.attachment', string='DTE file', copy=False)
    l10n_pe_dte_file_link = fields.Char(string='DTE file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_hash = fields.Char(string='DTE Hash', copy=False)
    l10n_pe_cdr_file = fields.Many2one('ir.attachment', string='CDR file', copy=False)
    l10n_pe_cdr_void_file = fields.Many2one('ir.attachment', string='CDR Void file', copy=False)
    l10n_pe_dte_pdf_file = fields.Many2one('ir.attachment', string='DTE PDF file', copy=False)
    l10n_pe_dte_pdf_file_link = fields.Char(string='DTE PDF file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_cdr_file = fields.Many2one('ir.attachment', string='CDR file', copy=False)
    l10n_pe_dte_cdr_file_link = fields.Char(string='CDR file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_cdr_void_file = fields.Many2one('ir.attachment', string='CDR Void file', copy=False)
    l10n_pe_dte_cdr_void_file_link = fields.Char(string='CDR Void file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_service_order = fields.Char(string='Purchase/Service order', help='This Purchase/service order will be shown on the electronic invoice')
    l10n_pe_dte_retention_type = fields.Selection([
        ('01', 'Tasa 3%'),
        ('02', 'Tasa 6%'),
    ], string='IGV Retention Type', copy=True, readonly=True,
        states={'draft': [('readonly', False)]},)

    # === Amount fields ===
    l10n_pe_dte_amount_subtotal = fields.Monetary(string='Subtotal',store=True, readonly=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True, help='Total without discounts and taxes')
    l10n_pe_dte_amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_base = fields.Monetary(string='Base Amount', store=True, readonly=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True, help='Total with discounts and before taxes')
    l10n_pe_dte_amount_exonerated = fields.Monetary(string='Exonerated  Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_free = fields.Monetary(string='Free Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_unaffected = fields.Monetary(string='Unaffected Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_exportation = fields.Monetary(string='Exportation Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_prepaid = fields.Monetary(string='Prepaid Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_untaxed = fields.Monetary(string='Total before taxes', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True, help='Total before taxes, all discounts included')
    l10n_pe_dte_global_discount = fields.Monetary(string='Global discount', store=True, readonly=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_in_words = fields.Char(string="Amount in Words", compute='_l10n_pe_dte_amount_in_words')
    l10n_pe_dte_amount_perception_base = fields.Float(string='Perception Base', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_perception_percentage = fields.Float(string='Perception Percentage', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_perception = fields.Float(string='Perception Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_retention_base = fields.Monetary(string='IGV Retention Base', copy=True, readonly=True,
        states={'draft': [('readonly', False)]},)
    l10n_pe_dte_amount_retention = fields.Monetary(string='IGV Retention Amount', copy=True, readonly=True,
        states={'draft': [('readonly', False)]},)
    # ==== Tax fields ====
    l10n_pe_dte_igv_percent = fields.Integer(string="Percentage IGV", compute='_get_percentage_igv')
    l10n_pe_dte_amount_icbper = fields.Monetary(string='ICBPER Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_igv = fields.Monetary(string='IGV Amount', store=True,compute='_compute_dte_amount',  compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_isc = fields.Monetary(string='ISC Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_others = fields.Monetary(string='Other charges', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_is_einvoice = fields.Boolean('Is E-invoice')
    l10n_pe_dte_amount_total = fields.Monetary(string='Total Amount', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    l10n_pe_dte_amount_total_with_perception = fields.Float(string='Total Amount With Perception', store=True, compute='_compute_dte_amount', compute_sudo=True, tracking=True)
    invoice_payment_fee_ids = fields.One2many('account.move.payment_fee','move_id', string='Credit Payment Fees')
    invoice_payment_fee_total = fields.Monetary(string='[Credit] Amount Pending to Pay', compute='_compute_invoice_payment_fee_total', store=True)
    amount_by_group2 = fields.Binary(string="Tax amount by group",
        compute='_compute_invoice_taxes_by_group2',
        help='Edit Tax amounts if you encounter rounding issues.')

    def _reverse_move_vals(self, default_values, cancel=True):
        res = super(AccountMove, self)._reverse_move_vals(default_values, cancel=cancel)
        i=0
        for line in res.get('line_ids', []):
            if abs(line[2]['discount'])>0:
                if abs((round(line[2]['quantity']*line[2]['price_unit']*line[2]['discount']/100,2)-line[2]['price_subtotal']))>0:
                    res['line_ids'][i][2]['price_unit'] = line[2]['price_total']/line[2]['quantity'] if line[2]['quantity']>0 else 0
                else:
                    res['line_ids'][i][2]['price_unit'] = line[2]['price_subtotal']/line[2]['quantity'] if line[2]['quantity']>0 else 0
                res['line_ids'][i][2]['discount'] = 0
            i+=1
        return res

    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_group2(self):
        for move in self:

            # Not working on something else than invoices.
            if not move.is_invoice(include_receipts=True):
                move.amount_by_group2 = []
                continue

            lang_env = move.with_context(lang=move.partner_id.lang).env
            balance_multiplicator = -1 if move.is_inbound() else 1

            tax_lines = move.line_ids.filtered('tax_line_id')
            base_lines = move.line_ids.filtered('tax_ids')

            tax_group_mapping = defaultdict(lambda: {
                'base_lines': set(),
                'base_amount': 0.0,
                'tax_amount': 0.0,
            })

            # Compute base amounts.
            for base_line in base_lines:
                base_amount = balance_multiplicator * (base_line.amount_currency if base_line.currency_id else base_line.balance)

                for tax in base_line.tax_ids.flatten_taxes_hierarchy():

                    if base_line.tax_line_id.tax_group_id == tax.tax_group_id:
                        continue

                    tax_group_vals = tax_group_mapping[tax.tax_group_id]
                    if base_line not in tax_group_vals['base_lines']:
                        tax_group_vals['base_amount'] += base_amount
                        tax_group_vals['base_lines'].add(base_line)

            # Compute tax amounts.
            for tax_line in tax_lines:
                tax_amount = balance_multiplicator * (tax_line.amount_currency if tax_line.currency_id else tax_line.balance)
                tax_group_vals = tax_group_mapping[tax_line.tax_line_id.tax_group_id]
                tax_group_vals['tax_amount'] += tax_amount

            tax_groups = sorted(tax_group_mapping.keys(), key=lambda x: x.sequence)
            amount_by_group = []
            for tax_group in tax_groups:
                tax_group_vals = tax_group_mapping[tax_group]
                amount_by_group.append((
                    tax_group.name,
                    tax_group_vals['tax_amount'],
                    tax_group_vals['base_amount'],
                    formatLang(lang_env, tax_group_vals['tax_amount'], currency_obj=move.currency_id),
                    formatLang(lang_env, tax_group_vals['base_amount'], currency_obj=move.currency_id),
                    len(tax_group_mapping),
                    tax_group.id
                ))
            move.amount_by_group2 = amount_by_group

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.company_id.country_id.code == 'PE' and self.partner_id.country_id and self.partner_id.country_id.code != 'PE':
            self.l10n_pe_dte_operation_type = '0200'
        else:
            self.l10n_pe_dte_operation_type = '0101'
        return super(AccountMove, self)._onchange_partner_id()

    @api.depends('invoice_payment_fee_ids','invoice_payment_fee_ids.amount_total')
    def _compute_invoice_payment_fee_total(self):
        for rec in self:
            invoice_payment_fee_total = 0
            for fee in rec.invoice_payment_fee_ids:
                invoice_payment_fee_total+=fee.amount_total
            rec.invoice_payment_fee_total = invoice_payment_fee_total

    def _compute_l10n_pe_dte_links(self):
        for move in self:
            move.l10n_pe_dte_file_link = move.l10n_pe_dte_file.url if move.l10n_pe_dte_file else None
            move.l10n_pe_dte_pdf_file_link = move.l10n_pe_dte_pdf_file.url if move.l10n_pe_dte_pdf_file else None
            move.l10n_pe_dte_cdr_file_link = move.l10n_pe_dte_cdr_file.url if move.l10n_pe_dte_cdr_file else None
            move.l10n_pe_dte_cdr_void_file_link = move.l10n_pe_dte_cdr_void_file.url if move.l10n_pe_dte_cdr_void_file else None

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'amount_by_group2')
    def _compute_dte_amount(self):
        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            l10n_pe_dte_global_discount = 0.0
            l10n_pe_dte_amount_discount = 0.0
            l10n_pe_dte_amount_subtotal = 0.0
            l10n_pe_dte_amount_prepaid = 0.0
            #~ E-invoice amounts
            l10n_pe_dte_amount_free = 0.0
            l10n_pe_dte_amount_total_with_perception = 0.0
            l10n_pe_dte_amount_perception_percentage = 0.0
            currencies = set()
            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)
                if move.is_invoice(include_receipts=True):
                    # === Invoices ===
                    # If the amount is negative, is considerated as global discount
                    if not line.l10n_pe_dte_advance_line:
                        l10n_pe_dte_global_discount += line.l10n_pe_dte_price_base < 0 and line.l10n_pe_dte_price_base * sign * -1 or 0.0
                    else:
                        l10n_pe_dte_amount_prepaid += abs(line.price_total)
                    # If the product is not free, it calculates the amount discount 
                    l10n_pe_dte_amount_discount += line.l10n_pe_dte_free_product == False and (line.l10n_pe_dte_price_base * line.discount)/100 or 0.0
                    # If the price_base is > 0, sum to the total without taxes and discounts
                    l10n_pe_dte_amount_subtotal += line.l10n_pe_dte_price_base > 0 and line.l10n_pe_dte_price_base or 0.0
                    # Free product amount
                    l10n_pe_dte_amount_free += line.l10n_pe_dte_amount_free
                # Affected by IGV
                if not line.exclude_from_invoice_tab and any(tax.l10n_pe_edi_tax_code in ['1000'] for tax in line.tax_ids):
                    # Untaxed amount.
                    total_untaxed += line.balance
                    total_untaxed_currency += line.amount_currency
            move.l10n_pe_dte_amount_base = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            # move.l10n_pe_dte_amount_base = sum([x[2] for x in move.amount_by_group if x[0] not in ['INA','EXO','EXP']])
            # Sum of Amount base of the lines where it has any Tax with code '9997'  (Exonerated)
            move.l10n_pe_dte_amount_exonerated = sum([x.l10n_pe_dte_price_base for x in move.invoice_line_ids if any(tax.l10n_pe_edi_tax_code in ['9997'] for tax in x.tax_ids)])
            # Sum of Amount base of the lines where it has any Tax with code in ['9998']  (Unaffected and exportation)
            move.l10n_pe_dte_amount_unaffected = sum([x.l10n_pe_dte_price_base for x in move.invoice_line_ids if any(tax.l10n_pe_edi_tax_code in ['9998'] for tax in x.tax_ids)])
            # Sum of Amount base of the lines where it has any Tax with code in ['9995']  (Unaffected and exportation)
            move.l10n_pe_dte_amount_exportation = sum([x.l10n_pe_dte_price_base for x in move.invoice_line_ids if any(tax.l10n_pe_edi_tax_code in ['9995'] for tax in x.tax_ids)])
            move.l10n_pe_dte_amount_prepaid = l10n_pe_dte_amount_prepaid
            move.l10n_pe_dte_amount_igv = sum([x[1] for x in move.amount_by_group2 if x[0] == 'IGV'])
            #move.l10n_pe_dte_amount_isc = sum([x[1] for x in move.amount_by_group2 if x[0] == 'ISC'])
            move.l10n_pe_dte_amount_isc = sum([x.l10n_pe_dte_isc_amount for x in move.invoice_line_ids if all(tax.l10n_pe_edi_tax_code not in ['9996'] for tax in x.tax_ids)])
            move.l10n_pe_dte_amount_icbper = sum([x[1] for x in move.amount_by_group2 if x[0] == 'ICBPER'])
            move.l10n_pe_dte_amount_others = sum([x[1] for x in move.amount_by_group2 if x[0] == 'OTROS'])
            move.l10n_pe_dte_amount_perception = sum([x[1] for x in move.amount_by_group2 if x[0] == 'PER'])
            move.l10n_pe_dte_amount_perception_base = sum([x[2] for x in move.amount_by_group2 if x[0] == 'PER'])
            #move.l10n_pe_dte_amount_untaxed = move.l10n_pe_dte_amount_base - move.l10n_pe_dte_amount_free
            move.l10n_pe_dte_amount_untaxed = move.l10n_pe_dte_amount_base
            move.l10n_pe_dte_amount_perception_base += sum([abs(x.balance) for x in move.invoice_line_ids if any(tax.tax_group_id.name in ['PERG'] for tax in x.tax_ids)])
            # TODO Global discount
            move.l10n_pe_dte_global_discount = l10n_pe_dte_global_discount
            move.l10n_pe_dte_amount_discount = l10n_pe_dte_amount_discount
            move.l10n_pe_dte_amount_subtotal = l10n_pe_dte_amount_subtotal
            move.l10n_pe_dte_amount_free = l10n_pe_dte_amount_free
            move.l10n_pe_dte_amount_total = move.l10n_pe_dte_amount_base + move.l10n_pe_dte_amount_exonerated + move.l10n_pe_dte_amount_unaffected + move.l10n_pe_dte_amount_exportation + move.l10n_pe_dte_amount_igv + move.l10n_pe_dte_amount_isc + move.l10n_pe_dte_amount_icbper + move.l10n_pe_dte_amount_others
            currency_rate_tmp = 1
            if move.currency_id.name!='PEN':
                currency_rate_tmp = abs(total_untaxed/total_untaxed_currency) if total_untaxed_currency!=0 else 1
            if move.l10n_pe_dte_amount_perception_base>0 and move.l10n_pe_dte_amount_perception==0:
                move.l10n_pe_dte_amount_perception = move.l10n_pe_dte_amount_perception_base
                
                move.l10n_pe_dte_amount_perception_base = round(move.l10n_pe_dte_amount_total*currency_rate_tmp,2)
            if move.l10n_pe_dte_amount_perception>0:
                l10n_pe_dte_amount_total_with_perception = round(move.l10n_pe_dte_amount_total*currency_rate_tmp + move.l10n_pe_dte_amount_perception,2)
                l10n_pe_dte_amount_perception_percentage = round(move.l10n_pe_dte_amount_perception*100/move.l10n_pe_dte_amount_perception_base,2)
            move.l10n_pe_dte_amount_perception_percentage = l10n_pe_dte_amount_perception_percentage
            move.l10n_pe_dte_amount_total_with_perception = l10n_pe_dte_amount_total_with_perception

    @api.onchange('l10n_pe_dte_amount_retention_base','l10n_pe_dte_retention_type','amount_total')
    def _onchange_l10n_pe_retention_calc(self):
        for rec in self:
            if rec.l10n_pe_dte_retention_type:
                if rec.l10n_pe_dte_amount_retention_base==0:
                    rec.l10n_pe_dte_amount_retention_base = rec.amount_total
                if rec.l10n_pe_dte_amount_retention_base:
                    percentage = 0
                    if rec.l10n_pe_dte_retention_type=='01':
                        percentage = 0.03
                    elif rec.l10n_pe_dte_retention_type=='02':
                        percentage = 0.06
                    rec.l10n_pe_dte_amount_retention = rec.l10n_pe_dte_amount_retention_base*percentage
                else:
                    rec.l10n_pe_dte_amount_retention = 0
            else:
                rec.l10n_pe_dte_amount_retention_base = 0
                rec.l10n_pe_dte_amount_retention = 0

    @api.depends('company_id')
    def _compute_l10n_pe_dte_operation_type(self):
        for move in self:
            move.l10n_pe_dte_operation_type = '0101' if move.company_id.country_id == self.env.ref('base.pe') and move.journal_id.type=='sale' else False

    def _get_l10n_pe_dte_extra_fields(self):
        updt = {}
        return updt
    def _post(self, soft=True):
        res = super(AccountMove, self)._post()
        for move in self:
            if move.journal_id.l10n_pe_is_dte:
                move.l10n_pe_dte_is_einvoice = True
                move.write(move._get_l10n_pe_dte_extra_fields())
            if move.l10n_pe_dte_is_einvoice and move.move_type=='out_invoice':
                move.l10n_pe_dte_compute_fees()
            if move.l10n_pe_dte_is_einvoice and move.company_id.l10n_pe_dte_send_interval_unit=="immediately":
                move.l10n_pe_dte_action_send()
        return res

    def l10n_pe_dte_action_send(self):
        #override this method for custom integration
        pass

    def l10n_pe_dte_action_check(self):
        #override this method for custom integration
        pass

    def l10n_pe_dte_action_cancel(self):
        #override this method for custom integration
        pass
    
    def _l10n_pe_prepare_dte(self):
        dte_serial = ''
        dte_number = ''
        if self.l10n_latam_use_documents and self.l10n_latam_document_number:
            seq_split = self.l10n_latam_document_number.split('-')
            if len(seq_split)==2:
                dte_serial = seq_split[0]
                dte_number = seq_split[1]
        else:
            seq_split = self.name.split('-')
            if len(seq_split)==2:
                dte_serial = seq_split[0]
                dte_number = seq_split[1]

        document = {
            'operation_type': self.l10n_pe_dte_operation_type,
            'partner_vat': self.partner_id.vat,
            'partner_identification_type': self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            'partner_street_address': (self.partner_id.street_name or '') \
                                + (self.partner_id.street_number and (' ' + self.partner_id.street_number) or '') \
                                + (self.partner_id.street_number2 and (' ' + self.partner_id.street_number2) or '') \
                                + (self.partner_id.street2 and (' ' + self.partner_id.street2) or '') \
                                + (self.partner_id.l10n_pe_district and ', ' + self.partner_id.l10n_pe_district.name or '') \
                                + (self.partner_id.city_id and ', ' + self.partner_id.city_id.name or '') \
                                + (self.partner_id.state_id and ', ' + self.partner_id.state_id.name or '') \
                                + (self.partner_id.country_id and ', ' + self.partner_id.country_id.name or ''),
            'partner_name': self.partner_id.commercial_partner_id.name or self.partner_id.commercial_partner_id.name,
            'partner_email': self.partner_id.email,
            'issue_date': self.invoice_date.strftime('%Y-%m-%d'),
            'date_due': self.invoice_date_due.strftime('%Y-%m-%d') if self.invoice_date_due else None,
            'dte_serial': dte_serial,
            'dte_number': dte_number,
            'currency_code': self.currency_id.name,
            'currency_rate': 1,
            'invoice_type_code': self.l10n_latam_document_type_id.code if self.journal_id.l10n_latam_use_documents else '01',
            'amount_total': self.l10n_pe_dte_amount_total, #self.amount_total
            'amount_taxable':abs(self.l10n_pe_dte_amount_base),
            'amount_exonerated': abs(self.l10n_pe_dte_amount_exonerated),
            'amount_unaffected': abs(self.l10n_pe_dte_amount_unaffected),
            'amount_export': abs(self.l10n_pe_dte_amount_exportation),
            'amount_prepaid': abs(self.l10n_pe_dte_amount_prepaid),
            'amount_free': abs(self.l10n_pe_dte_amount_free),
            'amount_igv': abs(self.l10n_pe_dte_amount_igv),
            "amount_isc": abs(self.l10n_pe_dte_amount_isc),
            "amount_icbper":abs(self.l10n_pe_dte_amount_icbper),
            "amount_others":sum([x[1] for x in self.amount_by_group2 if x[0] == 'OTROS']),
            "payment_term":self.invoice_payment_term_id.name if self.invoice_payment_term_id else '',
            "payment_term_is_credit":False,
            "payment_term_fees":[],
            "discount_global_base":0,
            "discount_global_amount":0,
            'other_charges':abs(self.l10n_pe_dte_amount_others),
            "discount_global":abs(self.l10n_pe_dte_global_discount),
            'perception_amount': abs(self.l10n_pe_dte_amount_perception),
            'perception_base': abs(self.l10n_pe_dte_amount_perception_base),
            'total_with_perception': abs(self.l10n_pe_dte_amount_total_with_perception),
            'notes': self.narration if not is_html_empty(self.narration) else '',
            'service_order': self.l10n_pe_dte_service_order,
            'seller': self.invoice_user_id.name,
            'incoterm': self.invoice_incoterm_id.code if self.invoice_incoterm_id else '',
        }
        if self.currency_id.id!=self.company_currency_id.id:
            date = self.date or self.invoice_date or fields.Date.today()
            currency_rates = self.currency_id._get_rates(self.company_id, date)
            exchange_rate = currency_rates.get(self.currency_id.id) or 1.0
            document['currency_rate'] = 1 / (exchange_rate or 1)

        if document['invoice_type_code']=='07':
            document['credit_note_type'] = self.l10n_pe_dte_credit_note_type
            document['rectification_ref_type'] = self.l10n_pe_dte_rectification_ref_type.code
            document['rectification_ref_number'] = self.l10n_pe_dte_rectification_ref_number
        elif document['invoice_type_code']=='08':
            document['debit_note_type'] = self.l10n_pe_dte_debit_note_type
            document['rectification_ref_type'] = self.l10n_pe_dte_rectification_ref_type.code
            document['rectification_ref_number'] = self.l10n_pe_dte_rectification_ref_number

        if len(self.invoice_payment_fee_ids)>0:
            for payment_fee in self.invoice_payment_fee_ids:
                document['payment_term_is_credit'] = True
                document['payment_term_fees'].append({
                    "due_date": payment_fee.date_due.strftime('%Y-%m-%d'),
                    "amount": payment_fee.amount_total,
                    "code": "Cuota" + str(payment_fee.sequence).zfill(3)
                })

        invoice_line_vals = []
        discount_global_base=0
        #other_charges=0
        counter_advanced_lines = 0
        for line in self.invoice_line_ids:
            if line.display_type == False:
                if line.l10n_pe_dte_advance_line:
                    counter_advanced_lines+=1
                dic_line = line.with_context(counter_advanced_lines=counter_advanced_lines)._l10n_pe_prepare_dte_lines()
                if dic_line.get('is_detraction_full_line', False):
                    continue
                '''if line.l10n_pe_dte_allowance_charge_reason_code=='50':
                    other_charges+=dic_line.get('price_subtotal')
                    continue'''
                if dic_line.get('price_total')<0 and not line.l10n_pe_dte_advance_line:
                    document['discount_global_amount']+=abs(dic_line.get('price_subtotal'))
                else:
                    discount_global_base+=dic_line.get('price_subtotal')
                    invoice_line_vals.append(dic_line)

        #document['other_charges'] = other_charges

        if document['discount_global_amount']>0:
            document["discount_global_type"]="02"
            document["discount_global_base"]=discount_global_base
            document["discount_global_factor"]=document['discount_global_amount']/document["discount_global_base"]

        if document['perception_amount']>0:
            document['perception_factor'] = round(document['perception_amount']/document['perception_base'],3)
            #document['amount_total']=document['perception_amount']
            if document['perception_factor']==0.01:
                document['perception_type'] = '02'
            elif document['perception_factor']==0.02:
                document['perception_type'] = '01'
            else:
                document['perception_type'] = '03'

        if self.l10n_pe_dte_retention_type:
            document['retention_type'] = self.l10n_pe_dte_retention_type
            document['retention_base'] = self.l10n_pe_dte_amount_retention_base
            document['retention_amount'] = self.l10n_pe_dte_amount_retention

        document['items'] = invoice_line_vals
        return document

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        res = super(AccountMove, self).action_invoice_sent()
        template = self.env.ref('l10n_pe_edi_extended.email_template_edi_invoice', raise_if_not_found=False)
        if template:
            res['context'].update({'default_template_id': template and template.id or False})
        return res

    '''def get_reversal_origin_data(self):    
        for move in self: 
            if move.type in ['out_invoice','out_refund']:
                if move.debit_origin_id:
                        move.l10n_pe_dte_rectification_ref_number = move.debit_origin_id.l10n_pe_edi_serie
                        move.l10n_pe_dte_rectification_ref_type = move.debit_origin_id.l10n_pe_edi_number
                        move.l10n_pe_edi_reversal_date = move.debit_origin_id.invoice_date
                if move.reversed_entry_id:
                        move.l10n_pe_edi_reversal_serie = move.reversed_entry_id.l10n_pe_edi_serie
                        move.l10n_pe_edi_reversal_number = move.reversed_entry_id.l10n_pe_edi_number
                        move.l10n_pe_edi_reversal_date = move.reversed_entry_id.invoice_date'''

    # Default invoice report for Electronic invoice    
    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.company_id.country_id.code == 'PE' and self.l10n_pe_dte_is_einvoice:
            return 'l10n_pe_edi_extended.report_einvoice_document'
        return super()._get_name_invoice_report()
    
    def l10n_pe_dte_credit_amount_single_fee(self):
        return self.l10n_pe_dte_amount_total-self.l10n_pe_dte_amount_retention

    def l10n_pe_dte_compute_fees(self):
        fees = []
        invoice_date = self.invoice_date.strftime('%Y-%m-%d')
        invoice_date_due = self.invoice_date_due.strftime('%Y-%m-%d')
        if self.move_type=='out_invoice':
            self.invoice_payment_fee_ids.unlink()
        if invoice_date!=invoice_date_due:
            if self.invoice_payment_term_id:
                payment_lines = self.invoice_payment_term_id.compute(self.l10n_pe_dte_credit_amount_single_fee(), date_ref=self.invoice_date, currency=self.currency_id)
                sequence = 1
                for payment_line in payment_lines:
                    if invoice_date==payment_line[0]:
                        continue
                    fees.append([0, 0, {
                        'sequence':sequence,
                        'amount_total': payment_line[1],
                        'date_due': payment_line[0],
                        'currency_id':self.currency_id.id,
                    }])
                    sequence+=1
            else:
                fees.append([0, 0, {
                    'sequence':1,
                    'amount_total': self.l10n_pe_dte_credit_amount_single_fee(),
                    'date_due': invoice_date_due,
                    'currency_id':self.currency_id.id,
                }])
        
        self.write({
            'invoice_payment_fee_ids': fees
        })

    def _get_last_sequence_domain(self, relaxed=False):
        # OVERRIDE
        where_string, param = super()._get_last_sequence_domain(relaxed=relaxed)
        if self.journal_id.l10n_pe_is_dte:
            where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
            if not relaxed:
                param['anti_regex'] = 'NULL'
        return where_string, param

    def _get_starting_sequence(self):
        # OVERRIDE
        if self.journal_id.l10n_pe_is_dte and self.l10n_latam_document_type_id:
            doc_mapping = {'01': 'FFI', '03': 'BOL', '07': 'CNE', '08': 'NDI'}
            middle_code = self.l10n_latam_document_type_id.l10n_pe_sequence_prefix
            # TODO: maybe there is a better method for finding decent 3nd journal default invoice names
            if self.journal_id.code != 'INV':
                middle_code = middle_code[:1] + self.journal_id.code[:3]
            return "%s %s-00000000" % (self.l10n_latam_document_type_id.doc_code_prefix, middle_code)

        return super()._get_starting_sequence()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_pe_dte_allowance_charge_reason_code = fields.Selection(
        selection=[
            ('02', 'Descuentos globales que afectan la base imponible del IGV/IVAP'),
            ('03', 'Descuentos globales que no afectan la base imponible del IGV/IVAP'),
            ('04', 'Descuentos globales por anticipos gravados que afectan la base imponible del IGV/IVAP'),
            ('05', 'Descuentos globales por anticipos exonerados'),
            ('06', 'Descuentos globales por anticipos inafectos'),
            ('20', 'Anticipo de ISC'),
            ('45', 'FISE'),
            ('46', 'Recargo al consumo y/o propinas'),
            ('49', 'Cargos globales que afectan la base imponible del IGV/IVAP'),
            ('50', 'Cargos globales que no afectan la base imponible del IGV/IVAP'),
            ('51', 'Percepción venta interna'),
            ('52', 'Percepción a la adquisición de combustible'),
            ('53', 'Percepción realizada al agente de percepción con tasa especial'),
            ('61', 'Retención de renta por anticipos'),
            ('62', 'Retención del IGV'),
            ('63', 'Rentención de renta de segunda categoría'),
        ],
        string="Allowance or Charge reason",
        default=False,
        help="Catalog 53 of possible reasons of discounts")
    l10n_pe_dte_price_base = fields.Monetary(string='Subtotal without discounts', digits=(9,10), store=True, readonly=True, currency_field='currency_id', help="Total amount without discounts and taxes")
    l10n_pe_dte_price_unit_excluded = fields.Float(string='Price unit excluded', digits=(9,10), store=True, readonly=True, currency_field='currency_id', help="Price unit without taxes")
    l10n_pe_dte_price_unit_included = fields.Float(string='Price unit IGV included', digits=(9,10), store=True, readonly=True, currency_field='currency_id', help="Price unit with IGV included")
    l10n_pe_dte_amount_discount = fields.Monetary(string='Amount discount before taxes', store=True, readonly=True, currency_field='currency_id', help='Amount discount before taxes')
    l10n_pe_dte_amount_free = fields.Monetary(string='Amount free', digits=(9,10), store=True, readonly=True, currency_field='currency_id', help='amount calculated if the line id for free product')
    l10n_pe_dte_free_product = fields.Boolean('Free', store=True, readonly=True, default=False, help='Is free product?')
    l10n_pe_dte_igv_amount = fields.Monetary(string='IGV amount',store=True, readonly=True, currency_field='currency_id', help="Total IGV amount")
    l10n_pe_dte_isc_amount = fields.Monetary(string='ISC amount',store=True, readonly=True, currency_field='currency_id', help="Total ISC amount")
    l10n_pe_dte_icbper_amount = fields.Monetary(string='ICBPER amount',store=True, readonly=True, currency_field='currency_id', help="Total ICBPER amount")
    #l10n_pe_dte_per_base = fields.Monetary(string='PERCEPTION base',store=True, readonly=True, currency_field='currency_id', help="Total PERCEPTION base")
    #l10n_pe_dte_per_amount = fields.Monetary(string='PERCEPTION amount',store=True, readonly=True, currency_field='currency_id', help="Total PERCEPTION amount")
    l10n_pe_dte_advance_line = fields.Boolean('Advance', store=True, default=False, help='Is advance line?')
    l10n_pe_dte_advance_invoice_id = fields.Many2one('account.move', string='Advance Invoice', store=True, readonly=True, help='Invoices related to the advance regualization')
    l10n_pe_dte_advance_type = fields.Selection([('02','Factura'),('03','Boleta de venta')], string='Advance Type')
    l10n_pe_dte_advance_serial = fields.Char('Advance serial')
    l10n_pe_dte_advance_number = fields.Char('Advance number')
    l10n_pe_dte_advance_date = fields.Date('Advance date')
    l10n_pe_dte_advance_amount = fields.Monetary(string='Advance amount',store=True, readonly=True, currency_field='currency_id', help="Total Advance amount")

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.
        '''
        res = super(AccountMoveLine, self)._get_price_total_and_subtotal_model(price_unit, quantity, discount, currency, product, partner, taxes, move_type)
        l10n_pe_dte_price_base = quantity * price_unit
        l10n_pe_dte_price_unit_included = price_unit
        l10n_pe_dte_igv_amount = 0.0
        l10n_pe_dte_isc_amount = 0.0
        l10n_pe_dte_icbper_amount = 0.0
        #l10n_pe_dte_per_amount = 0.0
        #l10n_pe_dte_per_base = 0.0
        tax_is_free = False
        if taxes:
            # Compute taxes for all line
            taxes_res = taxes._origin.compute_all(price_unit , quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            l10n_pe_dte_price_unit_excluded = l10n_pe_dte_price_unit_excluded_signed = quantity != 0 and taxes_res['total_excluded']/quantity or 0.0
            res['l10n_pe_dte_price_unit_excluded'] = l10n_pe_dte_price_unit_excluded   
            # Price unit whit all taxes included
            l10n_pe_dte_price_unit_included = l10n_pe_dte_price_unit_included_signed = quantity != 0 and taxes_res['total_included']/quantity or 0.0
            res['l10n_pe_dte_price_unit_included'] = l10n_pe_dte_price_unit_included     

            # Amount taxes after dicounts, return a dict with all taxes applied with discount incluided
            taxes_discount = taxes.compute_all(price_unit * (1 - (discount or 0.0) / 100.0), currency, quantity, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))  
            
            #~ With IGV taxes
            igv_taxes_ids = taxes.filtered(lambda r: r.tax_group_id.name == 'IGV')
            if igv_taxes_ids:
                # Compute taxes per unit
                l10n_pe_dte_price_unit_included = l10n_pe_dte_price_unit_included_signed = quantity != 0 and taxes_res['total_included']/quantity or 0.0 if igv_taxes_ids else price_unit
                res['l10n_pe_dte_price_unit_included'] = l10n_pe_dte_price_unit_included
                #~ IGV amount after discount for all line                
                l10n_pe_dte_igv_amount = sum( r['amount'] for r in taxes_discount['taxes'] if r['id'] in igv_taxes_ids.ids) 
            l10n_pe_dte_price_base = l10n_pe_dte_price_base_signed = taxes_res['total_excluded']
            res['l10n_pe_dte_price_base'] = l10n_pe_dte_price_base 

            #~ With ISC taxes
            isc_taxes_ids = taxes.filtered(lambda r: r.tax_group_id.name == 'ISC')
            if isc_taxes_ids:
                #~ ISC amount after discount for all line
                l10n_pe_dte_isc_amount = sum( r['amount'] for r in taxes_discount['taxes'] if r['id'] in isc_taxes_ids.ids) 

            #~ With ICBPER taxes
            icbper_taxes_ids = taxes.filtered(lambda r: r.tax_group_id.name == 'ICBPER')
            if icbper_taxes_ids:
                #~ ICBPER amount after discount for all line
                l10n_pe_dte_icbper_amount = sum( r['amount'] for r in taxes_discount['taxes'] if r['id'] in icbper_taxes_ids.ids) 

            #~ With PER taxes (Perception)
            per_taxes_ids = taxes.filtered(lambda r: r.tax_group_id.name == 'PER')
            if per_taxes_ids:
                l10n_pe_dte_per_amount = sum( r['amount'] for r in taxes_discount['taxes'] if r['id'] in per_taxes_ids.ids)
                res['l10n_pe_dte_price_unit_included']-=l10n_pe_dte_per_amount/quantity

            #~ With OTHER taxes (Perception)
            other_taxes_ids = taxes.filtered(lambda r: r.tax_group_id.name == 'OTROS')
            if other_taxes_ids:
                l10n_pe_dte_other_amount = sum( r['amount'] for r in taxes_discount['taxes'] if r['id'] in other_taxes_ids.ids)
                res['l10n_pe_dte_price_unit_included']-=l10n_pe_dte_other_amount/quantity

            #~ With GRA taxes (Free)
            gra_taxes_ids = taxes.filtered(lambda r: r.tax_group_id.name == 'GRA')
            if gra_taxes_ids:
                tax_is_free = True

        #~ Free amount
        if discount >= 100.0 or tax_is_free:  
            l10n_pe_dte_igv_amount = 0.0   # When the product is free, igv = 0
            #l10n_pe_dte_isc_amount = 0.0   # When the product is free, isc = 0
            l10n_pe_dte_icbper_amount = 0.0   # When the product is free, icbper = 0
            l10n_pe_dte_amount_discount = 0.0  # Although the product has 100% discount, the amount of discount in a free product is 0             
            l10n_pe_dte_free_product = True
            l10n_pe_dte_amount_free = l10n_pe_dte_price_unit_excluded * quantity
        else:
            l10n_pe_dte_amount_discount = (l10n_pe_dte_price_unit_included * discount * quantity) / 100
            l10n_pe_dte_free_product = False
            l10n_pe_dte_amount_free = 0.0

        res['l10n_pe_dte_amount_discount'] = l10n_pe_dte_amount_discount
        res['l10n_pe_dte_amount_free'] = l10n_pe_dte_amount_free
        res['l10n_pe_dte_free_product'] = l10n_pe_dte_free_product
        res['l10n_pe_dte_igv_amount'] = l10n_pe_dte_igv_amount            
        res['l10n_pe_dte_isc_amount'] = l10n_pe_dte_isc_amount            
        res['l10n_pe_dte_icbper_amount'] = l10n_pe_dte_icbper_amount
        #res['l10n_pe_dte_per_amount'] = l10n_pe_dte_per_amount
        #res['l10n_pe_dte_per_base'] = l10n_pe_dte_per_base
        return res

    def _l10n_pe_prepare_dte_lines(self):
        igv_type = '10'
        isc_type = ''
        is_detraction_full_line = False
        is_other_charge = False
        if self.discount >= 100.0:  
            # Discount >= 100% means the product is free and the IGV type should be 'No onerosa' and 'taxed'
            igv_type = self.tax_ids.filtered(lambda r: r.l10n_pe_edi_tax_code == '9996')[0].l10n_pe_edi_igv_type
        elif any(tax.l10n_pe_edi_tax_code in ['1000'] for tax in self.tax_ids):
            # Tax with code '1000' is IGV
            igv_type = '10'
        elif all(tax.l10n_pe_edi_tax_code in ['9997'] for tax in self.tax_ids):
            # Tax with code '9997' is Exonerated
            igv_type = '20'
        elif all(tax.l10n_pe_edi_tax_code in ['9998'] for tax in self.tax_ids):
            # Tax with code '9998' is Unaffected
            igv_type = '30'
        elif all(tax.l10n_pe_edi_tax_code in ['9995'] for tax in self.tax_ids):
            # Tax with code '9995' is for Exportation
            igv_type = '40'
        elif any(tax.l10n_pe_edi_tax_code in ['9996'] for tax in self.tax_ids):
            # Tax with code '9996' is for Free operations
            igv_type = self.tax_ids.filtered(lambda r: r.l10n_pe_edi_tax_code == '9996')[0].l10n_pe_edi_igv_type
        if any(tax.l10n_pe_edi_tax_code in ['2000'] for tax in self.tax_ids):
            isc_type = self.tax_ids.filtered(lambda r: r.l10n_pe_edi_tax_code == '2000')[0].l10n_pe_edi_isc_type
        
        if any(tax.tax_group_id.name=='PERG' and tax.amount==0 for tax in self.tax_ids) and len(self.tax_ids)==1:
            is_detraction_full_line = True

        if any(tax.tax_group_id.name=='OTROS' for tax in self.tax_ids):
            is_other_charge = False

        default_uom = 'NIU'
        if self.product_id.type=='service':
            default_uom = 'ZZ'

        line = {
            'product_code': self.product_id.default_code if self.product_id.default_code else '',
            'product_sunat_code': self.product_id.l10n_pe_edi_unspsc if self.product_id.l10n_pe_edi_unspsc else '',
            'name': self.name.replace('[%s] ' % self.product_id.default_code,'') if self.product_id else self.name,
            'quantity': abs(self.quantity),
            'uom_code': self.product_uom_id.l10n_pe_edi_unece if self.product_uom_id.l10n_pe_edi_unece else default_uom,
            'price_base':self.l10n_pe_dte_price_base,
            'price_subtotal': self.price_subtotal,
            'price_total': self.price_total if is_other_charge else self.price_subtotal+self.l10n_pe_dte_igv_amount+self.l10n_pe_dte_isc_amount+self.l10n_pe_dte_icbper_amount,#self.price_total
            'price_unit_included': self.l10n_pe_dte_price_unit_included,
            'price_unit_excluded': self.l10n_pe_dte_price_unit_excluded,
            'igv_type': igv_type,
            'isc_type': isc_type,
            'igv_amount': self.l10n_pe_dte_igv_amount,
            'isc_amount': self.l10n_pe_dte_isc_amount,
            'icbper_amount': self.l10n_pe_dte_icbper_amount,
            'free_amount': self.l10n_pe_dte_price_unit_included*self.quantity if self.l10n_pe_dte_free_product else 0,
            'discount_base':0,
            'discount_amount':0,
            'discount':self.l10n_pe_dte_amount_discount,
            'is_free':self.l10n_pe_dte_free_product,
            'is_detraction_full_line': is_detraction_full_line,
        }
        if self.discount>0 and self.discount<100:
            line['discount_type']='00'
            line['discount_factor']=(self.discount or 0.0) / 100.0
            line['discount_base']=self.price_subtotal/(1.0 - line['discount_factor'])
            line['discount_amount']=line['discount_base'] * line['discount_factor']
        if self.l10n_pe_dte_advance_line:
            line['advance_line'] = self.l10n_pe_dte_advance_line
            line['advance_type'] = self.l10n_pe_dte_advance_type
            line['advance_serial'] = self.l10n_pe_dte_advance_serial
            line['advance_number'] = self.l10n_pe_dte_advance_number
            line['advance_amount'] = self.l10n_pe_dte_price_base
            if self.l10n_pe_dte_advance_date:
                line['advance_date'] = self.l10n_pe_dte_advance_date.strftime('%Y-%m-%d')
        return line


    def show_detail_anticipo(self):
        #self.ensure_one()
        #raise ValueError(self.name)

        view = self.env.ref('l10n_pe_edi_extended.detail_anticipo', False)

        # picking_type_id = self.picking_type_id or self.picking_id.picking_type_id
        return {
            'name': self.name ,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }