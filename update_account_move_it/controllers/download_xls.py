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
	
	@http.route('/web/binary/download_template_update_journal_entry_example', type='http', auth="public")
	def download_template_update_journal_entry_example(self, **kw):

		invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','update_journal_entry_example.xlsx')])
		filecontent = invoice_xls.datas
		filename = 'Actualizar datos adicionales.xlsx'
		filecontent = base64.b64decode(filecontent)
			

		return request.make_response(filecontent,
			[('Content-Type', 'application/octet-stream'),
			('Content-Disposition', content_disposition(filename))])

	@http.route('/web/binary/download_template_add_doc_invoice_relac_example', type='http', auth="public")
	def download_template_add_doc_invoice_relac_example(self, **kw):

		invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','add_doc_invoice_relac_example.xlsx')])
		filecontent = invoice_xls.datas
		filename = 'Agregar Documentos Relacionados.xlsx'
		filecontent = base64.b64decode(filecontent)
			

		return request.make_response(filecontent,
			[('Content-Type', 'application/octet-stream'),
			('Content-Disposition', content_disposition(filename))])