# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition
import base64
import os, os.path
import csv
from os import listdir
import sys

class Download_xls(http.Controller):
	
	@http.route('/web/binary/download_template_import_initial', type='http', auth="public")
	def download_template_import_initial(self,model,id, **kw):

		Model = request.env[model]
		res = Model.browse(int(id))

		if res.tipo == 'out':
			invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','import_initial_customer.xlsx')])
			filecontent = invoice_xls.datas
			filename = 'Plantilla Saldos Iniciales por Cobrar.xlsx'
			filecontent = base64.b64decode(filecontent)
		
		else:
			invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','import_initial_supplier.xlsx')])
			filecontent = invoice_xls.datas
			filename = 'Plantilla Saldos Iniciales por Pagar.xlsx'
			filecontent = base64.b64decode(filecontent)
			

		return request.make_response(filecontent,
			[('Content-Type', 'application/octet-stream'),
			('Content-Disposition', content_disposition(filename))])