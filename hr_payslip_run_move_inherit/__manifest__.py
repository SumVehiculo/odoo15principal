# -*- encoding: utf-8 -*-
{
	'name': 'Hr Payslip Run Move Inherit',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'hr_payslip_run_move_it','hr_provisions'],
	'version': '1.0',
	'description':"""
		Modulo para generar Asiento Contable considerando las etiquetas analiticas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			# 'security/ir.model.access.csv',
			# 'views/hr_payslip_run_move.xml',
			'views/hr_contract.xml',
			],
	'installable': True,
	'license': 'LGPL-3',
}