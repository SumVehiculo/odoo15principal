# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HolidaysTypeIt(models.Model):
    _name = "hr.leave.type.it"
    _description = "Hr Holidays Type It"
    _order = 'sequence'

    name = fields.Char('Tipo de Ausencia', required=True)
    sequence = fields.Integer(default=100, help='El tipo con la secuencia más pequeña es el valor predeterminado en la ausencia')
    color = fields.Integer(string='Color', help="El color seleccionado aquí se utilizará en todas las pantallas con el tipo de tiempo libre.")
    icon_id = fields.Many2one('ir.attachment', string='Imagen de portada', domain="[('res_model', '=', 'hr.leave.type.it'), ('res_field', '=', 'icon_id')]")
    active = fields.Boolean('Active', default=True,
                            help="Si el campo activo se establece en falso, le permitirá ocultar el tipo de tiempo libre sin eliminarlo.")
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    responsible_id = fields.Many2one('res.users', 'Responsable de Aprobacion',
        domain=lambda self: [('groups_id', 'in', self.env.ref('hr_leave_it.group_hr_holidays_manager').id)])
    leave_validation_type = fields.Selection([
        ('no_validation', 'Sin Validacion'),
        ('hr', 'Por el encargado de Ausencias'),
        ('manager', "Por el aprobador de Empleados"),
        ('both', "Ambos")], default='hr', string='Tipo de Validacion')
    support_document = fields.Boolean(string='Cargar Documento de Sustento')

    suspension_type_id = fields.Many2one('hr.suspension.type',u'Tipo de Suspensión')
    ausencia_wd_id = fields.Many2one('hr.payslip.worked_days.type', string='WD Ausencia')