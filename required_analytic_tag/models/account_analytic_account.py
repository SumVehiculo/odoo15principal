from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit="account.analytic.account"
    
    @api.model
    def create(self, vals):
        if not self.env.user.has_group("required_analytic_tag.create_analytic_account_group"):
            raise UserError("Solo lo usuarios del grupo: 'Permiso Crear Cuenta Analitica' pueden crear etiquetas analiticas.")
        return super().create(vals)