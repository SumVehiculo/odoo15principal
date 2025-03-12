# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo import tools


class AccountMove(models.Model):
	_inherit = 'account.move'

	payment_method_it = fields.Selection([('01','Efectivo'),
										  ('02','Tarjeta'),
										  ('03','Deposito'),
										  ('04','Transferencia'),
										  ('05','Otros'),
										  ],string='N° de operacion', tracking=True)
	operation_number_it = fields.Text(string='N° de operacion', tracking=True)
	payment_date_it = fields.Date(string='Fecha de pago', tracking=True)