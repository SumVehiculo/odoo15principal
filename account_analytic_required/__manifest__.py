# -*- coding: utf-8 -*-
{
    'name' : 'Personalizaciones sum',
    'version': '1.0',
    'author': 'ITGRUPO,berth',
    'website': '',
    'category': 'stock',
    'depends' : ['stock','sale','account'],
    'data': [
        'security/group.xml',
        'views/sale_order.xml',
        'views/sale_order_line.xml',
        'views/sale_report.xml'
    ],
    'auto_install': False,
    'installable': True
}