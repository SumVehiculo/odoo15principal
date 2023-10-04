from odoo import _, api, fields, models, tools

class account_move(models.Model):

    _inherit = 'account.move'


    @api.constrains('name', 'partner_id', 'company_id', 'posted_before')
    def _check_unique_vendor_number(self):
      return