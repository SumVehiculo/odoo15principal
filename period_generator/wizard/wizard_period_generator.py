# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date
import calendar

PERIODS_CODES = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13']
PERIODS_NAMES = ['APERTURA','ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE','CIERRE']

class PeriodGenerator(models.TransientModel):
	_name = "period.generator"

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		if not fiscal_year:
			raise UserError(u'No existe un año fiscal con el año actual.')
		else:
			return fiscal_year.id

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())

	def generate_periods(self):
		if not self.fiscal_year_id:
			raise UserError('El año fiscal es un campo Obligatorio')
		log = []
		for c,code in enumerate(PERIODS_CODES):
			fiscal_year = self.fiscal_year_id.name
			period_code = fiscal_year + code
			period_name = PERIODS_NAMES[c] + '-' + fiscal_year
			if code == '00':
				date_start = date(int(fiscal_year),1,1)
				date_end = date(int(fiscal_year),1,1)
			elif code == '13':
				date_start = date(int(fiscal_year),12,31)
				date_end = date(int(fiscal_year),12,31)
			else:
				date_start = date(int(fiscal_year),c,1)
				date_end = date(int(fiscal_year),c,calendar.monthrange(int(fiscal_year),c)[1])
			account_period = self.env['account.period'].search([('code','=',period_code),('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)
			if account_period:
				continue
			else:
				if code == '00' or code == '13':
					self.env['account.period'].create({'code':period_code,
												   'name':period_name,
												   'fiscal_year_id':self.fiscal_year_id.id,
												   'date_start':date_start,
												   'date_end':date_end,
												   'is_opening_close':True})
				else:
					self.env['account.period'].create({'code':period_code,
													'name':period_name,
													'fiscal_year_id':self.fiscal_year_id.id,
													'date_start':date_start,
													'date_end':date_end})
				log.append(period_name)
		return self.env['popup.it'].get_message('SE GENERARON LOS SIGUIENTES PERIODOS DE MANERA CORRECTA: \n %s' % ('\n'.join(log)))