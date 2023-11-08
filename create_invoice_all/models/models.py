# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, float_is_zero, date_utils, email_split, email_re, html_escape, is_html_empty
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.osv import expression

from datetime import date, timedelta
from collections import defaultdict
from contextlib import contextmanager
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

class AccountMove(models.Model):
	_inherit = "account.move"

	@api.model
	def create(self, vals):
		request = super(AccountMove, self).create(vals)
		for i in request:
			user = self.env.user
			bu = user.has_group('create_invoice_all.access_sale_crea_invoice')			
			if any(move.move_type in ["out_invoice", "in_refund"] for move in request) and bu:
				raise UserError ('Usted no tiene acceso a crear facturas de tipo venta')
			# raise UserError (f'test {i.move_type}')
		return request