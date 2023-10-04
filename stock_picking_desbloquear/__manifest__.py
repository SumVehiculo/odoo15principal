# -*- coding: utf-8 -*-
{
    'name' : 'Albaranes No Desbloquear',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'stock',
    'description':
        """
        Albaranes No Desbloquear
        """,
    'depends' : ['stock'],
    #,'fxo_sale_order_approve'
    'data': [
        'views/stock_picking_desbloquear.xml',
    ],
    'auto_install': False,
    'installable': True
}