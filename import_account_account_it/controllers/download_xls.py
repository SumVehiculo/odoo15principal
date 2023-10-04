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
	
	@http.route('/web/binary/download_template_account_account', type='http', auth="public")
	def download_template_account_account(self, **kw):

		invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','plantilla_modelo_cuentas.xlsx')])
		filecontent = invoice_xls.datas
		filename = 'Plantilla Plan Contable.xlsx'
		filecontent = base64.b64decode(filecontent)
			

		return request.make_response(filecontent,
			[('Content-Type', 'application/octet-stream'),
			('Content-Disposition', content_disposition(filename))])