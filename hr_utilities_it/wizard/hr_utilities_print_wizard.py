# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

class HrUtilitiesPrintWizard(models.TransientModel):
	_name = 'hr.utilities.print.wizard'
	_description = 'Hr Utilities Print Wizard'

	hr_utilities_id = fields.Many2one('hr.utilities.it',string='Utilidades')
	mode = fields.Selection([('all','Todos los Empleados'),('one','Solo un Empleado')],string='Modo',default='all',required=True)
	hr_utilities_line_id = fields.Many2one('hr.utilities.it.line',string='Empleado')

	def get_print(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Utilidades.pdf', pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
		elements = []
		if self.mode == 'all':
			for utilities_line in self.hr_utilities_id.utilities_line_ids:
				elements += utilities_line._get_print()
		else:
			elements += self.hr_utilities_line_id._get_print()
		doc.build(elements)
		f = open(MainParameter.dir_create_file + 'Utilidades.pdf', 'rb')
		return self.env['popup.it'].get_file('Utilidades.pdf',base64.encodebytes(b''.join(f.readlines())))