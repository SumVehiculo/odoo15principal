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

    l10n_pe_dte_conflux_uid = fields.Char(string='DTE Conflux UID', copy=False)

    def l10n_pe_dte_action_check(self):
        super(LogisticDespatch, self).l10n_pe_dte_action_check()
        ir_attach = self.env['ir.attachment']
        for move in self.filtered(
                lambda x: x.company_id.country_id == self.env.ref('base.pe') and
                            x.company_id.l10n_pe_dte_service_provider in ['CONFLUX'] and 
                            x.journal_id.l10n_pe_is_dte):
            if move.l10n_pe_dte_status in ('ask_for_status','rejected'):
                data_dict = {}
                response = self._send_json_to_conflux(token=move.company_id.l10n_pe_dte_conflux_token, method="get", data_dict=data_dict, ws_url='http://einvoice.conflux.pe/api/v/1/account_einvoice/despatch/%s/status/' % move.l10n_pe_dte_conflux_uid)
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
                                    "name":"R-%s-%s-%s.xml" % (move.company_id.vat, '09', response[1].get('nombre')),
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
                                    "name":"R-%s-%s.zip" % (move.company_id.vat, move.id),
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
        res = super(LogisticDespatch, self).l10n_pe_dte_action_cancel()
        for move in self.filtered(
                lambda x: x.company_id.country_id == self.env.ref('base.pe') and
                            x.company_id.l10n_pe_dte_service_provider in ['CONFLUX'] and 
                            x.journal_id.l10n_pe_is_dte):
            data_dict = move._l10n_pe_prepare_dte_void_conflux()
            log.info(data_dict)
            move.button_cancel()
            if move.state=="cancel":
                move.write({
                    "l10n_pe_dte_void_status":'accepted',
                    "l10n_pe_dte_cancel_reason": self._context.get('reason',_('Null document'))
                })
                message = _("Despatch <span style='color: #21b799;'>%s</span> nulled") % (move.name)
                move.message_post(body=message)
            else:
                raise UserError(_("It's not possible to cancel the despatch. Please check the log details \n Despatch: %s \n ")% (move.name))
        return res
    
    def l10n_pe_dte_action_send(self):
        super(LogisticDespatch, self).l10n_pe_dte_action_send()
        ir_attach = self.env['ir.attachment']
        for despatch in self.filtered(
                lambda x: x.company_id.country_id == self.env.ref('base.pe') and
                            x.company_id.l10n_pe_dte_service_provider in ['CONFLUX'] and 
                            x.journal_id.l10n_pe_is_dte):
            if not despatch.l10n_pe_dte_conflux_uid:
                despatch.verify_partner_company()
                data_dict = despatch._l10n_pe_prepare_dte_conflux()
                response = self._send_json_to_conflux(token=despatch.company_id.l10n_pe_dte_conflux_token, data_dict=data_dict)
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

                        _despatch = {
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
                            _despatch.update({
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
                            _despatch.update({
                                "l10n_pe_dte_cdr_file":cdr_attach.id,
                                "l10n_pe_dte_status_response": '%s - %s' % (response[1]["success"]["data"].get('sunat_description', ''), response[1]["success"]["data"].get('sunat_note', '')) if has_sunat_notes else '',
                                "l10n_pe_dte_status":"accepted",
                            })
                        despatch.write(_despatch)
                    else:
                        raise ValidationError('%s\n\nInformación técnica:\n\n %s' % (response[1]["error"]["message"], json.dumps(response[1]["error"])))
                        #raise UserError('%s, explain: %s' % (response[1]["error"]["message"], json.dumps(response[1]["error"])))
                else:
                    raise UserError(response[1])
    
    def _l10n_pe_prepare_dte_conflux(self):
        base_dte = self._l10n_pe_prepare_dte()
        conflux_dte = base_dte
        return conflux_dte

    def _l10n_pe_prepare_dte_void_conflux(self):
        conflux_dte_void = {
            'id': self.l10n_pe_dte_conflux_uid
        }
        return conflux_dte_void

    def _send_json_to_conflux(self, token="", method="post", ws_url='https://einvoice.conflux.pe/api/v/1/account_einvoice/despatch/', data_dict=None):
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