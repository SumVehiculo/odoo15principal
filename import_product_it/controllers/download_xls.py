# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition
import base64

class Download_xls(http.Controller):
	
	@http.route('/web/binary/download_product_import_template', type='http', auth="public")
	def download_product_import_template(self, **kw):

		invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','product_import_template.xlsx')])
		filecontent = invoice_xls.datas
		filename = 'Plantilla Importacion Producto.xlsx'
		filecontent = base64.b64decode(filecontent)
			

		return request.make_response(filecontent,
			[('Content-Type', 'application/octet-stream'),
			('Content-Disposition', content_disposition(filename))])