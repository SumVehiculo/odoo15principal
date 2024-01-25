# -*- encoding: utf-8 -*-
{
    'name': 'Kardex Formato Sunat',
    'version': '1.0',
    'author': 'ITGRUPO-KARDEX',
    'website': '',
    'category': 'account',
    'depends': ['base','product','kardex_valorado_it','account','uom','account_fields_it'],
    'description': """KARDEX FORMATO SUNAT""",
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',   
        'views/existence_type.xml',    
        'wizard/make_kardex_view.xml',
        'views/product_category.xml',
        'views/product_template.xml',
        'views/einvoice_catalog_25.xml',
        'views/einvoice_catalog_13.xml',
        'views/uom_uom.xml',
        
        
    ],
    'auto_install': False,
    'installable': True
}
