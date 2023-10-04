# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class CompanyBranch(models.Model):
    _name = 'res.company.branch.address'

    code = fields.Char('Codigo', required=True)
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', 'Contacto', required=True)
    company_id = fields.Many2one(
        'res.company', 'Empresa', required=True, default=lambda self:
        self.env['res.company']._company_default_get('account.account'))

    _sql_constraints = [
        ('code_company_branch_address_uniq', 'unique (code,company_id)',
         'The code of the operating unit must '
         'be unique per company!'),
        ('name_company_branch_address_uniq', 'unique (name,company_id)',
         'The name of the operating unit must '
         'be unique per company!')
    ]

    @api.model
    def get_session_info(self):
        user = self.env.user
        display_switch_company_menu = user.has_group('company_branch_address.group_multi_company_branch_address') and len(user.company_branch_address_ids) > 1
        return {
            "user_company_branch_addresss": {
                'current_company_branch_address': (user.default_company_branch_address_id.id, user.default_company_branch_address_id.name),
                'allowed_company_branch_addresss': [(comp.id, comp.name) for comp in user.company_branch_address_ids if user.company_id.id==comp.company_id.id]} if display_switch_company_menu else False
            }

    @api.model
    def get_user_company_branch_addresses(self):
        return [{'id':comp.id, 'name':comp.name} for comp in self.env.user.company_branch_address_ids if self.env.user.company_id.id==comp.company_id.id]
