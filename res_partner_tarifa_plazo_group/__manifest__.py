# -*- coding: utf-8 -*-
{
    'name' : 'Grupo Edición tarifa y plazo de pago en Contactos',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'base',
    'description':
        """
        Grupo Edición tarifa y plazo de pago en Contactos
        """,
    'depends' : ['base','account','product'],
    #,'fxo_sale_order_approve'
    'data': [
        'security/group_plazo_pago_contactos.xml'
    ],
    'auto_install': False,
    'installable': True
}