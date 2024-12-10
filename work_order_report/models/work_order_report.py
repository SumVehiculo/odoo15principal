import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from  xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_col_to_name
from datetime import datetime


class WorkOrderReport(models.Model):
    _name="work.order.report"
    _description="Reporte Por Orden de Trabajo"
    
    company_id = fields.Many2one(
        'res.company', 
        string='Compañia',
        default= lambda self: self.env.company.id
    )
    work_order_id = fields.Many2one('project.project', string='OT', required=True)
    # start_date= fields.Date('Desde', required=True)
    # end_date = fields.Date('Hasta', required=True)
   
    def get_report(self):
        filename = f"Reporte Por OT-{self.work_order_id.name}.xlsx"
        workbook = Workbook(filename)
        worksheet = workbook.add_worksheet("Reporte OT")
        worksheet.set_tab_color('blue')
        # Formats
        formats={}
        format_title = workbook.add_format({'bold': True})
        format_title.set_align('center')
        format_title.set_align('vcenter')
        format_title.set_text_wrap()
        format_title.set_font_size(12)
        format_title.set_font_name('Times New Roman')
        formats['title'] = format_title
        
        format_detail = workbook.add_format({'bold': True})
        format_detail.set_align('left')
        format_detail.set_align('vcenter')
        format_detail.set_text_wrap()
        format_detail.set_font_size(9)
        format_detail.set_font_name('Times New Roman')
        formats['detail'] = format_detail
        
        format_detail_right = workbook.add_format({'bold': True})
        format_detail_right.set_align('right')
        format_detail_right.set_align('vcenter')
        format_detail_right.set_text_wrap()
        format_detail_right.set_font_size(9)
        format_detail_right.set_font_name('Times New Roman')
        formats['detail_right'] = format_detail_right
        
        format_detail_border = workbook.add_format({'bold': True, 'bottom':1})
        format_detail_border.set_align('left')
        format_detail_border.set_align('vcenter')
        format_detail_border.set_text_wrap()
        format_detail_border.set_font_size(9)
        format_detail_border.set_font_name('Times New Roman')
        formats['detail_border'] = format_detail_border
        
        format_detail_border_right = workbook.add_format({'bold': True, 'bottom':1})
        format_detail_border_right.set_align('right')
        format_detail_border_right.set_align('vcenter')
        format_detail_border_right.set_text_wrap()
        format_detail_border_right.set_font_size(9)
        format_detail_border_right.set_font_name('Times New Roman')
        formats['detail_border_right'] = format_detail_border_right
        
        format_header = workbook.add_format({'bold': True})
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_border(style=1)
        format_header.set_text_wrap()
        format_header.set_bg_color('#DCE6F1')
        format_header.set_font_size(10.5)
        format_header.set_font_name('Times New Roman')
        formats['header'] = format_header

        format_base = workbook.add_format()
        format_base.set_align('left')
        format_base.set_border(style=1)
        format_base.set_text_wrap()
        format_base.set_font_size(9)
        format_base.set_font_name('Times New Roman')
        formats['base'] = format_base
        
        format_base_right = workbook.add_format({'num_format':'0.00'})
        format_base_right.set_align('right')
        format_base_right.set_border(style=1)
        format_base_right.set_text_wrap()
        format_base_right.set_font_size(9)
        format_base_right.set_font_name('Times New Roman')
        formats['base_number'] = format_base_right
        
        red_base = workbook.add_format()
        red_base.set_font_color('red')
        red_base.set_align('left')
        red_base.set_text_wrap()
        red_base.set_font_size(11)
        red_base.set_font_name('Times New Roman')
        formats['red_base'] = red_base
        
        # Header
        row=0
        worksheet.merge_range(row, 0, row, 9, "REPORTE POR OT", formats['title'])
        row+=1
        worksheet.merge_range(row, 0, row, 4, f"ORDEN DE TRABAJO : {self.work_order_id.name}", formats['detail'])
        row+=10        
        row,sale_invoice_total=self.sale_invoiced_data(row,worksheet,formats)
        worksheet.merge_range(row, 4, row, 6, "Total Lineas de Ventas Facturadas", formats.get('detail'))
        worksheet.write(row, 9, sale_invoice_total, formats.get('detail'))        
        row+=2
        
        row,invoiced_expenses_total=self.invoiced_expense_data(row,worksheet,formats)
        worksheet.merge_range(row, 4, row, 6, "Total Lineas de Gastos Facturados", formats.get('detail'))
        worksheet.write(row, 9, invoiced_expenses_total, formats.get('detail'))        
        row+=2
        
        row,warehouse_item_total=self.warehouse_item_data(row,worksheet,formats)
        worksheet.merge_range(row, 4, row, 6, "Total Articulos de Almacen", formats.get('detail'))
        worksheet.write(row, 9, warehouse_item_total, formats.get('detail'))        
        row+=2
        
        row,total_hourly_cost=self.employees_hourly_cost(row,worksheet,formats)
        worksheet.write(row, 4, "Total Costo Parte de Horas", formats.get('detail'))
        worksheet.write(row, 5, total_hourly_cost, formats.get('detail'))      
        row+=2 
        
        # Header
        worksheet.merge_range(3, 6, 3, 8, "Total Lineas de Ventas Facturadas", formats.get('detail'))
        worksheet.write(3, 9, sale_invoice_total, formats['detail_right'])
        
        worksheet.merge_range(4, 6, 4, 8, "Total Lineas de Gastos Facturados", formats.get('detail'))
        worksheet.write(4, 9, invoiced_expenses_total,formats['detail_right'])
        
        worksheet.merge_range(5, 6, 5, 8, "Total Lineas de Kardex", formats.get('detail'))
        worksheet.write(5, 9, warehouse_item_total, formats['detail_right'])
        
        worksheet.merge_range(6, 6, 6, 8, "Total Costo Horas", formats.get('detail_border'))
        worksheet.write(6, 9, total_hourly_cost, formats['detail_border_right'])
        
        total_net=sum([
            sale_invoice_total,
            invoiced_expenses_total,
            warehouse_item_total,
            total_hourly_cost
        ])
        worksheet.merge_range(7, 6, 7, 8, "NETO", formats['detail'])
        worksheet.write(7, 9, total_net, formats['detail_right'])
        
        total_sale_percentage = round((abs(total_net)/(sale_invoice_total if sale_invoice_total else 1))*100,2)
        worksheet.merge_range(8, 6, 8, 8, "% NETO / VENTAS", formats.get('detail'))
        worksheet.write(8, 9, total_sale_percentage, formats['detail_right'])
        
        column_widths = [15,15,15,30,30,15,20,15,15,15,15]
        for i, width in enumerate(column_widths):
            column_label = xl_col_to_name(i)
            worksheet.set_column(f'{column_label}:{column_label}', width)
        workbook.close()
        f = open(filename, 'rb')
        return self.env['popup.it'].get_file(filename,base64.encodestring(b''.join(f.readlines())))
    
    def sale_invoiced_data(self, row, worksheet, formats):
        total_sale_invoice=0
        query= f"""
            SELECT 
                vst1.fecha,
                vst1.cuenta,
                aa.name as cuenta_name,
                vst1.partner,
                vst1.glosa,
                pp.default_code,
                pt.name,
                vst1.voucher,
                vst1.nro_comprobante,
                vst1.balance as soles,
                vst1.importe_me as dollars
            FROM 
                get_diariog(
                    '1999/02/13',
                    '{datetime.now().strftime('%Y/%m/%d')}',
                    {self.company_id.id}
                ) vst1
                LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                LEFT JOIN account_move am on am.id = aml.move_id
                LEFT JOIN product_product pp on pp.id = aml.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN account_account aa on aa.code = vst1.cuenta
            WHERE 
                vst1.cuenta LIKE '7%' AND
                aml.work_order_id  = {self.work_order_id.id} AND
                aa.company_id = {self.company_id.id} AND
                am.state = 'posted'
            ;
        """
        worksheet.merge_range(row, 0, row, 4, "Lineas de Ventas Facturadas" , formats.get('red_base'))
        row+=1
        header_list=[
            'FECHA',
            'CUENTA',
            'NOMBRE CUENTA',
            'PARTNER',
            'GLOSA',
            'COD. PRODUCTO',
            'PRODUCTO',
            'VOUCHER',
            'NRO. COMP.',
            'SOLES'
        ]
        for count,label in enumerate(header_list):
            worksheet.write(
                row,
                count,
                label,
                formats.get('header')
            )
        row+=1
        self.env.cr.execute(query)
        data_list = self.env.cr.dictfetchall()
        for data in data_list:
            amount_soles = (data['soles'] * -1)  if data['soles'] else 0
            worksheet.write(row, 0, data['fecha'].strftime("%d/%m/%Y") if data['fecha'] else '', formats.get('base'))
            worksheet.write(row, 1, data['cuenta'] if data['cuenta'] else '', formats.get('base'))
            worksheet.write(row, 2, data['cuenta_name'] if data['cuenta_name'] else '', formats.get('base'))
            worksheet.write(row, 3, data['partner'] if data['partner'] else '', formats.get('base'))
            worksheet.write(row, 4, data['glosa'] if data['glosa'] else '', formats.get('base'))
            worksheet.write(row, 5, data['default_code'] if data['default_code'] else '', formats.get('base'))
            worksheet.write(row, 6, data['name'] if data['name'] else '', formats.get('base'))
            worksheet.write(row, 7, data['voucher'] if data['voucher'] else '', formats.get('base'))
            worksheet.write(row, 8, data['nro_comprobante'] if data['nro_comprobante'] else '', formats.get('base'))
            worksheet.write(row, 9, amount_soles if amount_soles else '', formats.get('base_number'))
            # worksheet.write(row, 10, data['dollars'] if  data['dollars'] else '', formats.get('base'))
            total_sale_invoice += amount_soles
            row+=1
        return row,total_sale_invoice
    
    def invoiced_expense_data(self, row, worksheet, formats):
        total_invoiced_expenses=0
        query= f"""
            SELECT 
                vst1.fecha,
                vst1.cuenta,
                aa.name as cuenta_name,
                vst1.partner,
                vst1.glosa,
                pp.default_code,
                pt.name,
                vst1.voucher,
                vst1.nro_comprobante,
                vst1.balance as soles,
                vst1.importe_me as dollars
            FROM 
                get_diariog(
                    '1999/02/13',
                    '{datetime.now().strftime('%Y/%m/%d')}',
                    {self.company_id.id}
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
                aml.work_order_id  = {self.work_order_id.id} AND
                aa.company_id = {self.company_id.id} AND
                am.state = 'posted'
            ;
        """
        worksheet.merge_range(row, 0, row, 4, "Lineas de Gastos Facturados" , formats.get('red_base'))
        row+=1
        header_list=[
            'FECHA',
            'CUENTA',
            'NOMBRE CUENTA',
            'PARTNER',
            'GLOSA',
            'COD. PRODUCTO',
            'PRODUCTO',
            'VOUCHER',
            'NRO. COMP.',
            'SOLES'
        ]
        for count,label in enumerate(header_list):
            worksheet.write(
                row,
                count,
                label,
                formats.get('header')
            )
        row+=1
        self.env.cr.execute(query)
        data_list = self.env.cr.dictfetchall()
        for data in data_list:
            amount_soles = (data['soles'] * -1) if data['soles'] else 0
            worksheet.write(row, 0, data['fecha'].strftime("%d/%m/%Y") if data['fecha'] else '', formats.get('base'))
            worksheet.write(row, 1, data['cuenta'] if data['cuenta'] else '', formats.get('base'))
            worksheet.write(row, 2, data['cuenta_name'] if data['cuenta_name'] else '', formats.get('base'))
            worksheet.write(row, 3, data['partner'] if data['partner'] else '', formats.get('base'))
            worksheet.write(row, 4, data['glosa'] if data['glosa'] else '', formats.get('base'))
            worksheet.write(row, 5, data['default_code'] if data['default_code'] else '', formats.get('base'))
            worksheet.write(row, 6, data['name'] if data['name'] else '', formats.get('base'))
            worksheet.write(row, 7, data['voucher'] if data['voucher'] else '', formats.get('base'))
            worksheet.write(row, 8, data['nro_comprobante'] if data['nro_comprobante'] else '', formats.get('base'))
            worksheet.write(row, 9, amount_soles if amount_soles else '', formats.get('base_number'))
            # worksheet.write(row, 10, data['dollars'] if  data['dollars'] else '', formats.get('base'))
            total_invoiced_expenses+= amount_soles
            row+=1
        return row,total_invoiced_expenses
    
    def warehouse_item_data(self, row, worksheet, formats):
        warehouse_item_total=0
        query= f"""
            SELECT 
                total.fechax AS kardex_date,
                total.serial AS kardex_serial,
                total.nro AS kardex_nro,
                total.numdoc_cuadre AS kardex_doc,
                total.name AS kardex_partner,
                total.operation_type AS kardex_op,
                total.kardex_op_name as kardex_op_name,
                total.new_name AS kardex_product,
                total.default_code AS kardex_prod_cod,
                total.unidad AS kardex_unit,
                total.ingreso,
                total.salida,
                
                total.product_id,
                total.location_id,
                total.origen_usage,
                total.destino_usage,
                total.debit,
                total.credit,
                total.unit_price
                
            FROM 
                (SELECT 
                    vst_kardex_sunat.*,
                    vst_kardex_sunat.fecha - interval '5' hour as fechax,
                    np.new_name,
                    tok.name as kardex_op_name,
                    sl_o.usage as origen_usage , 
                    sl_d.usage as destino_usage,
                    sm.price_unit_it as unit_price
                
                FROM vst_kardex_fisico_valorado AS vst_kardex_sunat
                    LEFT JOIN stock_move sm ON sm.id = vst_kardex_sunat.stock_moveid
	                LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                    LEFT JOIN type_operation_kardex tok ON tok.id = sp.type_operation_sunat_id
                    LEFT JOIN stock_location sl_o ON sl_o.id = sm.location_id
					LEFT JOIN stock_location sl_d ON sl_d.id = sm.location_dest_id
                    LEFT JOIN (
                        SELECT 
                            t_pp.id, 
                            ((coalesce(max(it.value),max(t_pt.name::TEXT))::CHARACTER varying::TEXT || ' '::TEXT) || replace(array_agg(pav.name)::CHARACTER varying::TEXT, '{{NULL}}'::TEXT, ''::TEXT))::CHARACTER varying AS new_name
                        FROM 
                            product_product t_pp
                            JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
                            LEFT JOIN ir_translation it ON t_pt.id = it.res_id AND 
                                it.name = 'product.template,name' AND 
                                it.lang = 'es_PE' AND 
                                it.state = 'translated'
                            LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
                            LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
                            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
                        GROUP BY t_pp.id
                    ) np ON np.id = vst_kardex_sunat.product_id	
                WHERE 
                    (
                        vst_kardex_sunat.fecha
                        BETWEEN 
                            '1999/02/13' AND
                            '{datetime.now().strftime('%Y/%m/%d')}'
                    ) AND 
                    vst_kardex_sunat.company_id = {self.company_id.id} AND
                    sm.work_order_id  = {self.work_order_id.id} AND
                    vst_kardex_sunat.operation_type IN ('01','10','20','91','92')
                )Total	
        """
        worksheet.merge_range(row, 0, row, 4, "Articulos de Almacen" , formats.get('red_base'))
        row+=1
        header_list=[
            'FECHA',
            'T. OP.',
            'T. OP. (NOMBRE)',
            'PARTNER',
            'PRODUCTO',
            'COD. PRODUCTO',
            'DOC. ALMACEN',
            'CANT.',
            'COSTO ALBARAN',
            'COSTO TOTAL',
        ]
        for count,label in enumerate(header_list):
            worksheet.write(
                row,
                count,
                label,
                formats.get('header')
            )
        row+=1
        self.env.cr.execute(query)
        data_list = self.env.cr.dictfetchall()
        cprom_data={}
        for data in data_list:          
            # Fecha
            worksheet.write(row, 0, data['kardex_date'].strftime("%d/%m/%Y") if data['kardex_date'] else '', formats.get('base'))
            # T. OP.
            worksheet.write(row, 1, data['kardex_op'] if data['kardex_op'] else '', formats.get('base'))
            # T. OP.(nombre)
            worksheet.write(row, 2, data['kardex_op_name'] if data['kardex_op_name'] else '', formats.get('base'))
            # Partner
            worksheet.write(row, 3, data['kardex_partner'] if data['kardex_partner'] else '', formats.get('base'))
            # Producto
            worksheet.write(row, 4, data['kardex_product'] if data['kardex_product'] else '', formats.get('base'))
            # Cod Prod
            worksheet.write(row, 5, data['kardex_prod_cod'] if data['kardex_prod_cod'] else '', formats.get('base'))
            # Doc Almacen
            worksheet.write(row, 6, data['kardex_doc'] if data['kardex_doc'] else '', formats.get('base'))
            # Cantidad
            quantity = (data['ingreso'] if data['ingreso'] else 0) - (data['salida'] if data['salida'] else 0)
            quantity *= -1
            worksheet.write(row, 7, quantity, formats.get('base'))
            # Costo albaran
            unit_price=data['unit_price'] if data['unit_price'] else 0
            worksheet.write(row, 8, unit_price, formats.get('base'))
            # Costo Total
            total_cost=round(quantity * unit_price * -1,2)
            worksheet.write(row, 9, total_cost, formats.get('base_number'))
            warehouse_item_total += total_cost
            row+=1
        return row,warehouse_item_total
    
    def employees_hourly_cost(self, row, worksheet, formats):
        query = f"""
        SELECT
            date,
            he.name AS employee_id,
            pt.name  AS task_id,
            unit_amount,
            hourly_cost,
            total_cost_per_hour
        FROM 
            account_analytic_line AS aal
            LEFT JOIN project_task AS pt ON pt.id = aal.task_id
            LEFT JOIN hr_employee AS he ON he.id = aal.employee_id
        WHERE
            aal.project_id = {self.work_order_id.id} AND
            (
                aal.date 
                BETWEEN 
                    '1999/02/13' AND
                    '{datetime.now().strftime('%Y/%m/%d')}'
            )
        ;
        """
        worksheet.merge_range(row, 0, row, 4, "Costo parte de Horas" , formats.get('red_base'))
        row+=1
        header_list=[
            'FECHA',
            'EMPLEADO',
            'TAREA',
            'HORAS EMPLEADAS',
            'COSTO POR HORA',
            'COSTO TOTAL POR HORA',
        ]
        for count,label in enumerate(header_list):
            worksheet.write(
                row,
                count,
                label,
                formats.get('header')
            )
        row+=1
        
        total_hourly_cost=0
        self.env.cr.execute(query)
        data_list = self.env.cr.dictfetchall()
        for data in data_list:
            total_cost_per_hour = (data['total_cost_per_hour'] * -1) if data['total_cost_per_hour'] else 0
            worksheet.write(row, 0, data['date'].strftime("%d/%m/%Y") if data['date'] else '', formats.get('base'))
            worksheet.write(row, 1, data['employee_id'] if data['employee_id'] else '', formats.get('base'))
            worksheet.write(row, 2, data['task_id'] if data['task_id'] else '', formats.get('base'))
            worksheet.write(row, 3, data['unit_amount'] if data['unit_amount'] else 0, formats.get('base'))
            worksheet.write(row, 4, data['hourly_cost'] if data['hourly_cost'] else 0, formats.get('base'))
            worksheet.write(row, 5, total_cost_per_hour if total_cost_per_hour else '', formats.get('base_number'))
            total_hourly_cost+= total_cost_per_hour
            row+=1
        return row, total_hourly_cost