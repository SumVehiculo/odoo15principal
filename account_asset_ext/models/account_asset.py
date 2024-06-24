# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class account_asset(models.Model):
    _inherit = 'account.asset'
    

    partner_id = fields.Many2one('res.partner', string='Socio')