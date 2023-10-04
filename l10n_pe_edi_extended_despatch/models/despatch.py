# -*- encoding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import requests
import json
import datetime

import logging
log = logging.getLogger(__name__)


class LogisticDespatch(models.Model):
    _inherit = 'logistic.despatch'

    @api.model
    def get_l10n_pe_dte_shipment_reason(self):
        lst = []
        lst.append(("01", "Venta"))
        lst.append(("02", "Compra"))
        lst.append(("03", "Venta con entrega a terceros"))
        lst.append(("04", "Traslado entre establecimientos de la misma empresa"))
        lst.append(("05", "Consignación"))
        lst.append(("06", "Devolución"))
        lst.append(("07", "Recojo de bienes transformados"))
        lst.append(("08", "Importación"))
        lst.append(("09", "Exportación"))
        lst.append(("13", "Otros"))
        lst.append(("14", "Venta sujeta a confirmación del comprador"))
        lst.append(("17", "Traslado de bienes para transformación"))
        lst.append(("18", "Traslado emisor itinerante CP"))
        return lst

    @api.model
    def get_l10n_pe_dte_transport_mode(self):
        lst = []
        lst.append(("01", "Transporte publico"))
        lst.append(("02", "Transporte privado"))
        return lst

    l10n_latam_country_code = fields.Char("Country Code (LATAM)",
        related='company_id.country_id.code', help='Technical field used to hide/show fields regarding the localization')
    l10n_pe_dte_shipment_reason = fields.Selection('get_l10n_pe_dte_shipment_reason', string='Reason', required=True, readonly=True, states={
                                       'draft': [('readonly', False)], }, default='01')
    l10n_pe_dte_transport_mode = fields.Selection('get_l10n_pe_dte_transport_mode', string='Mode', required=True, readonly=True, states={
                                      'draft': [('readonly', False)], }, default='02')
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
    l10n_pe_dte_cancel_reason = fields.Char(
        string="Cancel Reason", copy=False,
        help="Reason given by the user to cancel this move")
    l10n_pe_dte_partner_status = fields.Selection([
        ('not_sent', 'Not Sent'),
        ('sent', 'Sent'),
    ], string='Partner DTE status', copy=False, help="""
    Status of sending the DTE to the partner:
    - Not sent: the DTE has not been sent to the partner but it has sent to SII.
    - Sent: The DTE has been sent to the partner.""")
    l10n_pe_dte_file = fields.Many2one('ir.attachment', string='DTE file', copy=False)
    l10n_pe_dte_file_link = fields.Char(string='DTE file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_hash = fields.Char(string='DTE Hash', copy=False)
    l10n_pe_dte_pdf_file = fields.Many2one('ir.attachment', string='DTE PDF file', copy=False)
    l10n_pe_dte_pdf_file_link = fields.Char(string='DTE PDF file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_cdr_file = fields.Many2one('ir.attachment', string='CDR file', copy=False)
    l10n_pe_dte_cdr_file_link = fields.Char(string='CDR file', compute='_compute_l10n_pe_dte_links')
    l10n_pe_dte_cdr_void_file = fields.Many2one('ir.attachment', string='CDR Void file', copy=False)
    l10n_pe_dte_cdr_void_file_link = fields.Char(string='CDR Void file', compute='_compute_l10n_pe_dte_links')

    l10n_pe_dte_mtc_authorization = fields.Char('Autorizacion MTC', related='carrier_id.l10n_pe_dte_mtc_authorization', readonly=False)
    l10n_pe_dte_vehicle_2 = fields.Many2one('fleet.vehicle','Vehiculo Secundario 1')
    l10n_pe_dte_vehicle_3 = fields.Many2one('fleet.vehicle','Vehiculo Secundario 2')
    l10n_pe_dte_origin_branch_code = fields.Char(string='Codigo Sucursal')
    l10n_pe_dte_delivery_branch_code = fields.Char(string='Codigo Sucursal')
    l10n_pe_dte_seller_supplier_id = fields.Many2one('res.partner', string='Proveedor')
    l10n_pe_dte_buyer_id = fields.Many2one('res.partner', string='Comprador')
    l10n_pe_dte_reference_ids = fields.One2many('logistic.despatch.reference','despatch_id', string='Documentos de referencia')

    l10n_pe_dte_is_vehicle_m1_l = fields.Boolean(string='Indicador de traslado en vehículos de categoría M1 o L')
    l10n_pe_dte_is_return_with_empty_packages = fields.Boolean(string='Indicador de retorno de vehículo con envases o embalajes vacíos')
    l10n_pe_dte_is_empty_vehicle_return = fields.Boolean(string='Indicador de retorno de vehículo vacío')
    l10n_pe_dte_is_transport_total_dam_ds = fields.Boolean(string='Indicador de traslado total de la DAM o la DS')
    l10n_pe_dte_is_carrier_vehicle_and_driver = fields.Boolean(string='Indicador de registro de vehículos y conductores del transportista')
    l10n_pe_dte_transport_event_type = fields.Boolean(string='Tipo de evento')

    l10n_pe_dte_invoice_number = fields.Char(string='Numero de Factura')
    l10n_pe_dte_is_einvoice = fields.Boolean('Is E-invoice')

    def _compute_l10n_pe_dte_links(self):
        for move in self:
            move.l10n_pe_dte_file_link = move.l10n_pe_dte_file.url if move.l10n_pe_dte_file else None
            move.l10n_pe_dte_pdf_file_link = move.l10n_pe_dte_pdf_file.url if move.l10n_pe_dte_pdf_file else None
            move.l10n_pe_dte_cdr_file_link = move.l10n_pe_dte_cdr_file.url if move.l10n_pe_dte_cdr_file else None
            move.l10n_pe_dte_cdr_void_file_link = move.l10n_pe_dte_cdr_void_file.url if move.l10n_pe_dte_cdr_void_file else None

    def action_open(self):
        res = super(LogisticDespatch, self).action_open()
        for move in self:
            if move.journal_id.l10n_pe_is_dte:
                if not self.origin_address_id.zip:
                    raise ValidationError("El ubigeo de la direccion de partida es obligatorio")
                if not self.delivery_address_id.zip:
                    raise ValidationError("El ubigeo de la direccion de llegada es obligatorio")
                move.l10n_pe_dte_is_einvoice = True
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
        sequence = self.name.split('-')
        serial = sequence[0]
        number = sequence[1]

        _despatch = {
            'enviar': True,
            'serie': serial,
            'numero': number,
            'nombre_de_archivo': '%s-09-%s' % (self.company_id.vat,self.name),
            'motivo_de_envio': self.l10n_pe_dte_shipment_reason,
            'modo_de_transporte': self.l10n_pe_dte_transport_mode,
            'tipo_de_guia': '09',
            'informacion_de_envio': self.l10n_pe_dte_shipment_reason,

            'receptor_denominacion': self.partner_id.name,
            'receptor_tipo_de_documento': self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            'receptor_numero_de_documento': self.partner_id.vat,
            'receptor_direccion': self.partner_id.street,

            'fecha_de_emision': self.issue_date.strftime("%Y-%m-%d"),
            'fecha_de_inicio': self.start_date.strftime("%Y-%m-%d"),

            'peso': self.total_weight,
            'unidad_de_medida_peso': 'KGM',
            'bultos_paquetes': self.packages,
            'origen_establecimiento_anexo': self.l10n_pe_dte_origin_branch_code or None,
            'origen_ubigeo': self.origin_address_id.zip.replace('PE', '') if self.origin_address_id.zip else False,
            #'origen_direccion': self.origin_address_id.street,
            'origen_direccion': (self.origin_address_id.street_name or '') \
                                + (self.origin_address_id.street_number and (' ' + self.origin_address_id.street_number) or '') \
                                + (self.origin_address_id.street_number2 and (' ' + self.origin_address_id.street_number2) or '') \
                                + (self.origin_address_id.street2 and (' ' + self.origin_address_id.street2) or '') \
                                + (self.origin_address_id.l10n_pe_district and ', ' + self.origin_address_id.l10n_pe_district.name or '') \
                                + (self.origin_address_id.city_id and ', ' + self.origin_address_id.city_id.name or '') \
                                + (self.origin_address_id.state_id and ', ' + self.origin_address_id.state_id.name or '') \
                                + (self.origin_address_id.country_id and ', ' + self.origin_address_id.country_id.name or ''),
            'destino_establecimiento_anexo': self.l10n_pe_dte_delivery_branch_code or None,
            'destino_ubigeo': self.delivery_address_id.zip.replace('PE', '') if self.delivery_address_id.zip else False,
            #'destino_direccion': self.delivery_address_id.street ,
            'destino_direccion': (self.delivery_address_id.street_name or '') \
                                + (self.delivery_address_id.street_number and (' ' + self.delivery_address_id.street_number) or '') \
                                + (self.delivery_address_id.street_number2 and (' ' + self.delivery_address_id.street_number2) or '') \
                                + (self.delivery_address_id.street2 and (' ' + self.delivery_address_id.street2) or '') \
                                + (self.delivery_address_id.l10n_pe_district and ', ' + self.delivery_address_id.l10n_pe_district.name or '') \
                                + (self.delivery_address_id.city_id and ', ' + self.delivery_address_id.city_id.name or '') \
                                + (self.delivery_address_id.state_id and ', ' + self.delivery_address_id.state_id.name or '') \
                                + (self.delivery_address_id.country_id and ', ' + self.delivery_address_id.country_id.name or ''),
            #'observaciones': self.note,
            'traslado_con_vehiculo_m1_l': self.l10n_pe_dte_is_vehicle_m1_l,
            'retorno_con_envases_vacios': self.l10n_pe_dte_is_return_with_empty_packages,
            'retorno_de_vehiculo_vacio': self.l10n_pe_dte_is_empty_vehicle_return,
            'traslado_total_de_dam_ds': self.l10n_pe_dte_is_transport_total_dam_ds,
            'vehiculo_y_conductor_de_transportista': self.l10n_pe_dte_is_carrier_vehicle_and_driver,
            'tipo_de_evento': self.l10n_pe_dte_transport_event_type or None,
            'items': []
        }
        if self.l10n_pe_dte_seller_supplier_id:
            _despatch.update({
                'proveedor_denominacion': self.l10n_pe_dte_seller_supplier_id.name,
                'proveedor_tipo_de_documento': self.l10n_pe_dte_seller_supplier_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
                'proveedor_numero_de_documento': self.l10n_pe_dte_seller_supplier_id.vat,
            })
        if self.l10n_pe_dte_buyer_id:
            _despatch.update({
                'comprador_denominacion': self.l10n_pe_dte_buyer_id.name,
                'comprador_tipo_de_documento': self.l10n_pe_dte_buyer_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
                'comprador_numero_de_documento': self.l10n_pe_dte_buyer_id.vat,
            })


        if self.l10n_pe_dte_invoice_number:
            _despatch['numero_de_factura_referencia'] = self.l10n_pe_dte_invoice_number
        if self.note:
            if self.note!='':
                _despatch['observaciones'] = self.note
        if self.vehicle_id:
            _despatch.update({
                'placa_de_vehiculo': self.vehicle_id.license_plate,
            })
        if self.driver_id:
            _despatch.update({
                'placa_de_vehiculo': self.vehicle_id.license_plate,
                'operador_denominacion': self.driver_id.name,
                'operador_tipo_de_documento': self.driver_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
                'operador_numero_de_documeto': self.driver_id.vat,
                'operador_licencia': self.driver_id.logistic_license_number or None,
            })
        if self.carrier_id:
            _despatch.update({
                'portador_denominacion': self.carrier_id.name,
                'portador_tipo_de_documento': self.carrier_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
                'portador_numero_de_documento': self.carrier_id.vat,
                'portador_registro_mtc': self.l10n_pe_dte_mtc_authorization or None,
            })

        if self.l10n_pe_dte_vehicle_2:
            _despatch['placa_de_vehiculo_secundario_1'] = self.l10n_pe_dte_vehicle_2.license_plate
        if self.l10n_pe_dte_vehicle_3:
            _despatch['placa_de_vehiculo_secundario_2'] = self.l10n_pe_dte_vehicle_3.license_plate

        if self.l10n_pe_dte_reference_ids:
            _despatch['documentos_de_referencia'] = []
            for ref in self.l10n_pe_dte_reference_ids:
                _reference = {
                    'numero_de_documento': ref.l10n_latam_document_number,
                    'tipo_de_documento': ref.l10n_latam_document_type_id.code,
                }
                if ref.partner_id:
                    _reference['proveedor_documento_tipo'] = ref.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
                    _reference['proveedor_documento_numero'] = ref.partner_id.vat
                _despatch['documentos_de_referencia'].append(_reference)

        if self.line_ids:
            for line in self.line_ids:
                _item = {
                    'cantidad': line.quantity,
                    'descripcion': line.name.replace('[%s] ' % line.product_id.default_code,'') if line.product_id else line.name,
                    'codigo': line.product_id.default_code or '',
                    'codigo_producto_sunat': line.product_id.l10n_pe_edi_unspsc or '',
					'codigo_gtin': line.product_id.l10n_pe_edi_gtin or '',
                    'codigo_partida_arancelaria': line.product_id.l10n_pe_edi_tariff_code or '',
                    'codigo_dam':line.l10n_pe_dam_ds_code or '',
					'bien_normalizado': line.product_id.l10n_pe_edi_normalized_good,
                    'unidad_de_medida': line.product_id.uom_id.l10n_pe_edi_unece or 'NIU',
                    'peso': line.weight,
                    'unidad_de_medida_peso': self.weight_uom.l10n_pe_edi_unece or 'KGM',
                }
                if _item.get('codigo') == None:
                    _item['codigo'] = ''
                _despatch['items'].append(_item)
        log.info(_despatch)
        return _despatch

    def verify_partner_company(self):
        if self.l10n_pe_dte_shipment_reason == '01' and self.partner_id and self.journal_id.l10n_pe_is_dte:
            if self.partner_id.id == self.company_id.partner_id.id:
                raise ValidationError(
                    "El remitente no puede ser igual al destinatario")

    def verify_address_street(self, address_street):
        new_address = address_street
        new_address = new_address.translate(
            {ord(c): " " for c in "°!@#$%^&*()[]{};:,./<>?\|`~-=_+'"})
        new_address = new_address.strip()
        count_newaddress = len(new_address)
        if count_newaddress > 0:
            if new_address[0] == '\n':
                new_address[0] = ''
            if new_address[count_newaddress-1] == '\n':
                new_address[count_newaddress-1] = ''
        new_address = new_address.replace("ñ", "n")
        new_address = new_address.replace("Ñ", "N")
        new_address = new_address.replace("á", "a")
        new_address = new_address.replace("Á", "A")
        new_address = new_address.replace("é", "e")
        new_address = new_address.replace("É", "E")
        new_address = new_address.replace("í", "i")
        new_address = new_address.replace("Í", "I")
        new_address = new_address.replace("ó", "o")
        new_address = new_address.replace("Ó", "O")
        new_address = new_address.replace("ú", "u")
        new_address = new_address.replace("Ú", "U")
        if len(new_address) > 100:
            new_address = new_address[:100]
        return new_address

    def _get_name_despatch_report(self, report_xml_id):
        self.ensure_one()
        if self.company_id.country_id.code == 'PE':
            custom_report = {
                'logistic.report_despatch_document': 'l10n_pe_edi_extended_despatch.report_despatch_document',
            }
            return custom_report.get(report_xml_id) or report_xml_id
        return super()._get_name_despatch_report(report_xml_id)

    def action_despatch_sent(self):
        """ Open a window to compose an email, with the edi despatch template
            message loaded by default
        """
        res = super(LogisticDespatch, self).action_despatch_sent()
        template = self.env.ref('l10n_pe_edi_extended_despatch.email_template_edi_despatch', raise_if_not_found=False)
        if template:
            res['context'].update({'default_template_id': template and template.id or False})
        return res

class LogisticDespatchLine(models.Model):
    _inherit = 'logistic.despatch.line'

    l10n_pe_dam_ds_code = fields.Char(string='Codigo DAM/DS', help="""Si el motivo de traslado es IMPORTACIÓN debe registrar el siguiente formato en el formulario del código DAM o DS.
        a) Si el tipo de documento relacionado es 50 - Declaración Aduanera de Mercancías el formato sería:
        xxxx(serie)/xxx-xxxx-10-xxxxxx(DAM)
        Ejemplo: 0001/123-1234-10-123456
        b) Si el tipo de documento relacionado es 52 - Declaración Simplificada (DS) el formato sería:
        xxxx(serie)/xxx-xxxx-18-xxxxxx(DS)
        Ejemplo: 0001/123-1234-18-123456
        """)

class LogisticDespatchReference(models.Model):
    _name = 'logistic.despatch.reference'

    despatch_id = fields.Many2one('logistic.despatch')
    partner_id = fields.Many2one('res.partner', string='Cliente/Proveedor')
    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de documento')
    l10n_latam_document_number = fields.Char(string='Nro. Documento')