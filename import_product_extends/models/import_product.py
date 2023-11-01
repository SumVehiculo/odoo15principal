from odoo import models, fields, exceptions, api, _
import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
import base64


class ImportProductIt(models.TransientModel):
	_inherit = 'import.product.it'

	def find_category(self, name):
		category_obj = self.env['product.category']
		category_search = category_obj.search([('complete_name','=',name)],limit=1)
		if category_search:
			return category_search
		else:
			raise UserError('No existe una Categoria con el nombre "%s"' % name)