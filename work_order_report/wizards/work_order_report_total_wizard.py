from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WorkOrderReportTotalWizard(models.TransientModel):
    _name="work.order.report.total.wizard"
    _description="Wizard Reporte Orden de Trabajo Total"
    
    company_id = fields.Many2one(
        'res.company', 
        string='Compañia',
        default= lambda self: self.env.company.id
    )
    start_date= fields.Date('Desde', required=True)
    end_date = fields.Date('Hasta', required=True)
    
    def get_report(self):
        self.env.cr.execute("DELETE FROM general_work_order_report_total")
        self.env.cr.execute("ALTER SEQUENCE public.general_work_order_report_total_id_seq RESTART WITH 1")
        self.generate_data()
        return self.env.ref('work_order_report.general_work_order_report_total_action').read()[0]
        
        
    def get_sale_invoice_totals(self):
        query= f"""
            SELECT 
                SUM(vst1.balance) * - 1  AS sale_invoice_total,
                aml.work_order_id AS work_order_id
            FROM 
                get_diariog(
                    '{self.start_date.strftime('%Y/%m/%d')}',
                    '{self.end_date.strftime('%Y/%m/%d')}',
                    {self.env.company.id}
                ) vst1
                LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                LEFT JOIN account_move am on am.id = aml.move_id
                LEFT JOIN product_product pp on pp.id = aml.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN account_account aa on aa.code = vst1.cuenta
            WHERE 
                (
                    vst1.cuenta LIKE '7%'
                ) AND
                aml.work_order_id  IS NOT NULL AND
                aa.company_id = {self.env.company.id} AND
                am.state = 'posted'
            GROUP BY
                aml.work_order_id
            ;
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    def get_expenses_totals(self):
        query= f"""
            SELECT 
                SUM(vst1.balance) * - 1  AS expenses_total,
                aml.work_order_id AS work_order_id
            FROM 
                get_diariog(
                    '{self.start_date.strftime('%Y/%m/%d')}',
                    '{self.end_date.strftime('%Y/%m/%d')}',
                    {self.env.company.id}
                ) vst1
                LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                LEFT JOIN account_move am on am.id = aml.move_id
                LEFT JOIN product_product pp on pp.id = aml.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN account_account aa on aa.code = vst1.cuenta
            WHERE 
                (
                    vst1.cuenta LIKE '62%' OR 
                    vst1.cuenta LIKE '63%' OR 
                    vst1.cuenta LIKE '64%' OR
                    vst1.cuenta LIKE '65%' OR
                    vst1.cuenta LIKE '66%' OR
                    vst1.cuenta LIKE '67%' OR
                    vst1.cuenta LIKE '68%'
                ) AND
                aml.work_order_id  IS NOT NULL AND
                aa.company_id = {self.env.company.id} AND
                am.state = 'posted'
            GROUP BY
                aml.work_order_id
            ;
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
   
    def get_kardex_totals(self):
        query= f"""
            SELECT 
                (total.ingreso - total.salida) *  total.unit_price as kardex_total,
                total.work_order_id
            FROM (
                SELECT 
                    vst_kardex_sunat.*,
                    sm.price_unit_it as unit_price,
                    sm.work_order_id
                FROM vst_kardex_fisico_valorado AS vst_kardex_sunat
                    LEFT JOIN stock_move sm ON sm.id = vst_kardex_sunat.stock_moveid
                WHERE 
                    (
                        fecha_num((vst_kardex_sunat.fecha - interval '5' HOUR)::DATE) 
                        BETWEEN 
                            {self.start_date.strftime('%Y%m%d')} AND 
                            {self.end_date.strftime('%Y%m%d')}
                    ) AND 
                    vst_kardex_sunat.company_id = {self.company_id.id} AND
                    sm.work_order_id  IS NOT NULL AND
                    vst_kardex_sunat.operation_type IN ('01','10','20','91','92')
                )Total	
            GROUP BY
                total.work_order_id
            ;
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
        
    def generate_data(self):
        projects = self.env['project.project'].search([
            ('create_date','>=',self.start_date),
            ('create_date','<=',self.end_date),
        ])
        for project in projects:
            
            result={}
            result['project_id']=project.id
            result['client_id']=project.partner_id
            result['create_date']=project.create_date
            result['start_date']=project.date_start
            result['end_date']=project.date
            
            
            # result['sale_invoices_total']=project
            # result['expenses_invoices_total']=project
            # result['kardex_total']=project
            # result['hourly_cost_total']=project
            # result['net_total']=project
            # result['net_by_sale_total']=project
            self.env['general.work.order.report.total'].create(result)