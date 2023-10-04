# -*- coding: utf-8 -*-
{
    'name' : 'Reporte de Ventas Vista Tree',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'Sale',
    'description':
        """
        Reporte de Ventas Vista Tree
        """,
    'depends' : ['sale','sale_enterprise','sale_stock'],
    #,'fxo_sale_order_approve'
    'data': [
        'views/sale_report.xml',        
    ],
    'auto_install': False,
    'installable': True
}