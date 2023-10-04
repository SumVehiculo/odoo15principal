# -*- coding: utf-8 -*-
import requests
import json

from odoo import fields, models, api
from odoo.exceptions import UserError, Warning, ValidationError
from odoo.tools.translate import _
from odoo.tools.misc import formatLang, format_date, get_lang

import logging
log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_pe_dte_conflux_uid = fields.Char(string='DTE Conflux UID', copy=False)

    def l10n_pe_dte_action_check(self):
        super(AccountMove, self).l10n_pe_dte_action_check()
        ir_attach = self.env['ir.attachment']
        for move in self.filtered(
                lambda x: x.company_id.country_id.code == "PE" and
                            x.company_id.l10n_pe_dte_service_provider in ['CONFLUX'] and 
                            x.journal_id.l10n_pe_is_dte):
            if move.l10n_pe_dte_status in ('ask_for_status','rejected') or move.l10n_pe_dte_void_status=='ask_for_status':
                data_dict = {}
                response = self._send_json_to_conflux(token=move.company_id.l10n_pe_dte_conflux_token, method="get", data_dict=data_dict, ws_url='http://einvoice.conflux.pe/api/v/1/account_einvoice/invoice/%s/status/' % move.l10n_pe_dte_conflux_uid)
                if response[0]:
                    log.info(response[1])
                    if response[1].get("estado")=="open":
                        _invoice = {
                            "l10n_pe_dte_status": 'ask_for_status',
                        }
                        if response[1].get("emision_aceptada")==True:
                            _invoice.update({
                                "l10n_pe_dte_status": 'accepted',
                                })
                            has_sunat_notes = False
                            if response[1].get('sunat_note', False) and response[1].get('sunat_note', False)!="":
                                has_sunat_notes = True
                                _invoice.update({
                                    "l10n_pe_dte_status": 'objected',
                                })

                            if response[1].get("enlace_del_cdr"):
                                xml_attach = ir_attach.create({
                                    "name":"R-%s-%s-%s.xml" % (move.company_id.vat, response[1].get('tipo_de_comprobante'), response[1].get('nombre')),
                                    'res_model': self._name,
                                    'res_id': self.id,
                                    "type":'url',
                                    "url":response[1].get("enlace_del_cdr")
                                })
                                _invoice.update({
                                    "l10n_pe_dte_cdr_file":xml_attach.id,
                                    "l10n_pe_dte_status_response": '%s - %s' % (response[1].get('sunat_description', ''), response[1].get('sunat_note', '')) if has_sunat_notes else '',
                                })
                        elif response[1].get("emision_rechazada")==True:
                            _invoice.update({
                                "l10n_pe_dte_status": 'rejected',
                                "l10n_pe_dte_status_response": '%s - %s' % (response[1].get('sunat_description', ''), response[1].get('sunat_note', ''))
                            })
                        move.write(_invoice)
                    elif response[1].get("estado")=="annulled":
                        _invoice = {
                            "l10n_pe_dte_void_status": 'ask_for_status',
                        }
                        if response[1].get("baja_aceptada")==True:
                            _invoice.update({
                                "l10n_pe_dte_void_status": 'accepted',
                                })
                            if response[1].get("enlace_del_cdr"):
                                xml_attach = ir_attach.create({
                                    "name":"R-%s-%s.xml" % (move.company_id.vat, move.id),
                                    'res_model': self._name,
                                    'res_id': self.id,
                                    "type":'url',
                                    "url":response[1].get("enlace_del_cdr")
                                })
                                _invoice.update({
                                    "l10n_pe_dte_cdr_void_file":xml_attach.id,
                                })
                        elif response[1].get("baja_rechazada")==True:
                            _invoice.update({
                                "l10n_pe_dte_void_status": 'rejected',
                            })
                        move.write(_invoice)
                else:
                    raise UserError(response[1])

    def l10n_pe_dte_action_cancel(self):
        res = super(AccountMove, self).l10n_pe_dte_action_cancel()
        for move in self.filtered(
                lambda x: x.company_id.country_id.code == "PE" and
                            x.company_id.l10n_pe_dte_service_provider in ['CONFLUX'] and 
                            x.journal_id.l10n_pe_is_dte):
            if move.move_type in ['out_invoice', 'out_refund'] and move.journal_id.type == 'sale':
                data_dict = move._l10n_pe_prepare_dte_void_conflux()
                log.info(data_dict)
                move.button_cancel()
                if move.state=="cancel":
                    response = self._send_json_to_conflux(token=move.company_id.l10n_pe_dte_conflux_token, data_dict=data_dict, ws_url='https://einvoice.conflux.pe/api/v/1/account_einvoice/void/')
                    if response[0]:
                        log.info(response[1])
                        if response[1].get("status")=="success":
                            move.write({
                                "l10n_pe_dte_void_status":'ask_for_status',
                                "l10n_pe_dte_cancel_reason": self._context.get('reason',_('Null document'))
                            })
                            message = _("Invoice <span style='color: #21b799;'>%s</span> nulled by SUNAT") % (move.ref)
                            move.message_post(body=message)
                        else:
                            raise UserError(response[1]["error"]["message"])
                    else:
                        raise UserError(response[1])
                else:
                    raise UserError(_("It's not possible to cancel the invoice. Please check the log details \n Invoice: %s \n ")% (move.ref))
        return res

    def l10n_pe_dte_action_send(self):
        super(AccountMove, self).l10n_pe_dte_action_send()
        ir_attach = self.env['ir.attachment']
        for move in self.filtered(
                lambda x: x.company_id.country_id.code == "PE" and
                            x.company_id.l10n_pe_dte_service_provider in ['CONFLUX'] and 
                            x.journal_id.l10n_pe_is_dte):
            # generation of customer invoices
            if move.move_type in ['out_invoice', 'out_refund'] and move.journal_id.type == 'sale' and not move.l10n_pe_dte_conflux_uid:
                #move._l10n_cl_edi_post_validation()
                data_dict = move._l10n_pe_prepare_dte_conflux()
                log.info(data_dict)
                response = self._send_json_to_conflux(token=move.company_id.l10n_pe_dte_conflux_token, data_dict=data_dict)
                if response[0]:
                    if response[1].get("status")=="success":
                        xml_attach = ir_attach.create({
                            "name":"%s.xml" % data_dict.get('nombre_de_archivo'),
                            'res_model': self._name,
                            'res_id': self.id,
                            "type":'url',
                            "url":response[1]["success"]["data"].get("enlace_del_xml")
                        })
                        pdf_attach = ir_attach.create({
                            "name":"%s.pdf" % data_dict.get('nombre_de_archivo'),
                            'res_model': self._name,
                            'res_id': self.id,
                            "type":'url',
                            "url":response[1]["success"]["data"].get("enlace_del_pdf")
                        })

                        _invoice = {
                            "l10n_pe_dte_file":xml_attach.id,
                            "l10n_pe_dte_pdf_file":pdf_attach.id,
                            "l10n_pe_dte_hash":response[1]["success"]["data"].get("codigo_hash"),
                            "l10n_pe_dte_status":'ask_for_status',
                            "l10n_pe_dte_partner_status":'not_sent',
                            "l10n_pe_dte_conflux_uid": response[1]["success"]["data"].get("uid"),
                        }

                        has_sunat_notes = False
                        if response[1]["success"]["data"].get('sunat_note', False) and response[1]["success"]["data"].get('sunat_note', False)!="":
                            has_sunat_notes = True
                            _invoice.update({
                                "l10n_pe_dte_status": 'objected',
                            })

                        if response[1]["success"]["data"].get("enlace_del_cdr") and response[1]["success"]["data"].get("emision_aceptada", False):
                            cdr_attach = ir_attach.create({
                                "name":"R-%s.xml" % data_dict.get('nombre_de_archivo'),
                                'res_model': self._name,
                                'res_id': self.id,
                                "type":'url',
                                "url":response[1]["success"]["data"].get("enlace_del_cdr")
                            })
                            _invoice.update({
                                "l10n_pe_dte_cdr_file":cdr_attach.id,
                                "l10n_pe_dte_status_response": '%s - %s' % (response[1]["success"]["data"].get('sunat_description', ''), response[1]["success"]["data"].get('sunat_note', '')) if has_sunat_notes else '',
                                "l10n_pe_dte_status":"accepted",
                            })

                        move.write(_invoice)
                    else:
                        if 'El comprobante fue previamente comunicado hacia nuestros servicios' in response[1]['error']['message']:
                            log.info('comprobante existe en portal de proveedor %s', self.ref)
                            #TODO: Verficacion API REST de comprobante en portal de proveedor
                        raise ValidationError('%s\n\nInformacion tecnica:\n\n %s' % (response[1]["error"]["message"], json.dumps(response[1]["error"])))
                else:
                    raise UserError(response[1])

    def _l10n_pe_prepare_dte_conflux(self):
        base_dte = self._l10n_pe_prepare_dte()
        log.info(base_dte)
        conflux_dte = {
            "enviar":True,
            "nombre_de_archivo": "%s-%s-%s-%s" % (self.company_id.vat, base_dte.get('invoice_type_code'), base_dte.get('dte_serial'), base_dte.get('dte_number')),
            "cliente_tipo_de_documento":base_dte.get('partner_identification_type'),
            "cliente_numero_de_documento":base_dte.get('partner_vat'),
            "cliente_denominacion": base_dte.get('partner_name'),
            "cliente_direccion": base_dte.get('partner_street_address'),
            "fecha_de_emision": base_dte.get('issue_date'),
            "tipo_de_operacion":base_dte.get('operation_type'),
            "tipo_de_comprobante": base_dte.get('invoice_type_code'),
            "serie": base_dte.get('dte_serial'),
            "numero": base_dte.get('dte_number'),
            "forma_de_pago_credito":base_dte.get('payment_term_is_credit'),
            "credito_cuotas":[],
            "moneda": base_dte.get('currency_code'),
            "tipo_de_cambio": round(base_dte.get('currency_rate',1),3),
            "total_gravada": base_dte.get('amount_taxable'),
            "total_exonerada": base_dte.get('amount_exonerated'),
            "total_inafecta": base_dte.get('amount_unaffected'),
            "total_gratuita": base_dte.get('amount_free'),
            "total_exportacion": base_dte.get('amount_export'),
            "total_prepagado": base_dte.get('amount_prepaid'),
            "total_igv": base_dte.get('amount_igv'),
            "total_isc": base_dte.get('amount_isc'),
            "total_icbper": base_dte.get('amount_icbper'),
            #"total_otros": base_dte.get('amount_others'),
            "total": base_dte.get('amount_total'),
            "descuento_base": base_dte.get('discount_global_base'),
            "descuento_importe": base_dte.get('discount_global_amount'),
            "total_otros_cargos": base_dte.get('other_charges'),
            "items": []
        }
        if base_dte.get('service_order', False):
            conflux_dte['orden_compra_servicio'] = base_dte.get('service_order','')
        if base_dte.get('partner_email', False):
            if base_dte.get('partner_email', False)!='':
                conflux_dte['cliente_email'] = base_dte.get('partner_email')
        if base_dte.get('notes', False):
            if base_dte.get('notes', False)!='':
                conflux_dte['observaciones'] = base_dte.get('notes')
        if base_dte.get('seller', False):
            if base_dte.get('seller', False)!='':
                conflux_dte['vendedor'] = base_dte.get('seller')

        if base_dte.get('payment_term', False):
            if base_dte.get('payment_term', False)!='':
                conflux_dte['condiciones_de_pago'] = base_dte.get('payment_term')
        
        if base_dte.get('company_branch_id', False):
            conflux_dte['establecimiento_anexo'] = base_dte.get('company_branch_id')
        if base_dte.get('perception_amount',0)>0 and base_dte.get('perception_base',0)>0:
            conflux_dte['percepcion_tipo'] = base_dte.get('perception_type')
            conflux_dte['percepcion_base_imponible'] = base_dte.get('perception_base',0)
            conflux_dte['total_percepcion'] = base_dte.get('perception_amount',0)
            conflux_dte['total_incluido_percepcion'] = base_dte.get('total_with_perception',0)
            conflux_dte['tipo_de_operacion'] = '2001'
        if conflux_dte.get('descuento_importe',0)>0 and conflux_dte.get('descuento_base',0)>0:
            conflux_dte['descuento_tipo']=base_dte.get('discount_global_type')
            conflux_dte['descuento_factor']=base_dte.get('discount_global_factor')
        if conflux_dte.get('tipo_de_comprobante')=='07':
            conflux_dte['tipo_de_nota_de_credito'] = base_dte.get('credit_note_type')
            conflux_dte['documento_que_se_modifica_tipo'] = base_dte.get('rectification_ref_type')
            conflux_dte['documento_que_se_modifica_numero'] = base_dte.get('rectification_ref_number')
        elif conflux_dte.get('tipo_de_comprobante')=='08':
            conflux_dte['tipo_de_nota_de_debito'] = base_dte.get('debit_note_type')
            conflux_dte['documento_que_se_modifica_tipo'] = base_dte.get('rectification_ref_type')
            conflux_dte['documento_que_se_modifica_numero'] = base_dte.get('rectification_ref_number')
        if base_dte.get('date_due', False):
            conflux_dte['fecha_de_vencimiento'] = base_dte.get('date_due')
        for payment_fee in base_dte.get('payment_term_fees'):
            conflux_dte['credito_cuotas'].append({
                'codigo':payment_fee.get('code'),
                'fecha_de_vencimiento':payment_fee.get('due_date'),
                'importe_a_pagar':payment_fee.get('amount'),
            })
        if base_dte.get('detraction', False):
            conflux_dte["detraccion"]=base_dte.get('detraction')
            conflux_dte["total_detraccion"]=base_dte.get('detraction_amount')
            conflux_dte["porcentaje_detraccion"]=base_dte.get('detraction_percent')
            conflux_dte["codigo_detraccion"]=base_dte.get('detraction_code')
            conflux_dte['medio_de_pago_detraccion']=base_dte.get('detraction_payment_method_code')
            if base_dte.get('detraction_origin_address_zip', False):
                conflux_dte['ubigeo_origen']=base_dte.get('detraction_origin_address_zip')
            if base_dte.get('detraction_origin_address_street', False):
                conflux_dte['direccion_origen']=base_dte.get('detraction_origin_address_street')
            if base_dte.get('detraction_delivery_address_zip', False):
                conflux_dte['ubigeo_destino']=base_dte.get('detraction_delivery_address_zip')
            if base_dte.get('detraction_delivery_address_street', False):
                conflux_dte['direccion_destino']=base_dte.get('detraction_delivery_address_street')
            if base_dte.get('detraction_val_ref_serv_trans', False):
                conflux_dte['val_ref_serv_trans']=base_dte.get('detraction_val_ref_serv_trans')
            if base_dte.get('detraction_val_ref_carga_efec', False):
                conflux_dte['val_ref_carga_efec']=base_dte.get('detraction_val_ref_carga_efec')
            if base_dte.get('detraction_val_ref_carga_util', False):
                conflux_dte['val_ref_carga_util']=base_dte.get('detraction_val_ref_carga_util')
            if base_dte.get('detraction_detalle_viaje', False):
                conflux_dte['detalle_viaje']=base_dte.get('detraction_detalle_viaje')
        if base_dte.get('retention_type', False):
            conflux_dte["retencion_tipo"]=base_dte.get('retention_type')
            conflux_dte["retencion_base_imponible"]=base_dte.get('retention_base')
            conflux_dte["total_retencion"]=base_dte.get('retention_amount')
        if base_dte.get('remission_guides', []):
            conflux_dte['guias'] = []
            for guide in base_dte['remission_guides']:
                conflux_dte['guias'].append({
                    'guia_tipo': guide['type'],
                    'guia_serie_numero': guide['number']
                })
        for item in base_dte.get('items'):
            _item = {
                "codigo":item.get('product_code'),
                "codigo_producto_sunat":item.get('product_sunat_code'),
                "descripcion":item.get('name'),
                "cantidad":item.get('quantity'),
                "unidad_de_medida":item.get('uom_code'),
                "valor_unitario": item.get('price_unit_excluded'),
                "precio_unitario": item.get('price_unit_included') if not item.get('is_free') else item.get('free_amount')/item.get('quantity'),
                "subtotal":item.get('price_subtotal'),
                "total":item.get('price_total'),
                "tipo_de_igv": item.get('igv_type'),
                "igv":item.get('igv_amount'),
                "isc":item.get('isc_amount'),
                "icbper": item.get('icbper_amount'),
                "descuento_base":item.get('discount_base',0),
                "descuento_importe":item.get('discount_amount',0),
                "gratuito":item.get('is_free'),
            }
            if item.get('isc_amount')>0:
                _item['tipo_de_calculo_isc'] = item.get('isc_type')
            if _item.get('descuento_base')>0 and _item.get('descuento_importe')>0:
                _item['descuento_tipo']=item.get('discount_type')
                _item['descuento_factor']=item.get('discount_factor')

            if item.get('advance_line',False):
                _item['anticipo_regularizacion'] = item.get('advance_line',False)
                _item['anticipo_numero_de_documento'] = '%s-%s' % (item.get('advance_serial'), item.get('advance_number'))
                _item['anticipo_tipo_de_documento'] = item.get('advance_type', '01')
                if item.get('advance_date', False):
                    _item['anticipo_fecha'] = item.get('advance_date')
            conflux_dte['items'].append(_item)
        return conflux_dte

    def _l10n_pe_prepare_dte_void_conflux(self):
        conflux_dte_void = {
            'id': self.l10n_pe_dte_conflux_uid
        }
        return conflux_dte_void

    def _send_json_to_conflux(self, token="", method="post", ws_url='https://einvoice.conflux.pe/api/v/1/account_einvoice/invoice/', data_dict=None):
        s = requests.Session()
        if not ws_url:
            return (False, _("Conflux web service url not provided"))
        try:
            if method=='post':
                r = s.post(
                    ws_url,
                    headers={'Authorization': 'Token '+token},
                    json=data_dict)
            else:
                r = s.get(
                    ws_url,
                    headers={'Authorization': 'Token '+token},
                    json=data_dict)
        except requests.exceptions.RequestException as e:
            return (False, e)
        if r.status_code in (200,400):
            try:
                response = json.loads(r.content.decode())
                log.info(response)
            except ValueError as e:
                raise Warning(_("Exception decoding JSON response from Conflux: %s ", e))

            return (True, response)
        else:
            log.info(ws_url)
            log.info(token)
            log.info(data_dict)
            log.info(r.status_code)
            log.info(r.content)
            return (False, _("There's problems to connecte with Conflux Server"))