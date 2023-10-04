# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    l10n_pe_country_code = fields.Char(related='company_id.country_id.code', string='Country Code')
    l10n_pe_dte_service_provider = fields.Selection(related='company_id.l10n_pe_dte_service_provider', readonly=False)
    l10n_pe_dte_resolution_number = fields.Char(related='company_id.l10n_pe_dte_resolution_number', readonly=False)
    l10n_pe_dte_authorization_message = fields.Char(related='company_id.l10n_pe_dte_authorization_message', readonly=False)
    l10n_pe_dte_control_url = fields.Char(related='company_id.l10n_pe_dte_control_url', readonly=False)
    l10n_pe_dte_send_interval_unit = fields.Selection(related='company_id.l10n_pe_dte_send_interval_unit', readonly=False)
    l10n_pe_dte_send_next_execution_date = fields.Datetime(related='company_id.l10n_pe_dte_send_next_execution_date', readonly=False)
    l10n_pe_dte_check = fields.Boolean(related='company_id.l10n_pe_dte_check', readonly=False)
    l10n_pe_dte_check_interval_unit = fields.Selection(related='company_id.l10n_pe_dte_check_interval_unit', readonly=False)
    l10n_pe_dte_check_next_execution_date = fields.Datetime(related='company_id.l10n_pe_dte_check_next_execution_date', readonly=False)

    @api.onchange('l10n_pe_dte_send_interval_unit')
    def onchange_l10n_pe_dte_send_interval_unit(self):
        if self.company_id.l10n_pe_dte_send_next_execution_date:
            return
        if self.l10n_pe_dte_send_interval_unit == 'hourly':
            next_update = relativedelta(hours=+1)
        elif self.l10n_pe_dte_send_interval_unit == 'daily':
            next_update = relativedelta(days=+1)
        else:
            self.l10n_pe_dte_send_next_execution_date = False
            return
        self.l10n_pe_dte_send_next_execution_date = datetime.now() + next_update

    def update_l10n_pe_dte_send_manually(self):
        self.ensure_one()
        self.company_id.run_send_invoice()

    @api.onchange('l10n_pe_dte_check_interval_unit')
    def onchange_l10n_pe_dte_check_interval_unit(self):
        if self.company_id.l10n_pe_dte_check_next_execution_date:
            return
        if self.l10n_pe_dte_check_interval_unit == 'hourly':
            next_update = relativedelta(hours=+1)
        elif self.l10n_pe_dte_check_interval_unit == 'daily':
            next_update = relativedelta(days=+1)
        else:
            self.l10n_pe_dte_check_next_execution_date = False
            return
        self.l10n_pe_dte_check_next_execution_date = datetime.now() + next_update

    def update_l10n_pe_dte_check_manually(self):
        self.ensure_one()
        self.company_id.run_check_invoice()