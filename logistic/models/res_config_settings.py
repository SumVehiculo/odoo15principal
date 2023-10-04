# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    logistic_picking_done_restrict = fields.Boolean(related='company_id.logistic_picking_done_restrict', readonly=False)