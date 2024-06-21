import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from  xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_col_to_name


class WorkOrderReportWizard(models.TransientModel):
    _name="work.order.report.wizard"
    _description="Wizard Reporte Orden de Trabajo"
    
    company_id = fields.Many2one(
        'res.company', 
        string='Compañia',
        default= lambda self: self.env.company.id
    )
    work_order_id = fields.Many2one('project.project', string='OT', required=True)
    start_date= fields.Date('Desde', required=True)
    end_date = fields.Date('Hasta', required=True)
   
    def get_report(self):
        filename = "Reporte General OT.xlsx"
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
        
        red_base = workbook.add_format()
        red_base.set_font_color('red')
        red_base.set_align('left')
        red_base.set_text_wrap()
        red_base.set_font_size(11)
        red_base.set_font_name('Times New Roman')
        formats['red_base'] = red_base
        
        
        # Header
        row=0
        worksheet.merge_range(row, 0, row, 11, "REPORTE GENERAL OT", formats['title'])
        row+=1
        header_details=[
            f"ORDEN DE TRABAJO : {self.work_order_id.name}",
            f"DEL {self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')}"
        ]
        for detail in header_details:
            worksheet.merge_range(row, 0, row, 4, detail, formats['detail'])
            row+=1
        header_details=None
        row+=3
        row=self.sale_invoiced_data(row,worksheet,formats)
        row+=3
        row=self.invoiced_expense_data(row,worksheet,formats)
        row+=3
        row=self.warehouse_item_date(row,worksheet,formats)
        
        column_widths = [15,15,15,30,30,15,20,15,15,15,15]
        for i, width in enumerate(column_widths):
            column_label = xl_col_to_name(i)
            worksheet.set_column(f'{column_label}:{column_label}', width)
        workbook.close()
        f = open(filename, 'rb')
        return self.env['popup.it'].get_file(filename,base64.encodestring(b''.join(f.readlines())))
    
    def sale_invoiced_data(self, row, worksheet, formats):
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
                    '{self.start_date.strftime('%Y/%m/%d')}',
                    '{self.end_date.strftime('%Y/%m/%d')}',
                    {self.company_id.id}
                ) vst1
                LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                LEFT JOIN product_product pp on pp.id = aml.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN account_account aa on aa.code = vst1.cuenta
            WHERE 
                vst1.cuenta LIKE '7%' AND
                aml.work_order_id  = {self.work_order_id.id} AND
                aa.company_id = {self.company_id.id}
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
            'SOLES',
            'DÓLARES',
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
            worksheet.write(row, 0, data['fecha'].strftime("%d/%m/%Y") if data['fecha'] else '', formats.get('base'))
            worksheet.write(row, 1, data['cuenta'] if data['cuenta'] else '', formats.get('base'))
            worksheet.write(row, 2, data['cuenta_name'] if data['cuenta_name'] else '', formats.get('base'))
            worksheet.write(row, 3, data['partner'] if data['partner'] else '', formats.get('base'))
            worksheet.write(row, 4, data['glosa'] if data['glosa'] else '', formats.get('base'))
            worksheet.write(row, 5, data['default_code'] if data['default_code'] else '', formats.get('base'))
            worksheet.write(row, 6, data['name'] if data['name'] else '', formats.get('base'))
            worksheet.write(row, 7, data['voucher'] if data['voucher'] else '', formats.get('base'))
            worksheet.write(row, 8, data['nro_comprobante'] if data['nro_comprobante'] else '', formats.get('base'))
            worksheet.write(row, 9, data['soles'] if data['soles'] else '', formats.get('base'))
            worksheet.write(row, 10, data['dollars'] if  data['dollars'] else '', formats.get('base'))
            row+=1
        return row
    
    def invoiced_expense_data(self, row, worksheet, formats):
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
                    '{self.start_date.strftime('%Y/%m/%d')}',
                    '{self.end_date.strftime('%Y/%m/%d')}',
                    {self.company_id.id}
                ) vst1
                LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                LEFT JOIN product_product pp on pp.id = aml.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN account_account aa on aa.code = vst1.cuenta
            WHERE 
                vst1.cuenta SIMILAR TO '62% | 63% | 64% | 65% | 67%' AND
                aml.work_order_id  = {self.work_order_id.id} AND
                aa.company_id = {self.company_id.id}
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
            'SOLES',
            'DÓLARES',
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
            worksheet.write(row, 0, data['fecha'].strftime("%d/%m/%Y") if data['fecha'] else '', formats.get('base'))
            worksheet.write(row, 1, data['cuenta'] if data['cuenta'] else '', formats.get('base'))
            worksheet.write(row, 2, data['cuenta_name'] if data['cuenta_name'] else '', formats.get('base'))
            worksheet.write(row, 3, data['partner'] if data['partner'] else '', formats.get('base'))
            worksheet.write(row, 4, data['glosa'] if data['glosa'] else '', formats.get('base'))
            worksheet.write(row, 5, data['default_code'] if data['default_code'] else '', formats.get('base'))
            worksheet.write(row, 6, data['name'] if data['name'] else '', formats.get('base'))
            worksheet.write(row, 7, data['voucher'] if data['voucher'] else '', formats.get('base'))
            worksheet.write(row, 8, data['nro_comprobante'] if data['nro_comprobante'] else '', formats.get('base'))
            worksheet.write(row, 9, data['soles'] if data['soles'] else '', formats.get('base'))
            worksheet.write(row, 10, data['dollars'] if  data['dollars'] else '', formats.get('base'))
            row+=1
        return row
    
    def warehouse_item_date(self, row, worksheet, formats):
        query= f"""
            SELECT 
                fechax AS kardex_date,
                serial AS kardex_serial,
                nro AS kardex_nro,
                numdoc_cuadre AS kardex_doc,
                name AS kardex_partner,
                operation_type AS kardex_op,
                new_name AS kardex_product,
                default_code AS kardex_prod_cod,
                unidad AS kardex_unit,
                ingreso AS kardex_income,
                salida AS kardex_release
            FROM 
                (SELECT 
                    vst_kardex_sunat.*,
                    vst_kardex_sunat.fecha - interval '5' hour as fechax,
                    np.new_name
                FROM vst_kardex_fisico_valorado AS vst_kardex_sunat
                    LEFT JOIN stock_move sm ON sm.id = vst_kardex_sunat.stock_moveid
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
                        fecha_num((vst_kardex_sunat.fecha - interval '5' HOUR)::DATE) 
                        BETWEEN 
                            {self.start_date.strftime('%Y%m%d')} AND 
                            {self.end_date.strftime('%Y%m%d')}
                    ) AND 
                    vst_kardex_sunat.company_id = {self.company_id.id} AND
                    sm.work_order_id  = {self.work_order_id.id}
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
            'COSTO UNIT. SOLES',
            'SOLES',
            'DÓLARES',
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
            worksheet.write(row, 0, data['kardex_date'] if data['kardex_date'] else '', formats.get('base'))
            worksheet.write(row, 1, data['kardex_serial'] if data['kardex_serial'] else '', formats.get('base'))
            worksheet.write(row, 2, data['kardex_nro'] if data['kardex_nro'] else '', formats.get('base'))
            worksheet.write(row, 3, data['kardex_doc'] if data['kardex_doc'] else '', formats.get('base'))
            worksheet.write(row, 4, data['kardex_partner'] if data['kardex_partner'] else '', formats.get('base'))
            worksheet.write(row, 5, data['kardex_op'] if data['kardex_op'] else '', formats.get('base'))
            worksheet.write(row, 6, data['kardex_product'] if data['kardex_product'] else '', formats.get('base'))
            worksheet.write(row, 7, data['kardex_prod_cod'] if data['kardex_prod_cod'] else '', formats.get('base'))
            worksheet.write(row, 8, data['kardex_unit'] if data['kardex_unit'] else '', formats.get('base'))
            worksheet.write(row, 9, data['kardex_income'] if data['kardex_income'] else '', formats.get('base'))
            worksheet.write(row, 10, data['kardex_release'] if data['kardex_release'] else '', formats.get('base'))
            row+=1
        return row