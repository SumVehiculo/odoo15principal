# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from psycopg2 import sql, DatabaseError
from odoo.exceptions import ValidationError,UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
	_inherit = 'res.partner'
	
	@api.model_create_multi
	def create(self, vals_list):
		search_partner_mode = self.env.context.get('res_partner_search_mode')
		is_customer = search_partner_mode == 'customer'
		is_supplier = search_partner_mode == 'supplier'
		if search_partner_mode:
			for vals in vals_list:
				if is_customer and 'customer_rank' not in vals:
					vals['is_customer'] = True
				elif is_supplier and 'supplier_rank' not in vals:
					vals['is_supplier'] = True
		return super().create(vals_list)