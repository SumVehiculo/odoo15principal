# -*- coding: utf-8 -*-
import logging
from collections import namedtuple, defaultdict
from datetime import datetime, timedelta, time
from pytz import timezone, UTC
from odoo import api, fields, models, tools
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')

class hr_work_suspension(models.Model):
    _inherit='hr.work.suspension'

    leave_id = fields.Many2one('hr.leave.it','Ausencia')

class hr_accrual_vacation(models.Model):
    _inherit='hr.accrual.vacation'

    leave_id = fields.Many2one('hr.leave.it','Ausencia')

class HrLeaveIt(models.Model):
    _name = "hr.leave.it"
    _description = "Time Off"
    _order = "date_from desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields_list):
        defaults = super(HrLeaveIt, self).default_get(fields_list)
        defaults = self._default_get_request_parameters(defaults)
        parameters = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        LeaveType = self.env['hr.leave.type.it'].search([('active', '=', True),('suspension_type_id', '=', parameters.suspension_type_id.id)], limit=1)
        # print("LeaveType",LeaveType.name)
        defaults['leave_type_id'] = LeaveType.id if LeaveType else defaults.get('leave_type_id')
        # defaults['work_suspension_id'] = parameters.suspension_type_id.id
        return defaults

    def _default_get_request_parameters(self, values):
        new_values = dict(values)
        global_from, global_to = False, False
        if values.get('date_from'):
            user_tz = self.env.user.tz or 'UTC'
            localized_dt = timezone('UTC').localize(values['date_from']).astimezone(timezone(user_tz))
            global_from = localized_dt.time().hour == 7 and localized_dt.time().minute == 0
            new_values['request_date_from'] = localized_dt.date()
        if values.get('date_to'):
            user_tz = self.env.user.tz or 'UTC'
            localized_dt = timezone('UTC').localize(values['date_to']).astimezone(timezone(user_tz))
            global_to = localized_dt.time().hour == 19 and localized_dt.time().minute == 0
            new_values['request_date_to'] = localized_dt.date()
        return new_values

    name = fields.Char('Descripcion')
    state = fields.Selection([
        ('draft', 'Por Enviar'),
        ('confirm', 'Por Aprobar'),
        ('refuse', 'Rechazado'),
        ('validate1', 'Segunda Aprobacion'),
        ('validate', 'Aprobado')
        ], string='Estados', compute='_compute_state', store=True, tracking=True, copy=False, readonly=False,
        help="El estado se establece en 'Por Enviar', cuando se crea una solicitud de Ausencia." +
        "\nEl estado es 'Por Aprobar', cuando el usuario confirma la solicitud de Ausencia." +
        "\nEl estado es 'Rechazado', cuando el gerente rechaza la solicitud de Ausencia." +
        "\nEl estado es 'Aprobado', cuando el gerente aprueba la solicitud de Ausencia.")
    user_id = fields.Many2one('res.users', string='Usuario', related='employee_id.user_id', related_sudo=True, compute_sudo=True, store=True, readonly=True)
    leave_type_id = fields.Many2one("hr.leave.type.it", string="Tipo de Ausencia", required=True, readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    color = fields.Integer("Color", related='leave_type_id.color')
    validation_type = fields.Selection(string='Tipo de Validacion', related='leave_type_id.leave_validation_type', readonly=False)
    employee_id = fields.Many2one('hr.employee', string='Empleado', index=True, readonly=False, ondelete="restrict",
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]},
        tracking=True)
    active_employee = fields.Boolean(related='employee_id.active', readonly=True)
    tz_mismatch = fields.Boolean(compute='_compute_tz_mismatch')
    tz = fields.Selection(_tz_get, compute='_compute_tz')
    department_id = fields.Many2one('hr.department', compute='_compute_department_id', store=True, string='Departamento', readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    date_from = fields.Datetime(
        'Fecha Desde', compute='_compute_date_from_to', store=True, readonly=False, index=True, copy=False, required=True, tracking=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    date_to = fields.Datetime(
        'Fecha Hasta', compute='_compute_date_from_to', store=True, readonly=False, copy=False, required=True, tracking=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    number_of_days = fields.Float('Duracion (Dias)', compute='_compute_number_of_days', store=True, readonly=False, copy=False, tracking=True,
        help='Número de días de la solicitud de Ausencia. Utilizado en el cálculo. Para corregir manualmente la duración, utilice este campo.')
    first_approver_id = fields.Many2one('hr.employee', string='Primer Aprobador', readonly=True, copy=False,
        help='Esta área es rellenada automáticamente por el usuario que valida la ausencia')
    second_approver_id = fields.Many2one('hr.employee', string='Segundo Aprobador', readonly=True, copy=False,
        help='Esta área es rellenada automáticamente por el usuario que valida la ausencia (si el tipo de ausencia necesita una segunda aprobacion)')
    can_reset = fields.Boolean('Puede restablecer', compute='_compute_can_reset')
    can_approve = fields.Boolean('Puede aprobar', compute='_compute_can_approve')

    attachment_ids = fields.One2many('ir.attachment', 'res_id', string="Attachments")
    supported_attachment_ids = fields.Many2many('ir.attachment', string="Adjuntar Archivo", compute='_compute_supported_attachment_ids',
        inverse='_inverse_supported_attachment_ids')
    supported_attachment_ids_count = fields.Integer(compute='_compute_supported_attachment_ids')
    leave_type_support_document = fields.Boolean(related="leave_type_id.support_document")
    request_date_from = fields.Date('Request Start Date')
    request_date_to = fields.Date('Request End Date')
    is_hatched = fields.Boolean('Hatched', compute='_compute_is_hatched')
    is_striked = fields.Boolean('Striked', compute='_compute_is_hatched')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    contract_id = fields.Many2one('hr.contract','Contrato')
    payslip_run_id = fields.Many2one('hr.payslip.run','Planilla')
    work_suspension_id = fields.Many2one('hr.suspension.type',related='leave_type_id.suspension_type_id',string=u'Tipo de Suspensión', store=True)
    payslip_status = fields.Boolean('Enviado a Planillas', copy=False, default= False)

    _sql_constraints = [
        ('date_check2', "CHECK ((date_from <= date_to))", "La fecha de inicio debe ser anterior a la fecha de finalización."),
        ('duration_check', "CHECK ( number_of_days >= 0 )", "Si desea cambiar la cantidad de días, debe usar el 'período'"),
    ]

    @api.onchange('leave_type_id', 'number_of_days')
    def verify_name(self):
        self.name = '%s: %s dias' % (
        (self.leave_type_id.name or '').strip(), (str(self.number_of_days) or '').strip())

    def _get_number_of_days(self, date_from, date_to, employee_id):
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            return {'days': (date_to-date_from).days+1, 'hours': 0}
        return {'days': (date_to-date_from).days+1, 'hours': 0}

    @api.onchange('contract_id')
    def onchange_contract(self):
        if self.contract_id.id:
            self.employee_id = self.contract_id.employee_id.id
            self.department_id = self.contract_id.employee_id.department_id.id
        else:
            self.employee_id = None
            self.department_id = None

    def action_refuse(self):
        l = self.contract_id.work_suspension_ids.filtered(lambda reg: reg.leave_id.id == self.id)
        h = self.env['hr.accrual.vacation'].search([('leave_id','=',self.id)])
        if self.payslip_status or len(l)>0 or len(h)>0:
            # raise UserError(u'No se puede rechazar si ya se encuentra en reportado en planilla')
            self.payslip_status = False
            l.unlink()
            h.unlink()
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['draft', 'confirm', 'validate', 'validate1'] for holiday in self):
            raise UserError(_('La solicitud de ausencia debe ser confirmada o validada para poder rechazarla.'))

        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # Post a second message, more verbose than the tracking message
        for holiday in self:
            if holiday.employee_id.user_id:
                holiday.message_post(
                    body=_('Su %(leave_type)s solicitado el %(date)s ha sido rechazado', leave_type=holiday.leave_type_id.name, date=holiday.date_from),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids)
        self.activity_update()
        return True

    def action_approve(self):
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('La solicitud de ausencia debe ser confirmada ("Por aprobar") para poder aprobarla.'))

        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        valida1 = False
        valida2 = False
        first_validators=[]
        second_validators=[]
        res=False
        for l in MainParameter.validator_ids:
            if self.env.user.id == l.user_id.id:
                if l.first_validate:
                    valida1=l.first_validate
                if l.second_validate:
                    valida2=l.second_validate
            if l.first_validate:
                first_validators.append(l.user_id.id)
            if l.second_validate:
                second_validators.append(l.user_id.id)
        if not valida1:
            raise UserError(u'No tiene permiso para realizar esta operación')
        else:
            if self.env.user.id in first_validators:
                current_employee = self.env.user.employee_id
                self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
            else:
                raise UserError(u'No tiene permiso para realizar esta operación')

        # Publique un segundo mensaje, más detallado que el mensaje de seguimiento
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.message_post(
                body=_(
                    'Su  %(leave_type)s planeado el %(date)s ha sido aceptado',
                    leave_type=holiday.leave_type_id.name,
                    date=holiday.date_from
                ),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        return True

    def action_validate(self):
        current_employee = self.env.user.employee_id
        leaves = self._get_leaves_on_public_holiday()
        if leaves:
            raise ValidationError(_('Se supone que los siguientes empleados no deben trabajar durante ese período:\n %s') % ','.join(leaves.mapped('employee_id.name')))
        if any(holiday.state not in ['confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday in self):
            raise UserError(_('La solicitud de ausencia debe ser confirmada para poder aprobarla.'))
        self.write({'state': 'validate'})
        leaves_second_approver = self.env['hr.leave.it']
        leaves_first_approver = self.env['hr.leave.it']

        for leave in self:
            if leave.validation_type == 'both':
                leaves_second_approver += leave
            else:
                leaves_first_approver += leave
        leaves_second_approver.write({'second_approver_id': current_employee.id})
        leaves_first_approver.write({'first_approver_id': current_employee.id})
        return True

    def _get_leaves_on_public_holiday(self):
        return self.filtered(lambda l: l.employee_id and not l.number_of_days)

    # envio de data a nomina central
    def prepare_suspension_data(self,contract_id):
        vals = {
            'suspension_type_id': self.work_suspension_id.id,
            'reason': self.leave_type_id.ausencia_wd_id.name,
            'days': self.number_of_days,
            'payslip_run_id': self.payslip_run_id.id,
            'leave_id': self.id,
            'contract_id': contract_id.id,
        }
        return vals

    def prepare_payslip_data(self,slip):
        vals={
            'days':self.number_of_days,
            'accrued_period':self.payslip_run_id.id,
            'motive':self.leave_type_id.name,
            'date_aplication':self.request_date_from,
            'request_date_from':self.request_date_from,
            'request_date_to':self.request_date_to,
            'leave_id':self.id,
            'slip_id':slip.id,
        }
        return vals

    def send_data_to_payslip(self):
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        for l in self:
            if not l.payslip_run_id:
                raise UserError(u'La ausencia %s de %s no tiene asignada una planilla Mensual' % (l.name, l.employee_id.name))
            if l.payslip_status == False:
                if l.state=='validate':
                    slip = self.env['hr.payslip'].search([('payslip_run_id','=',l.payslip_run_id.id),('employee_id','=',l.employee_id.id)])
                    if len(slip)==0:
                        raise UserError(u'El empleado %s no existe en la Planilla de %s' % (l.employee_id.name,l.payslip_run_id.name.name))
                    if l.work_suspension_id:
                        vals = l.prepare_suspension_data(slip.contract_id)
                        # print("vals",vals)
                        self.env['hr.work.suspension'].create(vals)

                    if l.work_suspension_id.id == MainParameter.suspension_type_id.id:
                        vals=l.prepare_payslip_data(slip)
                        # print(vals)
                        self.env['hr.accrual.vacation'].create(vals)

                        if l.leave_type_id.ausencia_wd_id:
                            total_dias_vaca = self.env['hr.accrual.vacation'].search([('slip_id', '=', slip.id)]).mapped('days')
                            total_dias_dm = self.env['hr.work.suspension'].search([('payslip_run_id', '=', l.payslip_run_id.id),('contract_id', '=',l.contract_id.id),('suspension_type_id', '=',MainParameter.suspension_dm_type_id.id)]).mapped('days')
                            # print("total_dias_vaca",sum(total_dias_vaca))

                            vaca_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.vacations_wd_id)
                            dm_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.medico_wd_id)
                            dia_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
                            # print(vaca_line)
                            vaca_line.number_of_days = sum(total_dias_vaca)
                            dm_line.number_of_days = sum(total_dias_dm)
                            dia_line.number_of_days = 30-sum(total_dias_vaca)-sum(total_dias_dm)

                    elif l.work_suspension_id.id == MainParameter.suspension_dm_type_id.id:
                        total_dias_vaca = self.env['hr.accrual.vacation'].search([('slip_id', '=', slip.id)]).mapped('days')
                        total_dias_dm = self.env['hr.work.suspension'].search([('payslip_run_id', '=', l.payslip_run_id.id),('contract_id', '=',l.contract_id.id),('suspension_type_id', '=',MainParameter.suspension_dm_type_id.id)]).mapped('days')
                        # print("total_dias_dm",total_dias_dm)

                        vaca_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.vacations_wd_id)
                        dm_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.medico_wd_id)
                        dia_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
                        # print(vaca_line)
                        vaca_line.number_of_days = sum(total_dias_vaca)
                        dm_line.number_of_days = sum(total_dias_dm)
                        dia_line.number_of_days = 30-sum(total_dias_vaca)-sum(total_dias_dm)
                    elif not l.work_suspension_id.id:
                        vals=l.prepare_payslip_data(slip)
                        # print(vals)
                        self.env['hr.accrual.vacation'].create(vals)
                        wd_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == l.leave_type_id.ausencia_wd_id)
                        wd_line.number_of_days = l.number_of_days
                    else:
                        DIAS_FAL = slip.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code')).mapped('code')
                        dia_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
                        wd_line = slip.worked_days_line_ids.filtered(lambda line: line.wd_type_id == l.leave_type_id.ausencia_wd_id)
                        if wd_line.code in tuple(DIAS_FAL):
                            wd_line.number_of_days = wd_line.number_of_days + l.number_of_days
                        else:
                            wd_line.number_of_days = l.number_of_days
                            dia_line.number_of_days = 30 - l.number_of_days
                    l.payslip_status = True
                else:
                    raise UserError(u'Para reportar a la planilla, primero debe de confirmar esta ausencia: %s de %s.' % (l.name, l.employee_id.name))
            else:
                raise UserError(u'La ausencia %s de %s ya fue enviada a la planilla Mensual' % (l.name, l.employee_id.name))
        return self.env['popup.it'].get_message(u'Se mandó al Lote de Nóminas exitosamente.')

    # metodos nativos
    def _auto_init(self):
        res = super(HrLeaveIt, self)._auto_init()
        tools.create_index(self._cr, 'hr_leave_date_to_date_from_index',
                           self._table, ['date_to', 'date_from'])
        return res

    @api.depends('leave_type_id')
    def _compute_state(self):
        for leave in self:
            leave.state = 'confirm' if leave.validation_type != 'no_validation' else 'draft'

    @api.depends('request_date_from', 'request_date_to', 'employee_id')
    def _compute_date_from_to(self):
        for holiday in self:
            if holiday.request_date_from and holiday.request_date_to and holiday.request_date_from > holiday.request_date_to:
                holiday.request_date_to = holiday.request_date_from
            if not holiday.request_date_from:
                holiday.date_from = False
            else:
                resource_calendar_id = holiday.employee_id.resource_calendar_id or self.env.company.resource_calendar_id
                domain = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
                attendances = self.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'week_type', 'dayofweek', 'day_period'], ['week_type', 'dayofweek', 'day_period'], lazy=False)

                # Must be sorted by dayofweek ASC and day_period DESC
                attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'], group['week_type']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))
                default_value = DummyAttendance(0, 0, 0, 'morning', False)

                if resource_calendar_id.two_weeks_calendar:
                    # find week type of start_date
                    start_week_type = self.env['resource.calendar.attendance'].get_week_type(holiday.request_date_from)
                    attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == start_week_type]
                    attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != start_week_type]
                    # First, add days of actual week coming after date_from
                    attendance_filtred = [att for att in attendance_actual_week if int(att.dayofweek) >= holiday.request_date_from.weekday()]
                    # Second, add days of the other type of week
                    attendance_filtred += list(attendance_actual_next_week)
                    # Third, add days of actual week (to consider days that we have remove first because they coming before date_from)
                    attendance_filtred += list(attendance_actual_week)
                    end_week_type = self.env['resource.calendar.attendance'].get_week_type(holiday.request_date_to)
                    attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == end_week_type]
                    attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != end_week_type]
                    attendance_filtred_reversed = list(reversed([att for att in attendance_actual_week if int(att.dayofweek) <= holiday.request_date_to.weekday()]))
                    attendance_filtred_reversed += list(reversed(attendance_actual_next_week))
                    attendance_filtred_reversed += list(reversed(attendance_actual_week))

                    # find first attendance coming after first_day
                    attendance_from = attendance_filtred[0]
                    # find last attendance coming before last_day
                    attendance_to = attendance_filtred_reversed[0]
                else:
                    # find first attendance coming after first_day
                    attendance_from = next((att for att in attendances if int(att.dayofweek) >= holiday.request_date_from.weekday()), attendances[0] if attendances else default_value)
                    # find last attendance coming before last_day
                    attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= holiday.request_date_to.weekday()), attendances[-1] if attendances else default_value)

                compensated_request_date_from = holiday.request_date_from
                compensated_request_date_to = holiday.request_date_to

                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)
                holiday.date_from = timezone(holiday.tz).localize(datetime.combine(compensated_request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
                holiday.date_to = timezone(holiday.tz).localize(datetime.combine(compensated_request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)

    @api.depends('employee_id')
    def _compute_department_id(self):
        for holiday in self:
            if holiday.employee_id:
                holiday.department_id = holiday.employee_id.department_id
            else:
                holiday.department_id = False

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to:
                holiday.number_of_days = holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
            else:
                holiday.number_of_days = 0

    @api.depends('tz')
    @api.depends_context('uid')
    def _compute_tz_mismatch(self):
        for leave in self:
            leave.tz_mismatch = leave.tz != self.env.user.tz

    @api.depends('employee_id')
    def _compute_tz(self):
        for leave in self:
            tz = False
            leave.tz = tz or self.env.company.resource_calendar_id.tz or self.env.user.tz or 'UTC'

    def _get_calendar(self):
        self.ensure_one()
        return self.employee_id.resource_calendar_id or self.env.company.resource_calendar_id

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_reset(self):
        for holiday in self:
            try:
                holiday._check_approval_update('draft')
            except (AccessError, UserError):
                holiday.can_reset = False
            else:
                holiday.can_reset = True

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        for holiday in self:
            try:
                if holiday.state == 'confirm' and holiday.validation_type == 'both':
                    holiday._check_approval_update('validate1')
                else:
                    holiday._check_approval_update('validate')
            except (AccessError, UserError):
                holiday.can_approve = False
            else:
                holiday.can_approve = True

    @api.depends('state')
    def _compute_is_hatched(self):
        for holiday in self:
            holiday.is_striked = holiday.state == 'refuse'
            holiday.is_hatched = holiday.state not in ['refuse', 'validate']

    @api.depends('leave_type_support_document', 'attachment_ids')
    def _compute_supported_attachment_ids(self):
        for holiday in self:
            holiday.supported_attachment_ids = holiday.attachment_ids
            holiday.supported_attachment_ids_count = len(holiday.attachment_ids.ids)

    def _inverse_supported_attachment_ids(self):
        for holiday in self:
            holiday.supported_attachment_ids.write({
                'res_id': holiday.id,
            })

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date(self):
        if self.env.context.get('leave_skip_date_check', False):
            return
        for holiday in self.filtered('employee_id'):
            domain = [
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_('No puede asignar 2 ausencias que se superponen en el mismo día para el mismo empleado.'))

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date_state(self):
        if self.env.context.get('leave_skip_state_check'):
            return
        for holiday in self:
            if holiday.state in ['cancel', 'refuse', 'validate1', 'validate']:
                raise ValidationError(_("Esta modificación no está permitida en el estado actual."))

    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        if employee.user_id:
            self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)

    def _check_double_validation_rules(self, employees, state):
        if self.user_has_groups('hr_leave_it.group_hr_holidays_manager'):
            return
        is_leave_user = self.user_has_groups('hr_leave_it.group_hr_holidays_manager')
        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
            if employees and not is_leave_user:
                raise AccessError(_('No puedes hacer la Primera Aprobacion de %s, porque no eres administrador de ausencias', employees[0].name))
        elif state == 'validate' and not is_leave_user:
            raise AccessError(_('No tiene derecho a aplicar una segunda aprobación en una solicitud de ausenciae'))

    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        if not self._context.get('leave_fast_create'):
            leave_types = self.env['hr.leave.type.it'].browse([values.get('leave_type_id') for values in vals_list if values.get('leave_type_id')])
            mapped_validation_type = {leave_type.id: leave_type.leave_validation_type for leave_type in leave_types}

            for values in vals_list:
                employee_id = values.get('employee_id', False)
                leave_type_id = values.get('leave_type_id')
                # Handle automatic department_id
                if not values.get('department_id'):
                    values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})

                # Handle no_validation
                if mapped_validation_type[leave_type_id] == 'no_validation':
                    values.update({'state': 'confirm'})

                if 'state' not in values:
                    # To mimic the behavior of compute_state that was always triggered, as the field was readonly
                    values['state'] = 'confirm' if mapped_validation_type[leave_type_id] != 'no_validation' else 'draft'

                # Handle double validation
                if mapped_validation_type[leave_type_id] == 'both':
                    self._check_double_validation_rules(employee_id, values.get('state', False))

        holidays = super(HrLeaveIt, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

        for holiday in holidays:
            if not self._context.get('leave_fast_create'):
                holiday_sudo = holiday.sudo()
                holiday_sudo.add_follower(employee_id)
                if holiday.validation_type == 'manager':
                    holiday_sudo.message_subscribe(partner_ids=holiday.employee_id.leave_manager_id.partner_id.ids)
                if holiday.validation_type == 'no_validation':
                    # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
                    holiday_sudo.action_validate()
                    holiday_sudo.message_subscribe(partner_ids=[holiday._get_responsible_for_approval().partner_id.id])
                    holiday_sudo.message_post(body=_("The time off has been automatically approved"), subtype_xmlid="mail.mt_comment") # Message from OdooBot (sudo)
                elif not self._context.get('import_file'):
                    holiday_sudo.activity_update()
        return holidays

    def write(self, values):
        is_officer = self.env.user.has_group('hr_leave_it.group_hr_holidays_manager') or self.env.is_superuser()
        if not is_officer and values.keys() - {'supported_attachment_ids', 'message_main_attachment_id'}:
            if any(hol.date_from.date() < fields.Date.today() and hol.employee_id.leave_manager_id != self.env.user for hol in self):
                raise UserError(_('You must have manager rights to modify/validate a time off that already begun'))

        employee_id = values.get('employee_id', False)
        if not self.env.context.get('leave_fast_create'):
            if values.get('state'):
                self._check_approval_update(values['state'])
                if any(holiday.validation_type == 'both' for holiday in self):
                    if values.get('employee_id'):
                        employees = self.env['hr.employee'].browse(values.get('employee_id'))
                    else:
                        employees = self.mapped('employee_id')
                    self._check_double_validation_rules(employees, values['state'])
            if 'date_from' in values:
                values['request_date_from'] = values['date_from']
            if 'date_to' in values:
                values['request_date_to'] = values['date_to']
        result = super(HrLeaveIt, self).write(values)
        if not self.env.context.get('leave_fast_create'):
            for holiday in self:
                if employee_id:
                    holiday.add_follower(employee_id)
        return result

    @api.ondelete(at_uninstall=False)
    def _unlink_if_correct_states(self):
        error_message = _('You cannot delete a time off which is in %s state')
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        now = fields.Datetime.now()

        if not self.user_has_groups('hr_leave_it.group_hr_holidays_manager'):
            if any(hol.state not in ['draft', 'confirm'] for hol in self):
                raise UserError(error_message % state_description_values.get(self[:1].state))
            if any(hol.date_from < now for hol in self):
                raise UserError(_('No puede eliminar una ausencia que está en el pasado'))
        else:
            for holiday in self.filtered(lambda holiday: holiday.state not in ['draft', 'cancel', 'confirm']):
                raise UserError(error_message % (state_description_values.get(holiday.state),))

    def unlink(self):
        return super(HrLeaveIt, self.with_context(leave_skip_date_check=True)).unlink()

    def copy_data(self, default=None):
        if default and 'date_from' in default and 'date_to' in default:
            default['request_date_from'] = default.get('date_from')
            default['request_date_to'] = default.get('date_to')
            return super().copy_data(default)
        raise UserError(_('Una ausencia no se puede duplicar.'))

    ####################################################
    # Business methods
    ####################################################

    def _remove_resource_leave(self):
        """ This method will create entry in resource calendar time off object at the time of holidays cancel/removed """
        return self.env['resource.calendar.leaves'].search([('holiday_id', 'in', self.ids)]).unlink()

    def action_draft(self):
        if any(holiday.state not in ['confirm', 'refuse'] for holiday in self):
            raise UserError(_('El estado de la solicitud de ausencia debe ser "Rechazado" o "Por aprobar" para que se restablezca como borrador.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })
        self.activity_update()
        return True

    def action_confirm(self):
        for rec in self:
            if rec.filtered(lambda holiday: holiday.state != 'draft'):
                raise UserError(_('La solicitud de Ausencia debe estar en estado Borrador, para poder confirmarla.'))
            rec.write({'state': 'confirm'})
            holidays = rec.filtered(lambda leave: leave.validation_type == 'no_validation')
            if holidays:
                # La validación automática debe realizarse en sudo, ya que es posible que el usuario no tenga los derechos para hacerlo por sí mismo.
                holidays.sudo().action_validate()
            rec.activity_update()
        return True

    def action_documents(self):
        domain = [('id', 'in', self.attachment_ids.ids)]
        return {
            'name': _("Documentos de Sustento"),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'context': {'create': False},
            'view_mode': 'list',
            'domain': domain
        }

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return
        current_employee = self.env.user.employee_id
        is_manager = self.env.user.has_group('hr_leave_it.group_hr_holidays_manager')

        for holiday in self:
            val_type = holiday.validation_type
            if not is_manager and state != 'confirm':
                if state == 'draft':
                    if holiday.state == 'refuse':
                        raise UserError(_('Solo el Administrador de Ausencias puede restablecer una solicitud rechazada.'))
                    if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Solo un administrador de Ausencias puede restablecer una Solicitud iniciada.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Solo un administrador de ausencias puede restablecer las solicitudes de otras personas.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.employee_id:
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    if holiday.employee_id == current_employee:
                        raise UserError(_('Solo un administrador de ausencias puede aprobar/rechazar sus propias solicitudes.'))

    # ------------------------------------------------------------
    # Activity methods
    # ------------------------------------------------------------

    def _get_responsible_for_approval(self):
        self.ensure_one()
        responsible = self.env.user
        if self.validation_type == 'manager' or (self.validation_type == 'both' and self.state == 'confirm'):
            if self.employee_id.leave_manager_id:
                responsible = self.employee_id.leave_manager_id
        elif self.validation_type == 'hr' or (self.validation_type == 'both' and self.state == 'validate1'):
            if self.leave_type_id.responsible_id:
                responsible = self.leave_type_id.responsible_id
        return responsible

    def activity_update(self):
        to_clean, to_do = self.env['hr.leave.it'], self.env['hr.leave.it']
        for holiday in self:
            note = _(
                'New %(leave_type)s Request created by %(user)s',
                leave_type=holiday.leave_type_id.name,
                user=holiday.create_uid.name,
            )
            if holiday.state == 'draft':
                to_clean |= holiday
            elif holiday.state == 'confirm':
                holiday.activity_schedule(
                    'hr_leave_it.mail_act_leave_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate1':
                holiday.activity_feedback(['hr_leave_it.mail_act_leave_approval'])
                holiday.activity_schedule(
                    'hr_leave_it.mail_act_leave_second_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
        if to_clean:
            to_clean.activity_unlink(['hr_leave_it.mail_act_leave_approval', 'hr_leave_it.mail_act_leave_second_approval'])
        if to_do:
            to_do.activity_feedback(['hr_leave_it.mail_act_leave_approval', 'hr_leave_it.mail_act_leave_second_approval'])

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        # due to record rule can not allow to add follower and mention on validated leave so subscribe through sudo
        if self.state in ['validate', 'validate1']:
            self.check_access_rights('read')
            self.check_access_rule('read')
            return super(HrLeaveIt, self.sudo()).message_subscribe(partner_ids=partner_ids, subtype_ids=subtype_ids)
        return super(HrLeaveIt, self).message_subscribe(partner_ids=partner_ids, subtype_ids=subtype_ids)

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        return self.env.user.employee_id.sudo(False)._get_unusual_days(date_from, date_to)