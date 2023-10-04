# -*- encoding: utf-8 -*-
{
    'name': 'Kardex Valorado',
    'version': '1.0',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'website': '',
    'category': 'Kardex',
    'depends': ['kardex_save_period_tabla','kardex_fisico_it','kardex_fields_it','purchase_stock','account'],
    'description': """KARDEX""",
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'wizard/make_kardex_view.xml',
    ],
    'auto_install': False,
    'installable': True
}
