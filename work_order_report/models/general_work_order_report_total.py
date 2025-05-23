from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class GeneralWorkOrderReportTotal(models.Model):
    _name="general.work.order.report.total"
    _description="Reporte General de Orden de Trabajo" 
    _auto=False

    project_id = fields.Many2one('project.project', string='OT')
    client_id = fields.Many2one('res.partner', string='Cliente OT')
    tag_names = fields.Text(string='Etiquetas')
    requested_period_id = fields.Many2one('account.period', string='Solicitado para mes de')
    schedule_date = fields.Date('Fecha de Programación')
    start_date = fields.Date('Fecha Inicio del Proyecto')
    end_date = fields.Date('Fecha Fin del Proyecto')
    report_delivery_date = fields.Date('Fecha de Entrega de Informes')
    invoice_date = fields.Date('Fecha de Facturación')
    sale_invoices_total = fields.Float('Total de Lineas de Ventas Facturadas')
    expenses_invoices_total = fields.Float('Total de Lineas de Gastos Facturados')
    kardex_total = fields.Float('Total Lineas de Kardex')
    hourly_cost_total = fields.Float('Total Costo Horas')
    net_total = fields.Float('Neto ')
    net_by_sale_total = fields.Float('% Neto/Ventas')
    estimated_usd_billings = fields.Float('Facturación Estimada USD')
    
    def get_report(self):

        self.env.cr.execute(f"""
            CREATE OR REPLACE view general_work_order_report_total as (
				SELECT row_number() OVER () AS id, data.* FROM(
                    {self.get_sql()}
                ) AS data
            )
        """)
        return {
            'name': 'Reporte General OT',
            'type': 'ir.actions.act_window',
            'res_model': 'general.work.order.report.total',
            'view_mode': 'tree',
            'view_type': 'form',
        }
        
    def get_sql(self):
        return self.get_with_sql() + self.get_select_sql() + self.get_from_sql() + self.get_where_sql()

    def sql_sale_totals(self):
        return f"""
            SELECT 
                SUM(vst1.balance) * - 1  AS total,
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
                SUM(vst1.balance) * - 1  AS total,
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
                ROUND(
                    SUM(
                        (
                            COALESCE(total.ingreso, 0) - COALESCE(total.salida, 0)
                        ) * COALESCE(total.unit_price, 0)
                    )::numeric ,
                    2
                ) AS total,
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
                        (vst_kardex_sunat.fecha - interval '5' HOUR)::DATE
                        BETWEEN 
                            '2020/01/01' AND
                            '{(datetime.now() - timedelta(hours=5)).strftime('%Y/%m/%d')}'
                    ) AND 
                    vst_kardex_sunat.company_id = {self.env.company.id} AND
                    sm.work_order_id  IS NOT NULL AND
                    vst_kardex_sunat.operation_type IN ('01','10','20','91','92')
                )Total	
            GROUP BY
                total.work_order_id
        """
        
    def get_hourly_cost_totals(self):
        return f"""
        SELECT
            ROUND(CAST(SUM(aal.total_cost_per_hour) * -1 AS numeric),2) AS total,
            aal.project_id as work_order_id
        FROM 
            account_analytic_line AS aal
            LEFT JOIN project_task AS pt ON pt.id = aal.task_id
            LEFT JOIN hr_employee AS he ON he.id = aal.employee_id
        WHERE
            aal.project_id IS NOT NULL AND
            aal.company_id = {self.env.company.id} AND
            (
                aal.date 
                BETWEEN 
                    '2020/01/01' AND
                    '{(datetime.now() - timedelta(hours=5)).strftime('%Y/%m/%d')}'
            )
        GROUP BY
            aal.project_id
        """

    def get_project_tag(self):
        return f"""
        SELECT 
            string_agg(pt.name, ', ') AS tags,
            pp_pt_rel.project_project_id AS project_id
        FROM 
            project_project_project_tags_rel AS pp_pt_rel
            LEFT JOIN project_tags AS pt ON pt.id = pp_pt_rel.project_tags_id
        WHERE
            pt.company_id = {self.env.company.id}
        GROUP BY
            pp_pt_rel.project_project_id
        """

    
    def get_with_sql(self):
        return f"""
            WITH 
                invoice_totals AS({self.sql_sale_totals()}),
                expenses_totals AS({self.sql_purchase_totals()}),
                kardex_totals AS({self.get_kardex_totals()}), 
                hourly_cost_totals AS ({self.get_hourly_cost_totals()}),
                fixed_project_tags AS ({self.get_project_tag()})
        """

    def get_select_sql(self):
        return """
            SELECT
                pp.id AS project_id,
                pp.partner_id AS client_id,
                fpt.tags AS tag_names,
                pp.requested_period_id AS requested_period_id,
                pp.schedule_date AS schedule_date,
                pp.date_start AS start_date,
                pp.date AS end_date,
                pp.report_delivery_date AS report_delivery_date,
                pp.invoice_date AS invoice_date,
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
                        (
                            (
                                COALESCE(it.total, 0) +
                                COALESCE(et.total, 0) +
                                COALESCE(kt.total, 0) +
                                COALESCE(hct.total, 0)
                            )
                         / NULLIF(it.total, 0)) * 100 AS numeric
                    ), 2
                ) AS net_by_sale_total,
                pp.estimated_usd_billings AS estimated_usd_billings
        """

    def  get_from_sql(self):
        return """
        FROM
            project_project AS pp 
            LEFT JOIN invoice_totals AS it ON it.work_order_id = pp.id
            LEFT JOIN expenses_totals AS et ON et.work_order_id = pp.id
            LEFT JOIN kardex_totals AS kt ON kt.work_order_id = pp.id
            LEFT JOIN hourly_cost_totals AS hct ON hct.work_order_id = pp.id
            LEFT JOIN fixed_project_tags AS fpt ON fpt.project_id = pp.id
        """
    
    def get_where_sql(self):
        return f"""
        WHERE
            pp.active AND
            pp.company_id = {self.env.company.id}
        """
