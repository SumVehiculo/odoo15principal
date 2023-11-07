# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class product_category(models.Model):
    _inherit = "product.category"

    empresa_field = fields.Selection(selection=[('sum', 'SUM'),('sumas', 'SUMMAS'),('csi', 'CSI'),], string='Empresa')



class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    account_analytic_id = fields.Many2one("account.analytic.account",string="Cuenta Analítica")
    analytic_tag_ids = fields.Many2many("account.analytic.tag",string="Etiquetas Analíticas")

    def _select(self):
        t = super(PurchaseReport,self)._select()
        t += ", l.account_analytic_id, array_agg(l.analytic_tag_ids) as analytic_tag_ids"
        return t
    def _group_by(self):
        t = super(PurchaseReport,self)._group_by()
        t += ", l.account_analytic_id"
        return t



class SaleReport(models.Model):
    _inherit = "sale.report"

#    account_analytic_id = fields.Many2one("account.analytic.account",string="Cuenta Analítica")
    analytic_tag_ids = fields.Many2many("account.analytic.tag",string="Etiquetas Analíticas")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['account_analytic_id'] = ", array_agg(l.analytic_tag_ids) as analytic_tag_ids"
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
