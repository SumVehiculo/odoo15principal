from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAnalyticTag(models.Model):
    _inherit="account.analytic.tag"
    
    @api.model
    def create(self, vals):
        if not self.env.user.has_group("required_analytic_tag.create_analytic_tag_group"):
            raise UserError("Solo lo usuarios en el grupo: 'Crear Etiquetas Analiticas' pueden crear etiquetas analiticas.")
        return super().create(vals)