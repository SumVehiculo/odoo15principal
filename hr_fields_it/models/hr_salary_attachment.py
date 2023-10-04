# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
from dateutil.relativedelta import relativedelta

class HrSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment'

    _sql_constraints = [
        ('check_monthly_amount', 'check(1=1)', 'La cantidad mensual debe ser estrictamente positiva.'),
        ('check_total_amount', 'check(1=1)', 'El monto total debe ser estrictamente positivo y mayor o igual al monto mensual.'),
        ('check_remaining_amount', 'check(1=1)', 'La cantidad restante debe ser positiva.'),
        ('check_dates', 'check(1=1)', 'La fecha de finalización no puede ser anterior a la fecha de inicio.'),
    ]

    # employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    # company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    # currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    # description = fields.Char(required=True)
    deduction_type = fields.Selection(required=False, tracking=False)
    monthly_amount = fields.Monetary(required=False, tracking=False, help='Monto a pagar cada mes.')
    active_amount = fields.Monetary(compute='')
    total_amount = fields.Monetary(tracking=False, help='Monto total a pagar.')
    has_total_amount = fields.Boolean(compute='')
    paid_amount = fields.Monetary(tracking=False, help='Cantidad ya pagada.')
    remaining_amount = fields.Monetary(compute='', store=True, help='Importe restante a pagar.')
    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_estimated_end = fields.Date(compute='', help='Fecha de finalización aproximada.')
    date_end = fields.Date(tracking=False, help='Fecha en la que se ha dado por finalizada o cancelada esta cesión.')
    # state = fields.Selection(
    #     selection=[
    #         ('open', 'Running'),
    #         ('close', 'Completed'),
    #         ('cancel', 'Cancelled'),
    #     ],
    #     string='Status',
    #     default='open',
    #     required=True,
    #     tracking=True,
    #     copy=False,
    # )
    # payslip_ids = fields.Many2many('hr.payslip', relation='hr_payslip_hr_salary_attachment_rel', string='Payslips', copy=False)
    payslip_count = fields.Integer('# Payslips', compute='')

    # attachment = fields.Binary('Document', copy=False, tracking=True)
    # attachment_name = fields.Char()
    # has_similar_attachment = fields.Boolean(compute='_compute_has_similar_attachment')
    # has_similar_attachment_warning = fields.Char(compute='_compute_has_similar_attachment')

    enviado = fields.Boolean('Enviado', default=False)

    @api.model
    def create(self, vals):
        lead_res = super(HrSalaryAttachment, self).create(vals)
        for rec in lead_res:
            partner_ids = []
            if rec.employee_id.address_home_id:
                partner_ids.append(rec.employee_id.address_home_id.id)
            if partner_ids:
                # print("create partner_ids",partner_ids)
                rec.message_subscribe(partner_ids, None)
        return lead_res

    def write(self, vals):
        res = super(HrSalaryAttachment, self).write(vals)
        for rec in self:
            partner_ids = []
            if rec.employee_id.address_home_id:
                #message_unsubscribe
                message_partner_ids = rec.message_partner_ids.ids
                est_ids = [rec.employee_id.address_home_id.id] + [self.env.ref('base.partner_root').id]
                unsub_partners = set(message_partner_ids) - set(est_ids)
                if list(unsub_partners):
                    # print("write 1 partner_ids",unsub_partners)
                    rec.message_unsubscribe(list(unsub_partners))

                partner_ids.append(rec.employee_id.address_home_id.id)
                partner_ids.append(self.env.user.partner_id.id)
                rec.message_subscribe(partner_ids, None)
                # print("write 2 partner_ids",partner_ids)
        return res

    def action_invoice_sent(self):
        # res = {}
        self.ensure_one()
        Employee = self.employee_id
        data_record = self.attachment
        ir_values = {
            'name': '%s %s.pdf' % (self.description,Employee.name),
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'hr.salary.attachment',
        }
        # print("ir_values",ir_values)
        invoice_report_attachment_id = self.env['ir.attachment'].sudo().create(ir_values)
        if invoice_report_attachment_id:
            email_template = self.env.ref('hr_fields_it.email_template_hr_documentos')
            # print("self.employee_id.address_home_id.email",self.employee_id.address_home_id.email)
            if not self.employee_id.address_home_id.email:
                raise UserError(u'El contacto del empleado %s no tiene un correo establecido' % self.employee_id.name)
            else:
                email = self.employee_id.address_home_id.email
                # email = 'admin@example.com'
            if email_template and email:
                email_values = {
                    'email_to': email,
                    'email_cc': False,
                    'scheduled_date': False,
                    'recipient_ids': [],
                    'partner_ids': [],
                    'auto_delete': True,
                }
                email_template.attachment_ids = [(4, invoice_report_attachment_id.id)]
                # print("email_template",email_template)
                email_template.with_context(partner=self.employee_id.address_home_id, inv=self).send_mail(
                    self.id, email_values=email_values, force_send=True)
                email_template.attachment_ids = [(5, 0, 0)]

                body_html = """
                <div style="margin: 0px; padding: 0px;">
                    <h2 style="margin:0px 0 10px 0;font-size: 1.325rem;line-height:1.2;font-weight: 600;text-align:center;color:rgb(112,141,204);text-transform:uppercase;">
                        <b>
                            <font class="text-primary">
                                DOCUMENTO
                                <br />
                                {description}
                            </font>
                        </b>
                    </h2>
                    <hr align="left" size="1" width="100%" color="#e8e7e7" />
                    <p>Señor(es) : {employee_id},</p>
                    <br />
                    <p>Por la presente les comunicamos que la empresa {company}, le ha enviado el siguiente documento:</p>
                    <br />
                    <table>
                        <tbody>
                            <tr>
                                <td> Empleado </td>
                                <td> : </td>
                                <td> {employee_id} </td>
                            </tr>
                            <tr>
                                <td> DNI del Empleado </td>
                                <td> : </td>
                                <td> {dni} </td>
                            </tr>
                            <tr>
                                <td> Fecha</td>
                                <td> : </td>
                                <td> {date_start} </td>
                            </tr>

                        </tbody>
                    </table>
                </div>
                """.format( description = self.description,
                            employee_id = self.employee_id.name,
                            company = self.company_id.name,
                            dni = self.employee_id.identification_id,
                            date_start = self.date_start.strftime('%d-%m-%Y')
                            )
                self.message_post(body=body_html, attachment_ids=[invoice_report_attachment_id.id])
        return True

    def action_send_mass_mail(self):
        # today = fields.Date.context_today(self)
        issues = []
        for documento in self:
            # print("documento.attachment",documento.attachment)
            if not documento.enviado:
                if not documento.attachment:
                    raise UserError(u'Este Documento %s no tiene un adjunto' % documento.description)
                else:
                    try:
                        documento.action_invoice_sent()
                        documento.enviado = True
                        # print("mail_id",mail_id)
                    except:
                        issues.append(documento.employee_id.name)
            else:
                raise UserError(u'Este Documento %s ya ha sido enviado' % documento.description)

        if issues:
            return self.env['popup.it'].get_message('No se pudieron enviar los documentos de los siguientes Empleados: \n %s' % '\n'.join(issues))
        else:
            return self.env['popup.it'].get_message('Se enviaron todas los Documentos satisfactoriamente.')