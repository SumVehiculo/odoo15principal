from odoo import _, api, fields, models, tools
class account_personalizadas(models.Model): 
    _name = 'account.personalizadas'

    name = fields.Char(
        string="Concepto"
    )
    
    cuenta_mn_id = fields.Many2one(
        'account.account',
        string='Cuenta MN',
        )
    cuenta_me_id = fields.Many2one(
        'account.account',
        string='Cuenta ME',
        )
    
    p_type = fields.Selection([('receivable','Receivable'),('payable','Payable')],string='Tipo')

    
