# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import urllib.request
import urllib.parse
import requests
import json
import base64
from datetime import datetime, timedelta

class AccountMove(models.Model):
	_inherit = 'account.move'

	query_sunat_ids = fields.One2many('account.query.sunat','move_id',string=u'Verificacion Sunat',copy=False)

	def validate_sunat_query_params(self):
		if not self.company_id.partner_id.vat:
			raise UserError(u'La Compañía no tiene Nro de Documento.')
		if not self.partner_id.vat:
			raise UserError('El Proveedor no tiene Nro de Documento.')
		if len(self.ref.split('-')) != 2:
			raise UserError('El Nro de Comprobante no esta bien configurado')
		if not self.invoice_date:
			raise UserError('Falta Fecha de Factura.')

	def action_verify_sunat_invoice(self):
		obj_query = self.env['account.query.sunat']
		param = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		if not param:
			raise UserError(u'No existen Parametros Principales de Contabilidad para su Compañía')
		
		if not param.client_id or not param.client_secret:
			raise UserError(u'No estan configuradas las credenciales generadas en la página de SUNAT en Parametros Principales de Contabilidad para su Compañía')

		today = datetime.now()

		if not param.token_expire or today>param.token_expiration_date:
			params = {"grant_type" : u"client_credentials",
					"scope": u"https://api.sunat.gob.pe/v1/contribuyente/contribuyentes",
					"client_id": param.client_id,
					"client_secret": param.client_secret}

			
			url = 'https://api-seguridad.sunat.gob.pe/v1/clientesextranet/{client_id}/oauth2/token/'.format(client_id = param.client_id)
			
			headers = requests.utils.default_headers()
			headers['Content-Type'] = 'application/x-www-form-urlencoded'
			headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
			try:
				r = requests.post(url, headers=headers, data=params)
				#raise UserError(r.text)
				arre = r.text.replace("'",'"')
				arr2 = json.loads(arre)
				if 'access_token' in arr2.keys():
					param.token_expire = arr2['access_token']
					param.token_generation_date = today
					param.token_expiration_date = today + timedelta(seconds=int(arr2['expires_in']))
			except Exception as err:
				raise UserError(err)
			
		###### CREACION DE REPORTE ##############3

		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Reporte_query_sunat.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########RESUMEN DESTINO############
		worksheet = workbook.add_worksheet("REPORTE")
		worksheet.set_tab_color('blue')

		HEADERS = ['TD','NRO COMPROBANTE','PROVEEDOR','DOC PROVEEDOR','Estado Consulta',u'Mensaje del estado de la operación','Estado del Comprobante',
	     'Estado del Contribuyente',u'Condición de Domicilio del Contribuyente','Observaciones',u'Código de Error',
		 'Fecha Contable',u'Fecha Emisión']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		######################################################################
		if len(self)>30:
			raise UserError(u'No puede validar mas de 30 comprobantes')
		for move in self:
			if move.move_type not in ('in_invoice','in_refund'):
				raise UserError('Solo se aplica en Facturas de Proveedor')
			move.validate_sunat_query_params()
			partition = move.ref.split('-')
			params = {
						"numRuc": move.partner_id.vat,
						"codComp": move.l10n_latam_document_type_id.code,
						"numeroSerie": partition[0],
						"numero": int(partition[1]),
						"fechaEmision": move.invoice_date.strftime('%d/%m/%Y'),
						"monto": move.amount_total
					}
			
			url = 'https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/{ruc}/validarcomprobante'.format(ruc = move.company_id.partner_id.vat)
			
			headers = requests.utils.default_headers()
			headers['Content-Type'] = 'application/json'
			headers['Authorization'] = 'Bearer ' + param.token_expire 
			headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
			arr2={}
			try:
				r = requests.post(url, headers=headers, data=json.dumps(params))
				arre = r.text.replace("'",'"')
				arr2 = json.loads(arre)

			except Exception as err:
				raise UserError(err)
			if 'success' in arr2.keys():
				reg = obj_query.search([('move_id','=',move.id)],limit=1)
				if arr2['success']:
					if reg:
						reg.write({
							'success': arr2['success'],
							'message': arr2['message'] or '',
							'estadocp': arr2['data']['estadoCp'] if 'estadoCp' in arr2['data'].keys() else '',
							'estadoruc': arr2['data']['estadoRuc'] if 'estadoRuc' in arr2['data'].keys() else '',
							'conddomiruc': arr2['data']['condDomiRuc'] if 'condDomiRuc' in arr2['data'].keys() else '',
							'observaciones': arr2['data']['observaciones']  if 'observaciones' in arr2['data'].keys() else '',
						})
					else:
						reg = obj_query.create({
							'move_id': move.id,
							'success': arr2['success'],
							'message': arr2['message'] or '',
							'estadocp': arr2['data']['estadoCp'] if 'estadoCp' in arr2['data'].keys() else '',
							'estadoruc': arr2['data']['estadoRuc'] if 'estadoRuc' in arr2['data'].keys() else '',
							'conddomiruc': arr2['data']['condDomiRuc'] if 'condDomiRuc' in arr2['data'].keys() else '',
							'observaciones': arr2['data']['observaciones']  if 'observaciones' in arr2['data'].keys() else '',
						})
				else:
					if reg:
						reg.write({
							'success': arr2['success'] or False,
							'message': arr2['message'] or '',
							'errorcode': arr2['errorCode'] or '',
						})
					else:
						reg = obj_query.create({
							'move_id': move.id,
							'success': arr2['success'] or False,
							'message': arr2['message'] or '',
							'errorcode': arr2['errorCode'] or '',
						})
		
		

				worksheet.write(x,0,reg.td_p_id.code if reg.td_p_id else '',formats['especial1'])
				worksheet.write(x,1,reg.nro_comprobante if reg.nro_comprobante else '',formats['especial1'])
				worksheet.write(x,2,reg.proveedor_id.name if reg.proveedor_id else '',formats['especial1'])
				worksheet.write(x,3,reg.doc_proveedor if reg.doc_proveedor else '',formats['especial1'])
				worksheet.write(x,4,'VERDADERO' if reg.success else 'FALSO',formats['especial1'])
				worksheet.write(x,5,reg.message if reg.message else '',formats['especial1'])
				worksheet.write(x,6,dict(reg._fields['estadocp'].selection).get(reg.estadocp) if reg.estadocp else '',formats['especial1'])
				worksheet.write(x,7,dict(reg._fields['estadoruc'].selection).get(reg.estadoruc) if reg.estadoruc else '',formats['especial1'])
				worksheet.write(x,8,dict(reg._fields['conddomiruc'].selection).get(reg.conddomiruc) if reg.conddomiruc else '',formats['especial1'])
				worksheet.write(x,9,reg.observaciones if reg.observaciones else '',formats['especial1'])
				worksheet.write(x,10,reg.errorcode if reg.errorcode else '',formats['especial1'])
				worksheet.write(x,11,reg.move_id.date if reg.move_id.date else '',formats['dateformat'])
				worksheet.write(x,12,reg.move_id.invoice_date if reg.move_id.invoice_date else '',formats['dateformat'])
				x += 1

		widths = [5,22,58,18,15,22,13,14,22,26,16,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Reporte_query_sunat.xlsx', 'rb')

		return self.env['popup.it'].get_file('Validacion de Comprobantes.xlsx',base64.encodebytes(b''.join(f.readlines())))