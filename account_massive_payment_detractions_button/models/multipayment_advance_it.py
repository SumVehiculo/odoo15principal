# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	txt_emited = fields.Boolean(string='TXT Emitido',default=False,copy=False,help="Solo los usuarios dentro del grupo 'Aprobar emision de TXT detraccion (mas de una vez)' podra editar este campo")
	can_edit_txt_emited = fields.Boolean(compute='compute_can_edit_txt_detraction_emited')

	def compute_can_edit_txt_detraction_emited(self):
		self.can_edit_txt_emited  = self.user_has_groups('account_massive_payment_detractions_button.can_edit_txt_emited_detraction_multipayment_group')