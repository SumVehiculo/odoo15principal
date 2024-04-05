# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	# validator_ids=fields.One2many('hr.leave.validator','parameter_id','Validadores')
	# suspension_type_id = fields.Many2one('hr.suspension.type',u'Tipo de Suspensión Vacaciones')
	# vacations_wd_id = fields.Many2one('hr.payslip.worked_days.type', string='WD Vacaciones')
	#
	# suspension_dm_type_id = fields.Many2one('hr.suspension.type',u'Tipo de Suspensión D.M.')
	# medico_wd_id = fields.Many2one('hr.payslip.worked_days.type', string='WD Descanso Medico')

	#####VACACIONES######
	# vaca_input_id = fields.Many2one('hr.payslip.input.type', string='Input Vacaciones')

	def check_vacation_values(self):
		if not self.vacation_input_id or \
			not self.bonus_sr_ids or \
			not self.commission_sr_ids or \
			not self.extra_hours_sr_id or \
			not self.basic_sr_id or \
			not self.household_allowance_sr_id or \
			not self.lack_wd_id:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Vacaciones del Menu de Parametros Principales')


# class HrLeaveValidator(models.Model):
# 	_name='hr.leave.validator'
# 	_description = 'Validadores de Vacaciones'
#
# 	user_id = fields.Many2one('res.users','Usuario')
# 	first_validate = fields.Boolean(u'Primera Aprobación')
# 	second_validate = fields.Boolean(u'Segunda Aprobación')
# 	parameter_id = fields.Many2one('hr.main.parameter','Main')