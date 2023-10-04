# -*- coding: utf-8 -*-
{
    'name' : 'Grupo Edición Descuentos y tarifa en Ventas',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'sale',
    'description':
        """
        Grupo Edición Descuentos y tarifa en Ventas
        """,
    'depends' : ['sale'],
    #,'fxo_sale_order_approve'
    'data': [
        'security/group_discount_tarifa.xml',
    ],
    'auto_install': False,
    'installable': True
}
