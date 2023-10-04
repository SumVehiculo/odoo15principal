# -*- coding: utf-8 -*-
{
    'name' : 'Limite Credito Albaran',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'stock',
    'description':
        """
        Limite Credito Albaran
        """,
    'depends' : ['stock','account','base','sale','sale_order_credit_limit'],
    #,'fxo_sale_order_approve'
    'data': [
        'views/credit_limit.xml',
    ],
    'auto_install': False,
    'installable': True
}