# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CountryState(models.Model):
	_inherit = 'res.country.state'
	
	state_id = fields.Many2one('res.country.state',string='Departamento')
	province_id = fields.Many2one('res.country.state',string='Provincia')