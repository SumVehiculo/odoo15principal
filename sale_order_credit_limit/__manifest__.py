# -*- coding: utf-8 -*-
{
    'name' : 'Limite Credito',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'Account',
    'description':
        """
        Limite Credito
        """,
    'depends' : ['sale','account','base'],
    #,'fxo_sale_order_approve'
    'data': [
        'views/credit_limit.xml',
        'views/groups.xml',        
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
    'installable': True
}
