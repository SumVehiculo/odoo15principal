# -*- encoding: utf-8 -*-
{
	'name': 'Sale Line Invoiced Calcule',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['sale','l10n_pe_edi_extended'],
	'version': '1.0',
	'description':"""
	Agregar información a la factura.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'views/mrp_kardex.xml'],
	'installable': True
}
