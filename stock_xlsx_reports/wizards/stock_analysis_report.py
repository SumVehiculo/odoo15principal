from odoo import models, fields, api
from odoo.exceptions import UserError

from xlsxwriter.workbook import Workbook
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64

class StockAnalysisReport(models.Model):
    _name="stock.analysis.report"
    _description="Reporte de Analisis de Inventario"
    
    
    company_id = fields.Many2one(
        'res.company', 
        string='company',
        default = lambda self:self.env.company.id
    )
    period_id = fields.Many2one(
        'account.period', 
        string='Periodo',
        domain="[('is_opening_close','=',False)]",
        required=True
    )

    def styles(self, workbook):
        result={}
        base={
            'valign': 'vcenter',
            'text_wrap': True,
            'font_name': 'Arial'
        }
        result['title']= workbook.add_format(
            {
                **base,   
                'bold': True,
                'font_size': 11
            }
        )
        result['title_underline']= workbook.add_format(
            {
                **base,
                'bold': True,
                'font_size': 11,
                'underline':1
            }
        )
        result['text']= workbook.add_format(
            {
                **base,
                'font_size': 8
            }
        )
        result['text_right']= workbook.add_format(
            {
                **base,
                'font_size': 8,
                'align': 'right',
            }
        )
        result['text_center']= workbook.add_format(
            {
                **base,
                'font_size': 8,
                'align': 'center',
            }
        )
        result['header_gray']= workbook.add_format(
            {
                **base,
                'bold': True,
                'align': 'center',
                'font_size': 8,
                'bg_color': '#EDEDED',
                'border':1,
                'border_color':'#898788'
            }
        )
        result['header_strong_gray']= workbook.add_format(
            {
                **base,
                'bold': True,
                'align': 'center',
                'font_size': 8,
                'bg_color': '#D9D9D9',
                'border':1,
                'border_color':'#898788'
            }
        )
        result['header_strong_gray_right']= workbook.add_format(
            {
                **base,
                'bold': True,
                'align': 'right',
                'font_size': 8,
                'bg_color': '#D9D9D9',
                'border':1,
                'border_color':'#898788'
            }
        )
        result['header_blue']= workbook.add_format(
            {
                **base,
                'bold': True,
                'align': 'center',
                'font_size': 8,
                'bg_color': '#D6DCE4',
                'border':1,
                'border_color':'#898788'
            }
        )
        result['header_green']= workbook.add_format(
            {
                **base,
                'bold': True,
                'align': 'center',
                'font_size': 8,
                'bg_color': '#E2EFDA',
                'border':1,
                'border_color':'#898788'
            }
        )
        result['header_green_right']= workbook.add_format(
            {
                **base,
                'bold': True,
                'align': 'right',
                'font_size': 8,
                'bg_color': '#E2EFDA',
                'border':1,
                'border_color':'#898788'
            }
        )
        return result
    
    def get_with(self):
        return f"""
            WITH
                supplier_data AS (
                    SELECT
                        MIN(ps.sequence) as sequence,
                        ps.product_tmpl_id as product_tmpl_id,
                        rc.name as currency,
                        ps.price
                    FROM 
                        product_supplierinfo AS ps
                        LEFT JOIN res_currency as rc ON rc.id = ps.currency_id
                    GROUP BY
                        ps.product_tmpl_id,
                        rc.name,
                        ps.price
                ),
                product_label AS (
                    SELECT
                        pp_t.id, 
                        (
                            (max((pt_t.name->>'es_PE')::text)::character varying::text || ' '::text)
                            ||
                            replace(array_agg(pav.name)::character varying::text, '{{NULL}}'::text, ''::text)
                        )::character varying AS name
                    FROM 
                        product_product AS pp_t
                        JOIN product_template pt_t ON pt_t.id = pp_t.product_tmpl_id
                        LEFT JOIN product_variant_combination pvc on pvc.product_product_id = pp_t.id
                        LEFT JOIN product_template_attribute_value ptav on ptav.id = pvc.product_template_attribute_value_id
                        LEFT JOIN product_attribute_value pav on pav.id = ptav.product_attribute_value_id
                    GROUP BY
                        pp_t.id
                ),
                initial_stock AS (
                    SELECT 
                        product_id,
                        SUM (entry - output) as balance
                    FROM (
                        SELECT  product_qty as entry, 0 as output, product_id
                        FROM vst_kardex_fisico_lote() AS kardex_lote
                        LEFT JOIN stock_location AS sl ON sl.id = kardex_lote.location_dest_id
                        WHERE
                            sl.usage = 'internal' AND
                            kardex_lote.estado = 'done' AND
                            (date - INTERVAL '5 hours')::date  <= '{self.period_id.date_start - timedelta(days=1)}' 
                        UNION ALL
                        SELECT  0 as entry, product_qty as output, product_id
                        FROM  vst_kardex_fisico_lote() AS kardex_lote
                        LEFT JOIN stock_location AS sl ON sl.id = kardex_lote.location_id
                        WHERE
                            sl.usage = 'internal' AND
                            kardex_lote.estado = 'done' AND
                            (date - INTERVAL '5 hours')::date  <= '{self.period_id.date_start - timedelta(days=1)}' 
                    ) raw_kardex
                    GROUP BY
                        product_id
                    ORDER BY
                        product_id
                ),
                final_stock AS (
                    SELECT 
                        product_id,
                        SUM (entry - output) as balance
                    FROM (
                        SELECT  product_qty as entry, 0 as output, product_id
                        FROM vst_kardex_fisico_lote() AS kardex_lote
                        LEFT JOIN stock_location AS sl ON sl.id = kardex_lote.location_dest_id
                        WHERE
                            sl.usage = 'internal' AND
                            kardex_lote.estado = 'done' AND
                            (date - INTERVAL '5 hours')::date  <= '{self.period_id.date_end}' 
                        UNION ALL
                        SELECT  0 as entry, product_qty as output, product_id
                        FROM  vst_kardex_fisico_lote() AS kardex_lote
                        LEFT JOIN stock_location AS sl ON sl.id = kardex_lote.location_id
                        WHERE
                            sl.usage = 'internal' AND
                            kardex_lote.estado = 'done' AND
                            (date - INTERVAL '5 hours')::date  <= '{self.period_id.date_end}' 
                    ) raw_kardex
                    GROUP BY
                        product_id
                    ORDER BY
                        product_id
                ),
                vendors_stock_move AS (
                    SELECT 
                        sm.product_id,
                        SUM(
                            sm.quantity
                        ) as qty
                    FROM
                        stock_move AS sm 
                        LEFT JOIN stock_picking AS sp ON sp.id = sm.picking_id
                        LEFT JOIN stock_location AS sl ON sl.id = sp.location_dest_id 
                    WHERE
                        sp.state = 'done' AND
                        (sp.kardex_date - INTERVAL '5 hours')::date BETWEEN '{self.period_id.date_start}' AND '{self.period_id.date_end}' AND
                        sl.name ilike 'vendors'
                    GROUP BY
                        product_id
                ),
                customer_stock_move AS (
                    SELECT 
                        sm.product_id,
                        SUM(
                            sm.quantity
                        ) as qty
                    FROM
                        stock_move AS sm 
                        LEFT JOIN stock_picking AS sp ON sp.id = sm.picking_id
                        LEFT JOIN stock_location AS sl ON sl.id = sp.location_dest_id 
                    WHERE
                        sp.state = 'done' AND
                        (sp.kardex_date - INTERVAL '5 hours')::date BETWEEN '{self.period_id.date_start}' AND '{self.period_id.date_end}' AND
                        sl.name ilike 'customers'
                    GROUP BY
                        product_id
                ),
                other_stock_move AS (
                    SELECT 
                        sm.product_id,
                        SUM(
                            sm.quantity
                        ) as qty
                    FROM
                        stock_move AS sm 
                        LEFT JOIN stock_picking AS sp ON sp.id = sm.picking_id
                        LEFT JOIN stock_location AS sl ON sl.id = sp.location_dest_id 
                    WHERE
                        sp.state = 'done' AND
                        (sp.kardex_date - INTERVAL '5 hours')::date BETWEEN '{self.period_id.date_start}' AND '{self.period_id.date_end}' AND
                        sl.name not ilike 'vendors' AND 
                        sl.name not ilike 'customers'
                    GROUP BY
                        product_id
                ),
                total_sales AS (
                    SELECT 
                        aml.product_id,
                        SUM(
                            vst1.debe - vst1.haber
                        ) AS total
                    FROM 
                        get_diariog(
                            '{self.period_id.date_start.strftime("%Y-%m-%d")}',
                            '{self.period_id.date_end.strftime("%Y-%m-%d")}',
                            {self.company_id.id}
                        ) vst1
                        LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                        LEFT JOIN account_move am on am.id = aml.move_id
                        LEFT JOIN product_product pp on pp.id = aml.product_id
                    WHERE 
                        vst1.cuenta LIKE '7%' 
                        AND am.state = 'posted'
                    GROUP BY
                        aml.product_id
                )
    """
    
    def get_select(self):
        return f"""
        SELECT 
            pp.default_code as code,
            product_label.name as description,
            uu.name ->> 'es_PE' AS uom,
            supplier_data.currency as currency,
            COALESCE(supplier_data.price,0) as supplier_price,
            COALESCE(initial_stock.balance,0) as initial_stock,
            COALESCE(vendors_stock_move.qty,0) AS purchase_stock,
            COALESCE(customer_stock_move.qty,0) AS sale_stock,
            COALESCE(other_stock_move.qty,0) as other_stock,
            COALESCE(final_stock.balance,0) as final_stock,
            COALESCE(total_sales.total,0) as total_sales
        """
    
    def get_from(self):
        return f"""
        FROM 
            stock_move as sm
            LEFT JOIN uom_uom AS uu ON uu.id = sm.product_uom
            LEFT JOIN product_product AS pp ON pp.id = sm.product_id
            LEFT JOIN product_template AS pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_label ON product_label.id = pp.id
            LEFT JOIN supplier_data ON supplier_data.product_tmpl_id = pt.id
            LEFT JOIN initial_stock ON initial_stock.product_id = pp.id
            LEFT JOIN vendors_stock_move ON vendors_stock_move.product_id = pp.id
            LEFT JOIN customer_stock_move ON customer_stock_move.product_id = pp.id
            LEFT JOIN other_stock_move ON other_stock_move.product_id = pp.id
            LEFT JOIN final_stock ON final_stock.product_id = pp.id
            LEFT JOIN total_sales ON total_sales.product_id = pp.id
        """
    def get_group_by(self):
        return f"""
        GROUP BY
            pp.default_code,
            product_label.name,
            uu.name,
            supplier_data.currency,
            supplier_data.price,
            initial_stock.balance,
            vendors_stock_move.qty,
            customer_stock_move.qty,
            other_stock_move.qty,
            final_stock.balance,
            total_sales.total
        """
    def get_sql(self):
        return self.get_with() + self.get_select() + self.get_from() + self.get_group_by()
    
    
    
    
    def get_kardex_balance(self):
        start_date = self.period_id.date_start
        end_date = self.period_id.date_end
        
        kardex_backup = self.env['kardex.save'].search([
            ('company_id','=',self.env.company.id),
            ('state','=','done'),
            ('name.date_end','<',self.fini)
        ])
        backup_sql=""
        if kardex_backup:
            kardex_backup = kardex_backup.sorted(lambda l: l.name.code , reverse=True)[0]
            start_date = kardex_backup.name.date_end + timedelta(days=1)
            backup_sql=f"""
            UNION ALL
            
            SELECT
                ksp.producto AS product_id,
                ksp.stock AS income,
                0 AS outcome,
                ksp.cprom * ksp.stock AS debit,
                0 AS credit,
                '' AS origin,
                sl.usage AS destination
            FROM
                kardex_save_period ksp
                INNER JOIN stock_location sl ON sl.id = ksp.almacen
            WHERE
                save_id = {kardex_backup.id}
            """
        
        
        
        kardex_sql=f"""
        SELECT 
            * 
        FROM (
            SELECT
                physical_kardex.product_id,
                ingreso AS income,
                salida as outcome,
                debit,
                credit,
                sl_o.usage AS origin,
                sl_d.usage AS destination
            FROM 
                vst_kardex_fisico_valorado AS physical_kardex
                LEFT JOIN stock_move sm ON sm.id = physical_kardex.stock_moveid
                LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                INNER JOIN stock_location sl_o ON sl_o.id = sm.location_id
                INNER JOIN stock_location sl_d ON sl_d.id = sm.location_dest_id
            WHERE
                (sm.kardex_date INTERVAL '5 hours')::date BETWEEN '{start_date}' AND '{end_date}'
            {backup_sql}
        )
        ORDER BY
            physical_kardex.location_id,
            physical_kardex.product_id
        ;
        """
        kardex_balance = {}
        self.env.cr.execute(self.get_sql())
        for data in self.env.cr.dictfetchall():
            average_cost = kardex_balance.get(
                data['product_id'],
                {
                    'qty':0,
                    'amount':0
                }
            )
            income=data.get('ingreso',0)
            outcome=data.get('salida',0)
            debit=data.get('debit',0)
            credit=data.get('credit',0)
            unit_cost=average_cost.get('amount') / average_cost.get('qty') if average_cost.get('qty') else 0
            if data['ingreso'] or data['debit']:
                average_cost['qty'] += ( income -  outcome)
                average_cost['amount'] += ( debit -  credit)
            else:
                if (data['origen'] == 'internal' and data['destino'] == 'supplier'):
                    average_cost['qty'] -= outcome
                    average_cost['amount'] -= (debit - credit * outcome)
                else:
                    average_cost['qty'] += ( income -  outcome)
                    average_cost['amount'] -= (outcome * unit_cost) if outcome else credit
            average_cost['amount'] = average_cost['amount'] if average_cost['qty'] > 0 else 0
            kardex_balance[data['product_id']] = average_cost
        return kardex_balance
    
    
    
    def get_report(self):
        filename="Reporte_Analisis_inventario.xlsx"
        
        workbook = Workbook(filename)   
        worksheet = workbook.add_worksheet("Rep. Productos")
        worksheet.set_tab_color('blue')
        styles=self.styles(workbook)
        row=1
        worksheet.merge_range(row, 1, row, 2, f"{self.company_id.name}",styles['title'])
        row+=1
        worksheet.write(row, 2, 'REPORTE DE PRODUCTOS',styles['title_underline'])
        row+=2
        column=0
        kardex_balanced=self.get_kardex_balance()

        headers=[
            "Nro",
            "Codigo",
            "Desc CL-Factura",
            "UM",
            "Moneda",
            "Importe"
        ]
        for header in headers:
            worksheet.write(row, column, header.upper(), styles['header_gray'])
            column+=1
        worksheet.merge_range(row-1, column-2, row-1, column-1, "VALOR UNIT.",styles['header_gray'])
        months_label=[
            'Enero',
            'Febrero',
            'Marzo',
            'Abril',
            'Mayo',
            'Junio',
            'Julio',
            'Agosto',
            'Septiembre',
            'Octubre',
            'Noviembre',
            'Diciembre',
        ]
        headers_per_month=[
            'Stock Inicial',
            'INGRESOS ',
            'VENTAS',
            'OTROS',
            'Stock de Cierre',
        ]
        worksheet.merge_range(
            row-1, 
            column, 
            row-1, 
            column+len(headers_per_month) - 1 ,
            f"MOVIMIENTOS {months_label[self.period_id.date_start.month - 1].upper()} {self.period_id.date_start.year}",
            styles['header_blue']
        )
        for header in headers_per_month:
            worksheet.write(row, column, header.upper(), styles['header_blue'])
            column+=1
            
        headers=[
            "Total de Ventas",
            "Promedio de Ventas"
        ]
        for header in headers:
            worksheet.write(row, column, header.upper(), styles['header_green'])
            column+=1
        worksheet.write(row, column, 'VALORIZADO CIERRE', styles['header_gray'])
        column+=1
        row+=1

        row_counter=0
        
        # raise UserError(self.get_sql())
        
        self.env.cr.execute(self.get_sql())
        for record in self.env.cr.dictfetchall():
            worksheet.write(row, 0, f"{row_counter}",styles['text'])
            worksheet.write(row, 1, record['code'],styles['text'])
            worksheet.write(row, 2, record['description'],styles['text'])
            worksheet.write(row, 3, record['uom'],styles['text'])
            worksheet.write(row, 4, record['currency'],styles['text'])
            worksheet.write(row, 5, record['supplier_price'],styles['text'])
            
            worksheet.write(row, 6, record['initial_stock'],styles['text'])
            worksheet.write(row, 7, record['purchase_stock'],styles['text'])
            worksheet.write(row, 8, record['sale_stock'],styles['text'])
            worksheet.write(row, 9, record['other_stock'],styles['text'])
            worksheet.write(row, 10, record['final_stock'],styles['text'])
            worksheet.write(row, 11, record['total_sales'],styles['text'])
            worksheet.write(row, 12, record['total_sales']/self.period_id.date_start.month,styles['text'])
            row+=1
            row_counter+=1
        
        # Widths Columns
        width_columns=[4,9,55,8,8,9]
        # Months Columns
        width_columns+=([12] * len(headers_per_month))
        # Extra Columns
        width_columns+=([12] * 3)
        for count,column in enumerate(width_columns):
            worksheet.set_column(count, count, column)
        
        workbook.close()
        f = open(filename, 'rb')
        return self.env['popup.it'].get_file(
            filename,
            base64.encodebytes(b''.join(f.readlines()))
        )