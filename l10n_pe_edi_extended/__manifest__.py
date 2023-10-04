# -*- coding: utf-8 -*-
{
    'name': "Perú - E-invoicing",

    'summary': """
        Adds direct relation between location and warehouse.""",

    'description': """
        Adds direct relation between location and warehouse.
    """,

    'author': "Conflux",
    'website': "https://conflux.pe",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization/Peru',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'base', 'web', 'uom','account_debit_note','l10n_pe_extended','l10n_latam_base','l10n_latam_invoice_document'],

    # always loaded
    'data': [
        "security/ir.model.access.csv",
        'data/account_tax_data.xml',
        'data/currency_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'wizards/l10n_pe_dte_move_cancel_view.xml',
        'views/res_company_view.xml',
        'views/account_journal_view.xml',
        'views/account_tax_view.xml',
        'views/account_move_view.xml',
        'views/product_uom_view.xml',
        'views/product_view.xml',
        'views/res_config_settings_view.xml',
        #'views/account_report.xml',
        'views/report_invoice.xml',
        'wizards/account_debit_note_view.xml',
        'wizards/account_invoice_refund_view.xml',
    ],
    'sequence': 1,
}