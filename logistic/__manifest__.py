{
    "name": "Logistic",
    "description": "Agrega gestion de guias de remision",
    "depends": ["base","portal","account","stock","fleet"],
    'version': '15.0.1.0.0',
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/expedition_view.xml',
        "data/sequences.xml",
        'views/res_partner_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_warehouse_view.xml',
        'views/despatch_view.xml',
        'views/logistic_report.xml',
        'views/menuitem_view.xml',
        'views/account_journal_view.xml',
        'data/mail_template_data.xml',
        'views/report_despatch.xml',
        'wizards/logistic_despatch_send_views.xml',
        'views/res_config_settings_view.xml'
        ],
    'application': True,
}
