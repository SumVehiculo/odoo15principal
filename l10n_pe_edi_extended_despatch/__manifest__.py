{
    'name': "Perú - E-Despatch",

    'summary': """
        Add Electronic Despatch integration.""",

    'description': """
        Add Electronic Despatch integration.
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization/Peru',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    "depends": ["logistic","l10n_pe_edi_extended"],
    
    # always loaded
    "data": [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/logistic_despatch_view.xml',
        'views/report_despatch.xml',
        'views/product_view.xml',
        'views/stock_location_view.xml',
        'views/res_partner_view.xml',
    ],
}
