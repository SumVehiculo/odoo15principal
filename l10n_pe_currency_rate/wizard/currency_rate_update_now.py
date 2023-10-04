# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError
import urllib.request
import urllib.parse
import requests
import json

class CurrencyRateUpdateNow(models.TransientModel):
	_name = "currency.rate.update.now"
	
	date = fields.Date(string="Fecha",readonly=True,default=fields.Date.context_today)

	def update_now(self):
		rate_obj = self.env['res.currency.rate']
		currency = self.env.ref('base.USD')
		url = 'https://itgrupo.net/api/webservice/currencyratetoday'
		params = {'UserName' : 'APIUserGOLDtc',
				  'Password': 'Api$pass&241G13nd4TC',
				  'Date': self.date.strftime('%Y/%m/%d')}

		try:
			r = requests.post(url, params=params)
			arre = r.text.replace("'",'"')
			arr2 = json.loads(arre)

			if currency:
				rate_search = rate_obj.search([
							('name', '=', self.date),
							('currency_id', '=', currency.id),
							('company_id','=',self.env.company.id)
						],limit=1)

				if rate_search:
					rate_search.write({
						'rate': arr2['rate'],
						'sale_type': arr2['sale_type'],
						'purchase_type': arr2['purchase_type'],
					})
				else:
					rate_obj.create({
						'currency_id': currency.id,
						'rate': arr2['rate'],
						'name': self.date,
						'sale_type': arr2['sale_type'],
						'purchase_type': arr2['purchase_type'],
						'company_id': self.env.company.id
					})

				return self.env['popup.it'].get_message(u'SE ACTUALIZÓ CORRECTAMENTE EL TC PARA EL DIA %s'%(self.date.strftime('%Y/%m/%d')))
		
		except Exception as err:
			raise UserError(err)