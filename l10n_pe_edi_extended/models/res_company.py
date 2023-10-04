# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import logging
log = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_pe_dte_service_provider = fields.Selection([
        ('SUNATTEST', 'SUNAT - Test'),
        ('SUNAT', 'SUNAT - Production')], 'DTE Service Provider',
        help='Please select your company service provider for DTE service.')
    l10n_pe_dte_resolution_number = fields.Char(
        'SUNAT Exempt Resolution Number',
        help='This value must be provided and must appear in your pdf or printed tribute document, under the '
            'electronic stamp to be legally valid.')
    l10n_pe_dte_authorization_message = fields.Char(
        'SUNAT Exempt Authorization Message',
        help='This value must be provided and must appear in your pdf or printed tribute document, under the '
            'electronic stamp to be legally valid.')
    l10n_pe_dte_control_url = fields.Char(
        'DTE Control URL',
        help='This value must be provided and must appear in your pdf or printed tribute document, under the '
            'electronic stamp to be legally valid.')
    l10n_pe_dte_send_interval_unit = fields.Selection([
        ('immediately', 'Immediately'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily')],
        default='immediately', string='Send DTE:Interval Unit')
    l10n_pe_dte_send_next_execution_date = fields.Datetime(string="Send DTE:Next Execution")
    l10n_pe_dte_check = fields.Boolean('Check DTE to PSE/OSE')
    l10n_pe_dte_check_interval_unit = fields.Selection([
        ('hourly', 'Hourly'),
        ('daily', 'Daily')],
        default='daily', string='Check DTE:Interval Unit')
    l10n_pe_dte_check_next_execution_date = fields.Datetime(string="Check DTE:Next Execution")

    def run_send_invoice(self):
        """ This method is called from a cron job to send the invoices to PSE/OSE.
        """
        records = self.search([('l10n_pe_dte_send_next_execution_date', '>=', fields.Datetime.now())])
        if records:
            to_update = self.env['res.company']
            for record in records:
                if record.l10n_pe_dte_send_interval_unit == 'hourly':
                    next_update = relativedelta(hours=+1)
                elif record.l10n_pe_dte_send_interval_unit == 'daily':
                    next_update = relativedelta(days=+1)
                else:
                    record.l10n_pe_dte_send_next_execution_date = False
                    return
                record.l10n_pe_dte_send_next_execution_date = datetime.now() + next_update
                to_update += record
            to_update.l10n_pe_dte_send_invoices()
    
    def l10n_pe_dte_send_invoices(self):
        for company in self:
            if not company.l10n_pe_dte_send_interval_unit:
                log.info('Send Invoices to PSE/OSE is not active')
                continue
            invoice_ids = self.env['account.move'].search([
                ('l10n_pe_dte_is_einvoice','=',True),
                ('state','not in',['draft','cancel']),
                ('l10n_pe_dte_status','=','not_sent'),
                ('move_type','in',['out_invoice','out_refund']),
                ('company_id','=', company.id)]).sorted('invoice_date')
            for move in invoice_ids:
                try:
                    move.l10n_pe_dte_action_send()
                    self.env.cr.commit()
                    log.debug('Batch of Electronic invoices is sent')
                except Exception:
                    self.env.cr.rollback()
                    self.env.cr.commit()
                    log.exception('Something went wrong on Batch of Electronic invoices')

    def run_check_invoice(self):
        """ This method is called from a cron job to send the invoices to PSE/OSE.
        """
        records = self.search([('l10n_pe_dte_check_next_execution_date', '>=', fields.Datetime.now())])
        if records:
            to_update = self.env['res.company']
            for record in records:
                if record.l10n_pe_dte_check_interval_unit == 'hourly':
                    next_update = relativedelta(hours=+1)
                elif record.l10n_pe_dte_check_interval_unit == 'daily':
                    next_update = relativedelta(days=+1)
                else:
                    record.l10n_pe_dte_check_next_execution_date = False
                    return
                record.l10n_pe_dte_check_next_execution_date = datetime.now() + next_update
                to_update += record
            to_update.l10n_pe_dte_check_invoices()
    
    def l10n_pe_dte_check_invoices(self):
        for company in self:
            if not company.l10n_pe_dte_check:
                log.info('Check Invoices on PSE/OSE is not active')
                continue
            invoice_ids = self.env['account.move'].search([
                ('l10n_pe_dte_is_einvoice','=',True),
                ('state','not in',['draft','cancel']),
                ('l10n_pe_dte_status','=','ask_for_status'),
                ('move_type','in',['out_invoice','out_refund']),
                ('company_id','=', company.id)]).sorted('invoice_date')
            for move in invoice_ids:
                try:
                    move.l10n_pe_dte_action_check()
                    self.env.cr.commit()
                    log.debug('Batch of Electronic invoices is checked')
                except Exception:
                    self.env.cr.rollback()
                    self.env.cr.commit()
                    log.exception('Something went wrong on Check Status of Electronic invoices')