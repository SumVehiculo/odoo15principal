# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	fifth_rem_proyected = fields.Float(string='Remuneracion Afecta Quinta a Proyectar')
	grat_july_proyected = fields.Float(string='Gratificacion de Julio Proyectada')
	grat_december_proyected = fields.Float(string='Gratificacion de Diciembre Proyectada')

	def update_proyectado_quinta(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()

		for rec in self:

			first_contract = rec.get_first_contract(rec.employee_id, rec)
			# print("first_contract",first_contract.date_start.month)
			# print("year",date.today().year)
			af = (MainParameter.rmv*0.10) if rec.employee_id.children > 0 else 0
			amount = rec.wage + af

			if first_contract.date_start.year == date.today().year:
				if first_contract.date_start.month == 12:
					grat_july_proyected = 0
					grat_december_proyected = 0
				elif first_contract.date_start.month >= 7:
					grat_july_proyected = 0
					if first_contract.date_start.day == 1:
						grat_december_proyected = ((amount * (1 + (rec.social_insurance_id.percent)/100))/6) * (13-first_contract.date_start.month)
					else:
						grat_december_proyected = ((amount * (1 + (rec.social_insurance_id.percent)/100))/6) * (12-first_contract.date_start.month)
				else:
					if first_contract.date_start.day == 1:
						grat_july_proyected = ((amount * (1 + (rec.social_insurance_id.percent)/100))/6) * (7-first_contract.date_start.month)
					else:
						grat_july_proyected = ((amount * (1 + (rec.social_insurance_id.percent)/100))/6) * (6-first_contract.date_start.month)
					grat_december_proyected = amount * (1 + (rec.social_insurance_id.percent)/100)
			else:
				grat_july_proyected = amount * (1 + (rec.social_insurance_id.percent)/100)
				grat_december_proyected = amount * (1 + (rec.social_insurance_id.percent)/100)

			rec.fifth_rem_proyected = amount
			rec.grat_july_proyected = grat_july_proyected
			rec.grat_december_proyected = grat_december_proyected