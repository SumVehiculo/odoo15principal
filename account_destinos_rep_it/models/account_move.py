# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	def ver_destinos(self):

		sql = """
			DROP VIEW IF EXISTS account_des_move;
			CREATE OR REPLACE view account_des_move as (SELECT row_number() OVER () AS id, * from get_destinos(%s,%s,%d) where am_id = %d)""" % (
				self.date.strftime('%Y%m'),
				self.date.strftime('%Y%m'),
				self.company_id.id,
				self.id
			)

		self.env.cr.execute(sql)

		self.env.cr.execute("SELECT * FROM account_des_move")
		res = self.env.cr.dictfetchall()

		if len(res) <= 0:
			raise UserError("No hay ningun destino.")
		else:
			return {
			'name': 'Destinos',
			'type': 'ir.actions.act_window',
			'res_model': 'account.des.move',
			'view_mode': 'tree',
			'view_type': 'form',
			'target': 'new',
		}