# -*- encoding: utf-8 -*-
{
    'name': 'Hr Derechohabientes',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it','hr_base_it','hr_importers_it'],
	'version': '1.0',
	'description':"""
		Modulo que permite registrar el cónyuge o concubina o los hijos/as menores de edad
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'data/ir_cron_data.xml',
			'views/hr_employee.xml',
			'wizards/report_derechohabientes.xml',
	],
	'installable': True,
	'license': 'LGPL-3',
}
