# -*- encoding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools.misc import formatLang, format_date, get_lang
import requests
import json
import datetime
import logging
log = logging.getLogger(__name__)

class LogisticPoint(models.Model):
    _name = 'logistic.point'
    _description = 'Logistic Point'

    code = fields.Char('Code')
    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', string='Address')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses Related')

    @api.model
    def create(self, vals):
        res = super(LogisticPoint, self).create(vals)
        res.code = str(res.id).zfill(3)
        return res


class LogisticRoute(models.Model):
    _name = 'logistic.route'
    _description = 'Logistic Route'

    code = fields.Char('Code')
    name = fields.Char('Name')
    logistic_point_departure_id = fields.Many2one(
        'logistic.point', string='Departure')
    logistic_point_delivery_id = fields.Many2one(
        'logistic.point', string='Delivery')

    @api.model
    def create(self, vals):
        res = super(LogisticRoute, self).create(vals)
        res.code = str(res.id).zfill(3)
        return res


class LogisticDespatch(models.Model):
    _name = 'logistic.despatch'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Logistic Despatchs"
    _order = 'issue_date desc, name desc'
    _mail_post_access = 'read'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    type = fields.Selection([('out_despatch','Out Despatch'),('in_despatch','In Despatch')], string='Type', default='out_despatch')
    name = fields.Char(string='#', default='/', copy=False)
    ref = fields.Char(string='Reference')
    issue_date = fields.Date(string='Date despatch', readonly=True, copy=True, states={
                             'draft': [('readonly', False)], })
    start_date = fields.Date(string='Date start', readonly=True, copy=True, states={
                             'draft': [('readonly', False)], })
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('logistic.despatch'))
    partner_id = fields.Many2one('res.partner', string='Receiver', readonly=True, states={
                                 'draft': [('readonly', False)], })
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True, states={'draft': [('readonly', False)], })
    domain_journal_id = fields.Many2many('account.journal', compute='_compute_domain_journal_id')

    origin_address_id = fields.Many2one('res.partner', 'Origin Address', readonly=True, states={
                                        'draft': [('readonly', False)], })
    delivery_address_id = fields.Many2one('res.partner', 'Delivery Address', readonly=True, copy=True, states={
                                        'draft': [('readonly', False)], })
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', readonly=True, copy=True, states={
                                 'draft': [('readonly', False)], })
    driver_id = fields.Many2one('res.partner', string='Vehicle Driver', domain=[(
        'logistic_is_driver', '=', True)], readonly=True, copy=True, states={'draft': [('readonly', False)], })
    carrier_id = fields.Many2one('res.partner', string='Carrier',
                                 readonly=True, copy=True, states={'draft': [('readonly', False)], })

    total_volume = fields.Float(string='Volume', readonly=True, compute='_compute_weight_and_volume', store=True, copy=True, states={
                          'draft': [('readonly', False)], })
    total_weight = fields.Float(string='Weight', readonly=True, compute='_compute_weight_and_volume', store=True, copy=True, states={
                          'draft': [('readonly', False)], })
    weight_uom = fields.Many2one('uom.uom', string='UoM of weight',
                                 readonly=True, copy=True, states={'draft': [('readonly', False)], })
    packages = fields.Float(string='Packages', readonly=True, copy=True, states={
                            'draft': [('readonly', False)], })
    note = fields.Text(string='Notes')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('cancel', 'Cancel')], string='Status', default='draft')
    line_ids = fields.One2many('logistic.despatch.line', 'despatch_id',
                               readonly=True, copy=True, states={'draft': [('readonly', False)], })

    picking_ids = fields.Many2many('stock.picking', string='Pickings', readonly=True, copy=False, states={
                                   'draft': [('readonly', False)], })
    internal_number = fields.Char(string='Internal number', readonly=True, copy=False)
    despatch_origin = fields.Char(string='Origin', readonly=True, tracking=True,
        help="The document(s) that generated the despatch.")
    despatch_sent = fields.Boolean(readonly=True, default=False, copy=False,
        help="It indicates that the despatch has been sent.")
    despatch_user_id = fields.Many2one('res.users', copy=False, tracking=True,
        string='Salesperson',
        default=lambda self: self.env.user)
    user_id = fields.Many2one(string='User', related='despatch_user_id',
        help='Technical field used to fit the generic behavior in mail templates.')
    type_name = fields.Char('Type Name', compute='_compute_type_name')


    @api.model
    def default_get(self, fieldsx):
        res = super(LogisticDespatch, self).default_get(fieldsx)
        res.update({
            'issue_date': fields.Date.context_today(self)
        })

        return res

    @api.depends('warehouse_id')
    def _compute_domain_journal_id(self):
        for rec in self:
            if rec.warehouse_id.despatch_journal_ids:
                rec.domain_journal_id = rec.warehouse_id.despatch_journal_ids
            else:
                rec.domain_journal_id = self.env['account.journal'].search([('type','=','general')])

    @api.depends('line_ids.weight','line_ids.volume')
    def _compute_weight_and_volume(self):
        for rec in self:
            rec.total_weight = sum(self.line_ids.mapped('weight'))
            rec.total_volume = sum(self.line_ids.mapped('volume'))

    @api.depends('type')
    def _compute_type_name(self):
        type_name_mapping = {k: v for k, v in
                             self._fields['type']._description_selection(self.env)}
        replacements = {'out_despatch': _('Despatch')}

        for record in self:
            name = type_name_mapping[record.type]
            record.type_name = replacements.get(record.type, name)

    def unlink(self):
        for despatch in self:
            if despatch.state != 'draft':
                raise Warning(
                    'Despatch cannot be deleted if it is not in draft status.')
            if not (despatch.internal_number == None or despatch.internal_number == '' or despatch.internal_number == False):
                raise Warning(
                    'Despatch cannot be deleted!')
        return super().unlink()

    def action_cancel(self):
        for despatch in self:
            despatch.write({'state': 'cancel', 'name': False})

    def action_draft(self):
        for despatch in self:
            if despatch.state != 'cancel':
                raise Warning('The Despatch cannot be returned to draft if it is not in canceled status.')
            despatch.write({'state': 'draft'})

    def action_validate_despatch(self):
        pass

    def action_open(self):
        for rec in self:
            if not rec.journal_id:
                raise Warning(_('Journal is required to manage the despatch sequence'))
            rec.action_validate_despatch()
            if rec.internal_number and rec.internal_number != '':
                rec.name = rec.internal_number
            else:
                rec.name = rec.journal_id.despatch_sequence_id.next_by_id()
                rec.internal_number = rec.name
            if not rec.issue_date:
                rec.issue_date = fields.Date.context_today(self)
            if not rec.start_date:
                rec.start_date = fields.Date.context_today(self)
            rec.state = 'open'

    def action_despatch_sent(self):
        """ Open a window to compose an email, with the edi despatch template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('logistic.email_template_edi_despatch', raise_if_not_found=False)
        lang = get_lang(self.env)
        if template and template.lang:
            lang = template._render_template(template.lang, 'logistic.despatch', self.id)
        else:
            lang = lang.code
        compose_form = self.env.ref('logistic.logistic_despatch_send_wizard_form', raise_if_not_found=False)
        ctx = dict(
            default_model='logistic.despatch',
            default_res_id=self.id,
            # For the sake of consistency we need a default_res_model if
            # default_res_id is set. Not renaming default_model as it can
            # create many side-effects.
            default_res_model='logistic.despatch',
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_despatch_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).type_name,
            force_email=True
        )
        return {
            'name': _('Send Despatch'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'logistic.despatch.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def _get_despatch_display_name(self, show_ref=False):
        ''' Helper to get the display name of an despatch depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the despatch reference.
        :return:            A string representing the despatch.
        '''
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft':
            draft_name += {
                'out_despatch': _('Draft Despatch'),
                'in_despatch': _('Draft Despatch'),
            }[self.type]
            if not self.name or self.name == '/':
                draft_name += ' (* %s)' % str(self.id)
            else:
                draft_name += ' ' + self.name
        return (draft_name or self.name) + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')

    def _get_report_base_filename(self):
        return self._get_despatch_display_name()

    def _get_name_despatch_report(self, report_xml_id):
        self.ensure_one()
        return report_xml_id

class LogisticDespatchLine(models.Model):
    _name = 'logistic.despatch.line'
    _description = 'Logistic Despatch Line'

    despatch_id = fields.Many2one('logistic.despatch', string='Despatch')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    name = fields.Char(string='Description')
    uom_id = fields.Many2one(
        'uom.uom', string='UoM', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    weight = fields.Float(string='Weight', digits=(9,3))
    volume = fields.Float(string='Volume', digits=(9,3))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id
        self.name = self.product_id.display_name

    @api.onchange('product_id','quantity')
    def _onchange_prod_and_qty(self):
        if self.product_id:
            self.weight = self.product_id.weight*self.quantity
            self.volume = self.product_id.volume*self.quantity


class LogisticExpedition(models.Model):
    _name = 'logistic.expedition'
    _description = 'Logistic Expedition'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='#', default='/')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('logistic.expedition'))
    date_order = fields.Date(string='Date', required=True)
    date_start = fields.Date(string='Date of start', required=True)
    date_end = fields.Date(string='Date of end')
    route_id = fields.Many2one('logistic.route', string='Expedition Route', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    #carrier_id = fields.Many2one('delivery.carrier', string='Carrier')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('res.partner', string='Vehicle Carrier')
    tracking_code = fields.Char(string='Tracking Code')
    picking_ids = fields.One2many(
        'stock.picking', 'expedition_id', string='Pickings')
    net_weight = fields.Float(string='Net Weight')
    gross_weight = fields.Float(string='Gross Weight')
    opened_date = fields.Datetime(string='Authorized at')
    opened_uid = fields.Many2one('res.users', string='Authorized by')
    done_date = fields.Datetime(string='Finalized at')
    done_uid = fields.Many2one('res.users', string='Finalized by')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Authorized'), (
        'done', 'Finalized'), ('cancel', 'Cancel')], string='Status', default='draft')

    @api.model
    def create(self, vals):
        res = super(LogisticExpedition, self).create(vals)
        res.name = str(res.id).zfill(10)
        return res

    def action_open(self):
        for rec in self:
            _dict = {
                'state': 'open',
                'opened_date': fields.Datetime.now(),
                'opened_uid': self.env.uid
            }
            if rec.name == "/":
                _dict['name'] = self.env['ir.sequence'].next_by_code(
                    'logistic.expedition')
            rec.write(_dict)

    def action_get_picking(self):
        for rec in self:
            zone_ids = []
            for zone in rec.route_id.zone_ids:
                zone_ids.append(zone.id)
            pickings = self.env['stock.picking'].search([('expedition_id', '=', False), (
                'scheduled_date', '>=', '%s 00:00:00' % rec.date_start), ('scheduled_date', '<=', '%s 23:59:59' % rec.date_start), ('state', 'in', ('confirmed', 'assigned'))])
            for picking in pickings:
                picking.write({'expedition_id': rec.id})

    def action_done(self):
        for rec in self:
            rec.write({
                'state': 'done',
                'done_date': fields.Datetime.now(),
                'done_uid': self.env.uid
            })

    def action_view_expedition_despatch(self):
        self.env.cr.execute(
            """SELECT DISTINCT ON (despatch_id) despatch_id FROM stock_picking WHERE expedition_id=%s AND despatch_id IS NOT NULL ORDER BY despatch_id DESC""" % self.id)
        res = self.env.cr.dictfetchall()
        action = self.env.ref(
            'logistic.action_logistic_despatch_tree').read()[0]
        if len(res) > 0:
            action['domain'] = [
                ('id', 'in', [int(despatch.get('despatch_id')) for despatch in res])]
        else:
            action['domain'] = [('id', '=', -1)]
        return action
