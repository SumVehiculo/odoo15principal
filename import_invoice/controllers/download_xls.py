# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition
import base64



class Download_xls(http.Controller):
	
	@http.route('/web/binary/download_document', type='http', auth="public")
	def download_document(self,model,id, **kw):

		Model = request.env[model]
		res = Model.browse(int(id))

		if res.account_opt == 'default':
			if res.type_import in ('out_invoice','out_refund'):
				invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','invoice_customer.xls')])
				filecontent = invoice_xls.datas
				filename = 'Facturas Cliente sin Cuenta.xls'
				filecontent = base64.b64decode(filecontent)
			else:
				invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','invoice.xls')])
				filecontent = invoice_xls.datas
				filename = 'Facturas Proveedor sin Cuenta.xls'
				filecontent = base64.b64decode(filecontent)

		elif res.account_opt == 'custom':
			if res.type_import in ('out_invoice','out_refund'):
				invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','invoice_with_account_customer.xls')])
				filecontent = invoice_xls.datas
				filename = 'Facturas Cliente con Cuenta.xls'
				filecontent = base64.b64decode(filecontent)
			else:
				invoice_xls = request.env['ir.attachment'].sudo().search([('name','=','invoice_with_account.xls')])
				filecontent = invoice_xls.datas
				filename = 'Facturas Proveedor con Cuenta.xls'
				filecontent = base64.b64decode(filecontent)

		return request.make_response(filecontent,
			[('Content-Type', 'application/octet-stream'),
			('Content-Disposition', content_disposition(filename))])