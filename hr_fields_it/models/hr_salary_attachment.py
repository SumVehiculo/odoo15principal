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

    enviado = fields.Boolean('Enviado', default=False, copy=False)

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

    def send_documento_by_email(self):
        issues = []
        for documento in self:
            if not documento.enviado:
                if not documento.attachment:
                    raise UserError(u'Este Documento %s no tiene un adjunto' % documento.description)
                else:

                    template_mail_id = self.env.ref('hr_fields_it.email_template_hr_documentos', False)
                    attachment_ids = []
                    Employee = documento.employee_id

                    attach = {
                        'name': '%s %s.pdf' % (documento.description,Employee.name),
                        'type': 'binary',
                        'datas': documento.attachment,
                        'store_fname': documento.attachment,
                        'mimetype': 'application/pdf',
                        'res_model': 'mail.compose.message',
                    }
                    # print("ir_values",ir_values)
                    attachment_id = self.env['ir.attachment'].sudo().create(attach)


                    # attach = {}
                    # attach['name'] = '%s %s.pdf' % (documento.description,Employee.name),
                    # attach['type'] = 'binary'
                    # attach['datas'] = documento.attachment
                    # attach['res_model'] = 'mail.compose.message'
                    # # print("attach", attach)
                    # attachment_id = self.env['ir.attachment'].sudo().create(attach)
                    attachment_ids.append(attachment_id.id)

                    try:
                        if documento.employee_id.work_email and documento.employee_id.address_home_id.email:
                            template_mail_id.send_mail(documento.id, force_send=True, email_values={'attachment_ids': attachment_ids})
                            # payslip.message_post_with_template(template_mail_id.id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow")
                            # payslip.message_post(body=body_html, attachment_ids=attachment_ids)
                            # payslip.enviado = True
                            documento.enviado = True
                    except:
                        issues.append(Employee.name)
            else:
                raise UserError(u'Este Documento %s ya ha sido enviado' % documento.description)
        if issues:
            return self.env['popup.it'].get_message('No se pudieron enviar los documentos de los siguientes Empleados: \n %s' % '\n'.join(issues))
        else:
            return self.env['popup.it'].get_message('Se enviaron todas los Documentos satisfactoriamente.')