# -*- coding: utf-8 -*-
{
    'name': "Perú - Extended",
    'description': """
Peruvian accounting chart and tax localization extended.
Plan contable chileno e impuestos de acuerdo a disposiciones vigentes
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base_vat','l10n_latam_base','l10n_latam_invoice_document','l10n_pe'],

    # always loaded
    'data': [
        'data/l10n_latam_document_type_data.xml',
        'views/l10n_latam_document_type_view.xml',
    ]
}