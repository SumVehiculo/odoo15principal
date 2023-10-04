# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brands'

    name = fields.Char(string='Marca', required=True, translate=True)
    logo = fields.Binary(string='Logo')
    visible_slider = fields.Boolean(string='Visible en Website',default=True)
    active = fields.Boolean(string='Activo',default=True)
    product_ids = fields.One2many(
        'product.template',
        'product_brand_id',
        string='Productos',
    )
    products_count = fields.Integer(
        string='Numero De Productos',
        compute='_get_products_count',
    )

    @api.depends('product_ids')
    def _get_products_count(self):
        self.products_count = len(self.product_ids)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand',
        string='Marca',
        help='Seleccione La Marca Del Producto'
    )


class sale_order(models.Model):
    _inherit = 'sale.order'

    date_order = fields.Datetime(string='Order Date', required=True, readonly=False, index=True, states={}, copy=False, default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    


class SaleReport(models.Model):
    _inherit = "sale.report"

    marca = fields.Char('Marca')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['marca'] = ", pb.name as marca"
        
        groupby += ', pb.name'
        from_clause += '  left join product_brand pb on pb.id = t.product_brand_id'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
