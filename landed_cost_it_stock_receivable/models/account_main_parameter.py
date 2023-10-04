# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	partner_landed_cost_existences_id = fields.Many2one('res.partner', string='Contacto para Existencia por Recibir')