# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools

class product_template(models.Model):
    _inherit = 'product.template'    
    
    @api.constrains('default_code')
    def _check_sku_no_repeat(self):
        for i in self:
            if i.default_code:
                producto = self.env['product.template'].sudo().search([('default_code','=',i.default_code)])
                if producto:
                    for p in producto:
                        if p.id != i.id:
                            raise UserError("No Se Puede Crear Un Producto Con Referencia Interna Duplicada")                