# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class product_category(models.Model):
    _inherit = "product.category"

    empresa_field = fields.Selection(selection=[('sum', 'SUM'),('sumas', 'SUMMAS'),('csi', 'CSI'),], string='Empresa')



class PurchaseReport(models.Model):
    _inherit = "purchase.report"

#    account_analytic_id = fields.Many2one("account.analytic.account",string="Cuenta Analítica")
    analytic_tag_ids = fields.Many2many("account.analytic.tag",string="Etiquetas Analíticas")
    analytic_tag_ids_name = fields.Char(string="Etiquetas Analíticas")
    def _select(self):
        t = super(PurchaseReport,self)._select()
        t += ", array_agg(rel_etiq.account_analytic_tag_id) as analytic_tag_ids, array_agg( aat.name || ', ')::varchar as analytic_tag_ids_name"
        return t

#    def _group_by(self):
#        t = super(PurchaseReport,self)._group_by()
#        t += ", l.account_analytic_id"
#        return t

    def _from(self):
        t = super(PurchaseReport,self)._from()
        t += """
            left join account_analytic_tag_purchase_order_line_rel rel_etiq on rel_etiq.purchase_order_line_id = l.id 
            left join account_analytic_tag aat on aat.id = rel_etiq.account_analytic_tag_id
            """
        return t


class SaleReport(models.Model):
    _inherit = "sale.report"

#    account_analytic_id = fields.Many2one("account.analytic.account",string="Cuenta Analítica")
    analytic_tag_ids = fields.Many2many("account.analytic.tag",string="Etiquetas Analíticas")
    analytic_tag_ids_name = fields.Char(string="Etiquetas Analíticas")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['analytic_tag_ids'] = ", array_agg(rel_etiq.account_analytic_tag_id) as analytic_tag_ids"
        fields['analytic_tag_ids_name'] = ", array_agg( aat.name || ', ')::varchar as analytic_tag_ids_name"
        from_clause += 'left join account_analytic_tag_sale_order_line_rel rel_etiq on rel_etiq.sale_order_line_id = l.id left join account_analytic_tag aat on aat.id = rel_etiq.account_analytic_tag_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
