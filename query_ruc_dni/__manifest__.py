# -*- encoding: utf-8 -*-
{
	'name': 'Query RUC and DNI',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['l10n_latam_base','l10n_pe','account'],
	'version': '1.0',
	'description':"""
	-Parametros RUC/DNI
	Modulo para consultar RUC y DNI mediante el uso de una API
	Para instalar este modulo es necesario instalar la libreria suds-py3 con el comando 'python -m pip install suds-py3' 
	GRUPÒ : Mostrar direcciones Completas
	campos:
	     direccion_complete_it ,
	     direccion_complete_ubigeo_it (con ubigeo)
	     
	""",
	'auto_install': False,
	'demo': [],
	'data': [
			'security/security.xml',
			'security/ir.model.access.csv',
			'data/res_country_state.xml',
			'views/einvoice_catalog_06.xml',
			'views/res_country_state.xml',
			'views/res_partner.xml',
			'views/ruc_main_parameter.xml',
			'views/grupo.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
