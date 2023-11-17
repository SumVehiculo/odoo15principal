# -*- encoding: utf-8 -*-
{
	'name': 'Presupuestos IT',
	'category': 'account',
	'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
	'depends': ['account_budget_it'],
	'version': '1.0',
	'description':"""
		Correción Observaciones contabilidad-capacitacion SUM (#19689)
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'views/account_analytic_tag.xml',
        'views/account_budget_views.xml'],
	'installable': True
}
