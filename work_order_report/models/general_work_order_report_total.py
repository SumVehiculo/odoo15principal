from odoo import models, fields, api
from datetime import datetime, timedelta

class GeneralWorkOrderReportTotal(models.Model):
    _name="general.work.order.report.total"
    _description="Reporte General de Orden de Trabajo" 
    _auto=False

    project_id = fields.Many2one('project.project', string='OT')
    client_id = fields.Many2one('res.partner', string='Cliente OT')
    tag_ids = fields.Many2many('project.tags', string='Etiquetas')
    start_date = fields.Date('Fecha Inicio del Proyecto')
    end_date = fields.Date('Fecha Fin del Proyecto')
    sale_invoices_total = fields.Float('Total de Lineas de Ventas Facturadas')
    expenses_invoices_total = fields.Float('Total de Lineas de Gastos Facturados')
    kardex_total = fields.Float('Total Lineas de Kardex')
    hourly_cost_total = fields.Float('Total Costo Horas')
    net_total = fields.Float('Neto ')
    net_by_sale_total = fields.Float('% Neto/Ventas')
    
    def get_report(self):
        self.env.cr.execute(f"""
            CREATE OR REPLACE view sale_commercial_report as (
				SELECT row_number() OVER () AS id, data.* FROM(
                    {self.get_with_sql()}
                    {self.get_select_sql()}
                    {self.get_from_sql()}
                    {self.get_where_sql()}
                ) AS data
            )
        """)
        return {
            'name': 'Reporte Comercial',
            'type': 'ir.actions.act_window',
            'res_model': 'general.work.order.report.total',
            'view_mode': 'tree',
            'view_type': 'form',
        }
        
    
    def sql_sale_totals(self):
        return f"""
            SELECT 
                SUM(vst1.balance) * - 1  AS sale_invoice_total,
                aml.work_order_id AS work_order_id
            FROM 
                get_diariog(
                    '2020/01/01',
                    '{(datetime.now() - timedelta(hours=5)).strftime('%Y/%m/%d')}',
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
        """
    
    def sql_purchase_totals(self):
        return f"""
            SELECT 
                SUM(vst1.balance) * - 1  AS expenses_total,
                aml.work_order_id AS work_order_id
            FROM 
                get_diariog(
                    '2020/01/01',
                    '{(datetime.now() - timedelta(hours=5)).strftime('%Y/%m/%d')}',
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
        """

    def get_kardex_totals(self):
        return f"""
            SELECT 
                SUM((COALESCE(total.ingreso, 0) - COALESCE(total.salida, 0)) * COALESCE(total.unit_price, 0)) AS kardex_total,
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
                            '2020/01/01' AND
                            '{(datetime.now() - timedelta(hours=5)).strftime('%Y/%m/%d')}'
                    ) AND 
                    vst_kardex_sunat.company_id = {self.company_id.id} AND
                    sm.work_order_id  IS NOT NULL AND
                    vst_kardex_sunat.operation_type IN ('01','10','20','91','92')
                )Total	
            GROUP BY
                total.work_order_id
        """
        
    def get_hourly_cost_totals(self):
        return f"""
        SELECT
            SUM(aal.total_cost_per_hour) * -1 AS total_cost_per_hour,
            aal.project_id as work_order_id
        FROM 
            account_analytic_line AS aal
            LEFT JOIN project_task AS pt ON pt.id = aal.task_id
            LEFT JOIN hr_employee AS he ON he.id = aal.employee_id
        WHERE
            aal.project_id IS NOT NULL AND
            (
                aal.date 
                BETWEEN 
                    '2020/01/01' AND
                    '{(datetime.now() - timedelta(hours=5)).strftime('%Y/%m/%d')}'
            )
        GROUP BY
            aal.project_id
        """
    
    def get_with_sql(self):
        return f"""
            WITH 
                invoice_totals AS({self.sql_sale_totals()}),
                expenses_totals AS({self.sql_purchase_totals()}),
                kardex_totals AS({self.get_kardex_totals()}), 
                hourly_cost_totals AS ({self.get_hourly_cost_totals()})
        """
    
    def get_select_sql(self):
        return """
            SELECT
                pp.id AS project_id,
                pp.partner_id AS client_id,
                pp.date_start AS start_date,
                pp.date AS end_date,
                COALESCE(it.total,0) AS sale_invoices_total,
                COALESCE(et.total,0) AS expenses_invoices_total,
                COALESCE(kt.total,0) AS kardex_total,
                COALESCE(hct.total,0) AS hourly_cost_total,
                (
                    COALESCE(it.total,0) +
                    COALESCE(et.total,0) +
                    COALESCE(kt.total,0) +
                    COALESCE(hct.total,0) 
                ) AS net_total,
                ROUND(
                    CAST(
                        (ABS(
                            COALESCE(it.total, 0) +
                            COALESCE(et.total, 0) +
                            COALESCE(kt.total, 0) +
                            COALESCE(hct.total, 0)
                        ) / NULLIF(it.total, 0)) * 100 AS numeric
                    ), 2
                ) AS net_by_sale_total
        """

    def  get_from_sql(self):
        return """
        FROM
            project_project AS pp 
            LEFT JOIN invoice_totals AS it ON it.work_order_id = pp.id
            LEFT JOIN expenses_totals AS et ON et.work_order_id = pp.id
            LEFT JOIN kardex_totals AS kt ON kt.work_order_id = pp.id
            LEFT JOIN hourly_cost_totals AS hct ON hct.work_order_id = pp.id
        """
    
    def get_where_sql(self):
        return """
        WHERE
            pp.active AND
            pp.company_id = 1
        """
