# -*- encoding: utf-8 -*-
{
    'name': 'Kardex Formato Sunat V12',
    'version': '1.0',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'website': '',
    'category': 'account',
    'depends': ['kardex_valorado_it'],
    'description': """KARDEX FORMATO SUNAT V12""",
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv', 
        'wizard/make_kardex_view.xml',
    ],
    'auto_install': False,
    'installable': True
}
