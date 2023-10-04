# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning, UserError
import urllib.request
import urllib.parse
import requests
import json

class PeCurrencyRateUpdateWizard(models.TransientModel):
	
	_name = "pe.currency.rate.update.wizard"
	_description = 'PE Currency Rate Update Wizard'
	
	start_date = fields.Date(string="Fecha Inicial")
	end_date = fields.Date(string="Fecha Final")

	def get_currency_rate(self):
		rate_obj = self.env['res.currency.rate']
		currency = self.env.ref('base.USD')
		url = 'https://itgrupo.net/api/webservice/currencyraterange'
		params = {'UserName' : 'APIUserGOLDtc',
				'Password': 'Api$pass&241G13nd4TC',
				'DateIni': self.start_date.strftime('%Y/%m/%d'),
				'DateFin': self.end_date.strftime('%Y/%m/%d')}

		try:
			r = requests.post(url, params=params)
			arre = r.text.replace("'",'"')
			arr2 = json.loads(arre)

			if currency:
				for line in arr2:
					rate_search = rate_obj.search([
								('name', '=', line['name'].replace('/','-')),
								('currency_id', '=', currency.id),
								('company_id','=',self.env.company.id)
							],limit=1)

					if rate_search:
						rate_search.write({
							'rate': line['rate'],
							'sale_type': line['sale_type'],
							'purchase_type': line['purchase_type'],
						})
					else:
						rate_obj.create({
							'currency_id': currency.id,
							'rate': line['rate'],
							'name': line['name'].replace('/','-'),
							'sale_type': line['sale_type'],
							'purchase_type': line['purchase_type'],
							'company_id': self.env.company.id
						})

				return self.env['popup.it'].get_message(u'SE ACTUALIZÓ CORRECTAMENTE EL TC PARA %s - %s'%(self.start_date.strftime('%Y/%m/%d'),self.end_date.strftime('%Y/%m/%d')))
		
		except Exception as err:
			raise UserError(err)