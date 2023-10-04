{
    'name': 'Actualizacion Manual TC',
    'version': '1.0',
	'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'account',
    'depends': ['account','popup_it','account_fields_it'],
    'data': [
        'security/ir.model.access.csv',      
        'views/account_move.xml',
        'wizard/currency_rate_update_all_now.xml',
    ],
    'auto_install': False,
    'installable': True,
	'license': 'LGPL-3'
}