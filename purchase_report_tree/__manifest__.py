# -*- coding: utf-8 -*-
{
    'name' : 'Reporte de Compra Vista Tree',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'Purchase',
    'description':
        """
        Reporte de Compra Vista Tree
        """,
    'depends' : ['purchase','purchase_stock','purchase_enterprise'],
    #,'fxo_sale_order_approve'
    'data': [
        'views/purchase_report.xml',        
    ],
    'auto_install': False,
    'installable': True
}