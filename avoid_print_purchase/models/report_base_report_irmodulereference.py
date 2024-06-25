from odoo import models, fields, api
from odoo.exceptions import UserError

class ReportBaseReportirmodulereference(models.AbstractModel):
    _inherit = 'report.base.report_irmodulereference'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids,data)
        raise UserError(f"prueba reporte")
        return res
        report = self.env['ir.actions.report']._get_report_from_name('base.report_irmodulereference')
        selected_modules = self.env['ir.module.module'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': selected_modules,
            'findobj': self._object_find,
            'findfields': self._fields_find,
        }