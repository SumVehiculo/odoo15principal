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
    work_order_id = fields.Many2one('project.project', string='OT')
    start_date= fields.Date('Desde ')
    end_date = fields.Date('Hasta')
   
    def get_report(self):
        filename = "Reporte General OT.xlsx"
        workbook = Workbook(filename)
        worksheet = workbook.add_worksheet("Reporte OT")
        worksheet.set_tab_color('blue')
        # Header
        row=0
        row+=self.sale_invoiced_data(row,worksheet,workbook)
        
        column_widths = [15,15,15,30,30,15,20,15,15,15,15]
        for i, width in enumerate(column_widths):
            column_label = xl_col_to_name(i)
            worksheet.set_column(f'{column_label}:{column_label}', width)
        workbook.close()
        f = open(filename, 'rb')
        return self.env['popup.it'].get_file(filename,base64.encodestring(b''.join(f.readlines())))
    
    def sale_invoiced_data(self, row, worksheet, workbook):
        # Formats 
        format_header = workbook.add_format({'bold': True})
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_border(style=1)
        format_header.set_text_wrap()
        format_header.set_bg_color('#DCE6F1')
        format_header.set_font_size(15)
        format_header.set_font_name('Times New Roman')

        query= f"""
            SELECT 
                vst1.fecha,
                vst1.cuenta,
                aa.name,
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
                    {self.company_id}
                ) vst1
                LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                LEFT JOIN product_product pp on pp.id = aml.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN account_account aa on aa.code = vst1.cuenta
            WHERE 
                vst1.cuenta LIKE '7%';
        """
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
                format_header
            )
        row+=1
        self.env.cr.execute(query)
        data_list = self.env.cr.dictfetchall()
        for data in data_list:
            worksheet.write(row, 0, data['fecha'] if data['fecha'] else '', format_header)
            worksheet.write(row, 0, data['fecha'] if data['fecha'] else '', format_header)
            worksheet.write(row, 1, data['cuenta'] if data['cuenta'] else '', format_header)
            worksheet.write(row, 2, data['name'] if data['name'] else '', format_header)
            worksheet.write(row, 3, data['partner'] if data['partner'] else '', format_header)
            worksheet.write(row, 4, data['glosa'] if data['glosa'] else '', format_header)
            worksheet.write(row, 5, data['default_code'] if data['default_code'] else '', format_header)
            worksheet.write(row, 6, data['name'] if data['name'] else '', format_header)
            worksheet.write(row, 7, data['voucher'] if data['voucher'] else '', format_header)
            worksheet.write(row, 8, data['nro_comprobante'] if data['nro_comprobante'] else '', format_header)
            worksheet.write(row, 9, data['soles'] if data['soles'] else '', format_header)
            worksheet.write(row, 10, data['dollars'] if  data['dollars'] else '', format_header)
            row+=1
        return row
    
    def invoiced_expense_data(self,worksheet):
        pass
    
    def warehouse_item_date(self, worksheet):
        pass