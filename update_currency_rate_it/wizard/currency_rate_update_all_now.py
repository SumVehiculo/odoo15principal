# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
import urllib.request
import urllib.parse
import requests
import json

class CurrencyRateUpdateAllNow(models.TransientModel):
	_name = "currency.rate.update.all.now"
	
	date = fields.Date(string="Fecha",readonly=True,default=fields.Date.context_today)
	company_ids = fields.Many2many('res.company', string="Compañias", readonly=True)
	
	def update_now(self):
		rate_obj = self.env['res.currency.rate']
		currency = self.env.ref('base.USD')
		url = 'https://itgrupo.net/api/webservice/currencyratetoday'
		params = {'UserName' : 'APIUserGOLDtc',
				  'Password': 'Api$pass&241G13nd4TC',
				  'Date': self.date.strftime('%Y/%m/%d')}
		invoice = self.env['account.move'].browse(self.env.context['invoice_id'])
		try:
			r = requests.post(url, params=params)
			arre = r.text.replace("'",'"')
			arr2 = json.loads(arre)
			
			if currency:
				for company in self.company_ids:
					rate_search = rate_obj.sudo().search([
								('name', '=', self.date),
								('currency_id', '=', currency.id),
								('company_id','=',company.id)
							],limit=1)

					if rate_search:
						rate_search.sudo().write({
							'rate': arr2['rate'],
							'sale_type': arr2['sale_type'],
							'purchase_type': arr2['purchase_type'],
						})
					else:
						type_now=self.env['res.currency.rate'].sudo().search([('name','=',self.date),('company_id','=',company.id)])
						if not type_now:
							rate_obj.sudo().create({
								'currency_id': currency.id,
								'rate': arr2['rate'],
								'name': self.date,
								'sale_type': arr2['sale_type'],
								'purchase_type': arr2['purchase_type'],
								'company_id': company.id
							})
					if invoice.currency_rate == 1:
						invoice.currency_rate = arr2['sale_type']
				return self.env['popup.it'].get_message(u'SE ACTUALIZÓ CORRECTAMENTE EL TC PARA EL DIA %s'%(self.date.strftime('%Y/%m/%d')))
		
		except Exception as err:
			raise UserError(err)