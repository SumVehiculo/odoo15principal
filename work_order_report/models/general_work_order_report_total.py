from odoo import models, fields, api
from datetime import datetime, timedelta

class GeneralWorkOrderReportTotal(models.Model):
    _name="general.work.order.report.total"
    _description="Reporte General de Orden de Trabajo" 

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
        self.env.cr.execute("DELETE FROM general_work_order_report_total")
        self.env.cr.execute("ALTER SEQUENCE public.general_work_order_report_total_id_seq RESTART WITH 1")
        self.generate_data()
        return {
            'name': 'Reporte General OT',
			'type': 'ir.actions.act_window',
			'res_model': 'general.work.order.report.total',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(self.env.ref('work_oredr_report.general_work_order_report_total_view_tree').id, 'tree')],
			'target': 'current',
        }
        
        
    def get_sale_invoice_totals(self):
        query= f"""
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
            ;
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def get_kardex_totals(self):
        query= f"""
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
            ;
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
        
    def get_hourly_cost_totals(self):
        query=f"""
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
        ;
        
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    def generate_data(self):
        sales = self.get_sale_invoice_totals()
        expenses = self.get_expenses_totals()
        kardex = self.get_kardex_totals()
        hourly_cost =self.get_hourly_cost_totals()
        
        projects = self.env['project.project'].search([
            ('active','=',True),
            ('company_id','=',self.company_id.id),
            ('is_internal_project', '=', False)
        ])
        
        
        for project in projects:
            sale_data=next(filter(lambda s: s['work_order_id'] == project.id,sales),0) 
            expenses_data=next(filter(lambda e: e['work_order_id'] == project.id,expenses),0) 
            kardex_data=next(filter(lambda k: k['work_order_id'] == project.id,kardex),0) 
            hourly_cost_data=next(filter(lambda h: h['work_order_id'] == project.id,hourly_cost),0) 
            
            sale_data = sale_data['sale_invoice_total'] if sale_data else 0
            expenses_data = expenses_data['expenses_total'] if expenses_data else 0
            kardex_data = kardex_data['kardex_total'] if kardex_data else 0
            hourly_cost_data = hourly_cost_data['total_cost_per_hour'] if hourly_cost_data else 0
            
            
            result={}
            result['project_id']=project.id
            result['client_id']=project.partner_id.id
            result['start_date']=project.date_start
            result['end_date']=project.date
            result['tag_ids']=project.tag_ids.ids
            result['sale_invoices_total']=sale_data
            result['expenses_invoices_total']=expenses_data
            result['kardex_total']=kardex_data
            result['hourly_cost_total']=hourly_cost_data
            
            net_total=sum([
                sale_data,
                expenses_data,
                kardex_data,
                hourly_cost_data
            ])
            result['net_total']=net_total
            result['net_by_sale_total']=round((abs(net_total)/(sale_data if sale_data else 1))*100,2)
            self.env['general.work.order.report.total'].create(result)
    
    