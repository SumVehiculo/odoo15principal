# -*- coding: utf-8 -*-
{
    'name': "Integration EDI Despatch - IT Grupo",
    'description': """
Integracion de catalogos de sunat IT Grupo con guia de remision electronica internacional
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['l10n_pe_edi_extended_despatch'],

    # always loaded
    'data': [
        #'views/account_move_view.xml',
        #'views/company_branch_address_view.xml',
        #'views/report_invoice.xml',
    ]
}
