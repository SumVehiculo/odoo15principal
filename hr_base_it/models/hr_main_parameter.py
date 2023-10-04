# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from calendar import *

class HrMainParameter(models.Model):
	_name = 'hr.main.parameter'
	_description = 'Hr Main Parameter'

	name = fields.Char(default="Parametros Principales")
	company_id = fields.Many2one('res.company', string=u'Compañía', default=lambda self: self.env.company.id)
	income_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Ingresos', required=True)
	worker_contributions_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Aportes Trabajador', required=True)
	net_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Neto', required=True)
	net_discounts_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Descuentos al Neto', required=True)
	net_to_pay_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Neto a Pagar', required=True)
	employer_contributions_sr_id = fields.Many2one('hr.salary.rule', string='R. S. Aportes Empleador', required=True)
	dir_create_file = fields.Char(string='Directorio de Descarga', required=True)
	insurable_remuneration = fields.Many2one('hr.salary.rule', string='Remuneracion Asegurable', required=True)
	wd_dlab = fields.Many2many('hr.payslip.worked_days.type', 'wd_dlab_main_parameter_rel', 'main_parameter_id', 'wd_id', string='Worked Days Dias Laborados')
	wd_dnlab = fields.Many2many('hr.payslip.worked_days.type', 'wd_dnlab_main_parameter_rel', 'main_parameter_id', 'wd_id', string='Worked Days Dias no Laborados')
	wd_dsub = fields.Many2many('hr.payslip.worked_days.type', 'wd_dsub_main_parameter_rel', 'main_parameter_id', 'wd_id', string='Worked Days Dias Subsidiados')
	wd_ext = fields.Many2many('hr.payslip.worked_days.type', 'wd_dext_main_parameter_rel', 'main_parameter_id', 'wd_id', string='Worked Days Sobretiempo')
	wd_dvac = fields.Many2many('hr.payslip.worked_days.type', 'wd_dvac_main_parameter_rel', 'main_parameter_id', 'wd_id', string='Worked Days Ausencias')
	income_categories = fields.Many2many('hr.salary.rule.category', 'src_income_main_parameter_rel', 'main_parameter_id', 'src_id', string='Categorias Ingresos')
	discounts_categories = fields.Many2many('hr.salary.rule.category', 'src_discounts_main_parameter_rel', 'main_parameter_id', 'src_id', string='Categorias Descuentos')
	contributions_categories = fields.Many2many('hr.salary.rule.category', 'src_contributions_main_parameter_rel', 'main_parameter_id', 'src_id', string='Categorias Aportes Trabajador')
	contributions_emp_categories = fields.Many2many('hr.salary.rule.category', 'src_contributions_emp_main_parameter_rel', 'main_parameter_id', 'src_id', string='Categorias Aportes Empleador')
	signature = fields.Binary(string='Firma Empleador')
	payslip_working_wd = fields.Many2one('hr.payslip.worked_days.type', string='W.D. Dias Laborados')

	reprentante_legal_id = fields.Many2one('res.partner', string='Representante Legal')
	rmv = fields.Float('R.M.V.', default=1025)

	@api.model
	def create(self,vals):
		if len(self.search([('company_id', '=', self.env.company.id)])) > 0:
			raise UserError(u'No se puede crear mas de un Parametro Principal por Compañía')
		return super(HrMainParameter,self).create(vals)

	def get_main_parameter(self):
		MainParameter = self.search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter:
			raise UserError('No se ha creado Parametros Generales para esta compañia')
		return MainParameter

	def check_voucher_values(self):
		if not self.wd_dlab or \
			not self.wd_dnlab or \
			not self.wd_dsub or \
			not self.wd_ext or \
			not self.wd_dvac or \
			not self.income_categories or \
			not self.discounts_categories or \
			not self.contributions_categories or \
			not self.contributions_emp_categories:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Boleta del Menu de Parametros Principales')

	def get_month_name(self, month):
		array = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
				 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
		return array[month - 1]

	def get_months_of_30_days(self, days, months):
		while days >= 30:
			days -= 30
			months += 1
		return days, months

	def diff_months(self, date_from, date_to):
		return (date_to.year - date_from.year) * 12 + date_to.month - date_from.month

	def get_months_days_difference(self, date_from, date_to):
		if date_from.year == date_to.year and date_from.month == date_to.month:
			#### I don´t know if this is an error, posible fix
			return 0, date_to.day - date_from.day
		else:
			df_worked_days = 0
			months = (date_to.year - date_from.year) * 12 + (date_to.month - date_from.month - 1)
			df_last_day = monthrange(date_from.year, date_from.month)[1]
			if date_from.day == 1:
				months += 1
			else:
				df_worked_days += df_last_day - date_from.day + 1
			df_last_day = monthrange(date_to.year, date_to.month)[1]
			if date_to.day == df_last_day:
				months += 1
			else:
				df_worked_days += date_to.day
			if df_worked_days >= 30:
				return self.get_months_of_30_days(df_worked_days, months)
			else:
				return df_worked_days, months

	def number_to_letter(self, number):
		UNIDADES = (
			'',
			'UN ',
			'DOS ',
			'TRES ',
			'CUATRO ',
			'CINCO ',
			'SEIS ',
			'SIETE ',
			'OCHO ',
			'NUEVE ',
			'DIEZ ',
			'ONCE ',
			'DOCE ',
			'TRECE ',
			'CATORCE ',
			'QUINCE ',
			'DIECISEIS ',
			'DIECISIETE ',
			'DIECIOCHO ',
			'DIECINUEVE ',
			'VEINTE '
		)

		DECENAS = (
			'VENTI',
			'TREINTA ',
			'CUARENTA ',
			'CINCUENTA ',
			'SESENTA ',
			'SETENTA ',
			'OCHENTA ',
			'NOVENTA ',
			'CIEN '
		)

		CENTENAS = (
			'CIENTO ',
			'DOSCIENTOS ',
			'TRESCIENTOS ',
			'CUATROCIENTOS ',
			'QUINIENTOS ',
			'SEISCIENTOS ',
			'SETECIENTOS ',
			'OCHOCIENTOS ',
			'NOVECIENTOS '
		)

		MONEDAS = (
			{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
			{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
			{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
			{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
			{'country': u'Perú', 'currency': 'PEN', 'singular': u'SOL', 'plural': u'SOLES', 'symbol': u'S/.'},
			{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
		)
		# Para definir la moneda me estoy basando en los código que establece el ISO 4217
		# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
		# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

		def __convert_group(n):
			"""Turn each group of numbers into letters"""
			output = ''

			if(n == '100'):
				output = "CIEN"
			elif(n[0] != '0'):
				output = CENTENAS[int(n[0]) - 1]

			k = int(n[1:])
			if(k <= 20):
				output += UNIDADES[k]
			else:
				if((k > 30) & (n[2] != '0')):
					output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
				else:
					output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			return output
		#raise osv.except_osv('Alerta', number)
		number=str(round(float(number),2))
		separate = number.split(".")
		number = int(separate[0])

		if int(separate[1]) >= 0:
			moneda = "con " + str(separate[1]).ljust(2,'0') + "/" + "100 " 

		"""Converts a number into string representation"""
		converted = ''
		
		if not (0 <= number < 999999999):
			raise UserError('Alerta %d' % number)
			#return 'No es posible convertir el numero a letras'
		
		number_str = str(number).zfill(9)
		millones = number_str[:3]
		miles = number_str[3:6]
		cientos = number_str[6:]		

		if(millones):
			if(millones == '001'):
				converted += 'UN MILLON '
			elif(int(millones) > 0):
				converted += '%sMILLONES ' % __convert_group(millones)

		if(miles):
			if(miles == '001'):
				converted += 'MIL '
			elif(int(miles) > 0):
				converted += '%sMIL ' % __convert_group(miles)

		if(cientos):
			if(cientos == '001'):
				converted += 'UN '
			elif(int(cientos) > 0):
				converted += '%s ' % __convert_group(cientos)
		if float(number_str)==0:
			converted += 'CERO '
		converted += moneda

		return converted.upper()