# -*- encoding: utf-8 -*-
{
	'name': 'Kardex Actualizar Transferencias Internas IT',
	'version': '1.0',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'website': '',
	'category': 'account',
	'depends': ['kardex_valorado_it','cerrar_kardex_it'],
	'description': """Actualizador de Transferencias Internas el valor unitario""",
	'demo': [],
	'data': [
        'security/ir.model.access.csv',
		'stock_move_view.xml',
	],
	'auto_install': False,
	'installable': True
}

