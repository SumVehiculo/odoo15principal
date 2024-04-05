# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from calendar import *

class HrMainParameter(models.Model):
    _inherit = 'hr.main.parameter'

    # biweekly_advance_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Adelanto Quincena en Pagos a Bancos')
    #journal_bbva = fields.Many2one('account.journal', domain=[('type', '=', 'bank')], string='Diario BBVA')
    #journal_bcp = fields.Many2one('account.journal', domain=[('type', '=', 'bank')], string='Diario BCP')
    #journal_interbank = fields.Many2one('account.journal', domain=[('type', '=', 'bank')], string='Diario Interbank')
    #journal_scotiabank = fields.Many2one('account.journal', domain=[('type', '=', 'bank')], string='Diario Scotiabank')
    journals_banks = fields.Many2many('account.journal',domain=[('type', '=', 'bank')],string='Diarios')
