# -*- coding: utf-8 -*-
{
    'name': "Perú Transport Docs - E-invoicing",

    'summary': """
        Adds Integration with transport docs.""",

    'description': """
        Adds Integration with transport docs.
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization/Peru',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['l10n_pe_edi_extended'],

    # always loaded
    'data': [
        "security/ir.model.access.csv",
        'views/account_move_view.xml',
        'views/report_invoice.xml',
    ]
}