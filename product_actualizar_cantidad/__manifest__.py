# -*- coding: utf-8 -*-
{
    'name' : 'Ocultar Actualizar Cantidades',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'stock',
    'description':
        """
        Ocultar Actualizar Cantidades
        """,
    'depends' : ['stock','base'],
    #,'fxo_sale_order_approve'
    'data': [
        'security/group.xml',
        'views/stock_quant_hide_button.xml',
    ],
    'auto_install': False,
    'installable': True
}