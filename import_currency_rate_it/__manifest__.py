# -*- encoding: utf-8 -*-
{
	'name': 'Res Currency Rate IT',
	'category': 'Currency',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['l10n_pe_currency_rate','account_base_import_it'],
	'version': '1.0.0',
	'description':"""

	Agregar los Tipos de Cambios de la Pagina alterna

	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
		'wizard/currency_rate_update_wizard_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
