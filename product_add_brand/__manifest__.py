# -*- coding: utf-8 -*-
{
    'name': "Atharva Theme General",
    'category': 'Website',
    'sequence': 5,
    'summary': """Atharva Theme General""",
    'version': '2.3',
    'author': 'Atharva System',
    'support': 'support@atharvasystem.com',
    'website' : 'http://www.atharvasystem.com',
    'license' : 'OPL-1',
    'description': """
        Base Module for all themes by Atharva System""",
    'depends': ['sale','product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand_views.xml'
    ],
    'price': 14.00,
    'currency': 'EUR',
    'images': ['static/description/atharva-theme-general-banner.png'],
    'installable': True,
    'application': True
}
