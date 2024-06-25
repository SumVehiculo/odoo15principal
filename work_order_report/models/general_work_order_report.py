from odoo import models, fields, api

class GeneralWorkOrderReport(models.Model):
    _name="general.work.order.report"
    _description="Reporte de Orden de Trabajo Ingresos-Gastos" 
    
    date = fields.Date('Fecha')
    account = fields.Char('Cuenta')
    account_label = fields.Char('Nombre Cuenta')
    partner = fields.Char('Partner')
    gloss = fields.Char('Glosa')
    product_reference = fields.Char('Cod. Producto')
    product_id = fields.Many2one('product.product', string='Producto')
    voucher = fields.Char('Voucher')
    voucher_number = fields.Char('Nro. Compr.')
    soles = fields.Float('Soles')
    work_order_id = fields.Many2one('project.project', string='O. T.')
    
    def get_report(self):
        self.env.cr.execute("DELETE FROM general_work_order_report")
        self.env.cr.execute("ALTER SEQUENCE public.general_work_order_report_id_seq RESTART WITH 1")
        self.generate_data()
        return self.env.ref('work_order_report.general_work_order_report_action').read()[0]
        
    def generate_data(self):
        query= f"""
            SELECT 
                vst1.fecha AS date,
                vst1.cuenta AS account,
                aa.name AS account_label,
                vst1.partner AS partner,
                vst1.glosa AS gloss,
                pp.default_code AS product_reference,
                aml.product_id AS product_id,
                vst1.voucher AS voucher,
                vst1.nro_comprobante AS voucher_number,
                vst1.balance AS soles,
                aml.work_order_id AS work_order_id
            FROM 
                get_diariog(
                    '2000/01/01',
                    '2124/12/31',
                    {self.env.company.id}
                ) vst1
                LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
                LEFT JOIN account_move am on am.id = aml.move_id
                LEFT JOIN product_product pp on pp.id = aml.product_id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                LEFT JOIN account_account aa on aa.code = vst1.cuenta
            WHERE 
                (
                    vst1.cuenta LIKE '7%' OR
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
            ;
        """
        self.env.cr.execute(query)
        data_list = self.env.cr.dictfetchall()
        for data in data_list:
            result={}
            result['date']=data['date']
            result['account']=data['account']
            result['account_label']=data['account_label']
            result['partner']=data['partner']
            result['gloss']=data['gloss']
            result['product_reference']=data['product_reference']
            result['product_id']=data['product_id']
            result['voucher']=data['voucher']
            result['voucher_number']=data['voucher_number']
            result['soles']=-1 * data['soles']
            result['work_order_id']=data['work_order_id']
            self.env['general.work.order.report'].create(result)