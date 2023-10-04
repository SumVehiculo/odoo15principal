# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date
import calendar

PERIODS_CODES = ['00','01','02','03','04','05','06','07','08','09','10','11','12']
PERIODS_NAMES = ['APERTURA','ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']

class HrPeriodGenerator(models.TransientModel):
	_name = 'hr.period.generator'
	_description = 'Hr Period Generator'

	# def get_fiscal_year(self):
	# 	fiscal_year = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).fiscal_year
	# 	if not fiscal_year:
	# 		raise UserError('No existe un año fiscal configurado en Parametros Generales de Contabilidad')
	# 	else:
	# 		return fiscal_year.id

	# fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year())
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal')

	def generate_periods(self):
		if not self.fiscal_year_id:
			raise UserError('El año fiscal es un campo Obligatorio')
		log = []
		for c,code in enumerate(PERIODS_CODES):
			# print("c",c)
			# print("code",code)
			fiscal_year = self.fiscal_year_id.name
			period_code = fiscal_year + code
			period_name = PERIODS_NAMES[c] + '-' + fiscal_year
			if code == '00':
				continue
			else:
				date_start = date(int(fiscal_year),c,1)
				date_end = date(int(fiscal_year),c,calendar.monthrange(int(fiscal_year),c)[1])
			hr_period = self.env['hr.period'].search([('code','=',period_code),('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)
			if hr_period:
				continue
			else:
				self.env['hr.period'].create({'code':period_code,
													'name':period_name,
													'fiscal_year_id':self.fiscal_year_id.id,
													'date_start':date_start,
													'date_end':date_end})
				log.append(period_name)
		return self.env['popup.it'].get_message('SE GENERARON LOS SIGUIENTES PERIODOS DE MANERA CORRECTA: \n %s' % ('\n'.join(log)))