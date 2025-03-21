# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from odoo.addons.web.controllers.main import content_disposition
from odoo.http import request, content_disposition

class PopupItBalanceInventory(models.TransientModel):
	_name = 'popup.it.balance.inventory'
	_description = 'Popup IT Balance Inventory'

	name = fields.Char()
	output_name_1 = fields.Char(string='Nombre del Archivo 1')
	output_file_1 = fields.Binary(string=u'ESTADO DE SITUACIÓN FINANCIERA',readonly=True,filename="output_name_1")
	output_url_1 = fields.Char(string='URL del Archivo 1', readonly=True)

	output_name_2 = fields.Char(string='Nombre del Archivo 2')
	output_file_2 = fields.Binary(string='CTA. 10 EFECTIVO Y EQUIVALENTES DE EFECTIVO',readonly=True,filename="output_name_2")
	output_url_2 = fields.Char(string='URL del Archivo 2', readonly=True)

	output_name_3 = fields.Char(string='Nombre del Archivo 3')
	output_file_3 = fields.Binary(string='CTA. 12 CTA POR COBRAR COM. – TERC. Y 13 CTA POR COBRAR COM. – REL.',readonly=True,filename="output_name_3")
	output_url_3 = fields.Char(string='URL del Archivo 3', readonly=True)

	output_name_4 = fields.Char(string='Nombre del Archivo 4')
	output_file_4 = fields.Binary(string='CTA. 14 CTA POR COBRAR AL PERSONAL, ACCIONISTAS, DIRECTORES Y GERENTES',readonly=True,filename="output_name_4")
	output_url_4 = fields.Char(string='URL del Archivo 4', readonly=True)

	output_name_5 = fields.Char(string='Nombre del Archivo 5')
	output_file_5 = fields.Binary(string='CTA. 16 CTA POR COBRAR DIV. - TERC. O CTA. 17 CTA POR COBRAR DIV. - REL.',readonly=True,filename="output_name_5")
	output_url_5 = fields.Char(string='URL del Archivo 5', readonly=True)

	output_name_6 = fields.Char(string='Nombre del Archivo 6')
	output_file_6 = fields.Binary(string='CTA. 19 ESTIMACIÓN DE CTA DE COBRANZA DUDOSA',readonly=True,filename="output_name_6")
	output_url_6 = fields.Char(string='URL del Archivo 6', readonly=True)

	output_name_7 = fields.Char(string='Nombre del Archivo 7')
	output_file_7 = fields.Binary(string='CTA. 20 - MERCADERIAS Y LA CTA. 21 - PROD. TERMINADOS',readonly=True,filename="output_name_7")
	output_url_7 = fields.Char(string='URL del Archivo 7', readonly=True)

	output_name_8 = fields.Char(string='Nombre del Archivo 8')
	output_file_8 = fields.Binary(string='CTA. 30 INVERSIONES MOBILIARIAS',readonly=True,filename="output_name_8")
	output_url_8 = fields.Char(string='URL del Archivo 8', readonly=True)

	output_name_9 = fields.Char(string='Nombre del Archivo 9')
	output_file_9 = fields.Binary(string='CTA. 34 - INTANGIBLES',readonly=True,filename="output_name_9")
	output_url_9 = fields.Char(string='URL del Archivo 9', readonly=True)

	output_name_10 = fields.Char(string='Nombre del Archivo 10')
	output_file_10 = fields.Binary(string='CTA. 41 REMUNERACIONES Y PARTICIPACIONES POR PAGAR',readonly=True,filename="output_name_10")
	output_url_10 = fields.Char(string='URL del Archivo 10', readonly=True)

	output_name_11 = fields.Char(string='Nombre del Archivo 11')
	output_file_11 = fields.Binary(string='CTA. 42 CTA POR PAGAR COM. – TERC. Y LA CTA. 43 CTA POR PAGAR COM. – REL.',readonly=True,filename="output_name_11")
	output_url_11 = fields.Char(string='URL del Archivo 11', readonly=True)

	output_name_12 = fields.Char(string='Nombre del Archivo 12')
	output_file_12 = fields.Binary(string='CTA. 46 CTA POR PAGAR DIV. – TERC. Y DE LA CTA. 47 CTA POR PAGAR DIV. – REL.',readonly=True,filename="output_name_12")
	output_url_12 = fields.Char(string='URL del Archivo 12', readonly=True)

	output_name_13 = fields.Char(string='Nombre del Archivo 13')
	output_file_13 = fields.Binary(string='CTA. 47 - BEN. SOCIALES DE LOS TRABAJADORES (PCGR) - NO APLICA PARA EL PCGE',readonly=True,filename="output_name_13")
	output_url_13 = fields.Char(string='URL del Archivo 13', readonly=True)

	output_name_14 = fields.Char(string='Nombre del Archivo 14')
	output_file_14 = fields.Binary(string='CTA. 37 ACTIVO DIFERIDO Y DE LA CTA. 49 PASIVO DIFERIDO',readonly=True,filename="output_name_14")
	output_url_14 = fields.Char(string='URL del Archivo 14', readonly=True)

	output_name_15 = fields.Char(string='Nombre del Archivo 15')
	output_file_15 = fields.Binary(string='CTA. 50 CAPITAL 3.16.1 CTA. 50 - CAPITAL',readonly=True,filename="output_name_15")
	output_url_15 = fields.Char(string='URL del Archivo 15', readonly=True)

	output_name_16 = fields.Char(string='Nombre del Archivo 16')
	output_file_16 = fields.Binary(string='CTA. 50 CAPITAL 3.16.2 EST. DE LA PARTICIPACIÓN ACCIONARIA SOCIALES',readonly=True,filename="output_name_16")
	output_url_16 = fields.Char(string='URL del Archivo 16', readonly=True)

	output_name_17 = fields.Char(string='Nombre del Archivo 17')
	output_file_17 = fields.Binary(string='BALANCE DE COMPROBACIÓN',readonly=True,filename="output_name_17")
	output_url_17 = fields.Char(string='URL del Archivo 17', readonly=True)

	output_name_18 = fields.Char(string='Nombre del Archivo 18')
	output_file_18 = fields.Binary(string='ESTADO DE FLUJOS DE EFECTIVO - MÉTODO DIRECTO',readonly=True,filename="output_name_18")
	output_url_18 = fields.Char(string='URL del Archivo 18', readonly=True)

	output_name_19 = fields.Char(string='Nombre del Archivo 19')
	output_file_19 = fields.Binary(string='ESTADO DE CAMBIOS EN EL PATRIMONIO NETO',readonly=True,filename="output_name_19")
	output_url_19 = fields.Char(string='URL del Archivo 19', readonly=True)

	output_name_20 = fields.Char(string='Nombre del Archivo 20')
	output_file_20 = fields.Binary(string='ESTADO DE RESULTADOS',readonly=True,filename="output_name_20")
	output_url_20 = fields.Char(string='URL del Archivo 20', readonly=True)

	output_name_21 = fields.Char(string='Nombre del Archivo 21')
	output_file_21 = fields.Binary(string='ESTADO DE RESULTADOS INTEGRALES',readonly=True,filename="output_name_21")
	output_url_21 = fields.Char(string='URL del Archivo 21', readonly=True)

	output_name_22 = fields.Char(string='Nombre del Archivo 22')
	output_file_22 = fields.Binary(string='ESTADO DE FLUJOS DE EFECTIVO - MÉTODO INDIRECTO',readonly=True,filename="output_name_22")
	output_url_22 = fields.Char(string='URL del Archivo 22', readonly=True)

	@api.model
	def get_file(self, **kwargs):
		# Crear el registro del wizard
		wizard = self.create(kwargs)

		# Para cada archivo, crear un attachment y generar la URL
		for i in range(1, 23):
			output_name = kwargs.get(f'output_name_{i}')
			output_file = kwargs.get(f'output_file_{i}')
			if output_name:
				attachment = self.env['ir.attachment'].sudo().create({
					'name': output_name,
					'type': 'binary',
					'datas': output_file,
					'store_fname': output_name,
					'res_model': self._name,
					'res_id': wizard.id,
				})
				url = '/web/content/%s?download=1' % attachment.id
				wizard.write({f'output_url_{i}': url})
				
		return {
			"type": "ir.actions.act_window",
			"res_model": "popup.it.balance.inventory",
			"views": [[self.env.ref('account_sunat_balance_inventory_rep_it.popup_it_balance_inventory_form').id, "form"]],
			"res_id": wizard.id,
			"target": "new",
		}

	def view_file(self):
		url = self.env.context.get('url')
		return {
			'target': 'new',
			'type': 'ir.actions.act_url',
			'url': url
		}