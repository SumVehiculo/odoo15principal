# -*- encoding: utf-8 -*-
from odoo import fields, models

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    partner_id = fields.Many2one('res.partner', string='Partner')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('res.partner', related='vehicle_id.driver_id')