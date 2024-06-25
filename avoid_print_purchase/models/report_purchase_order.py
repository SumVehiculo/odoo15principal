from odoo import models, fields, api
from odoo.exceptions import UserError

class ReportPurchaseOrder(models.AbstractModel):
    _name = "report.purchase.order"
    _description = "Reporte Abstracto"
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['purchase.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'purchase.order',
            'docs': docs,
            'proforma': True
            }