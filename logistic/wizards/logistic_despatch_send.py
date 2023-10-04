# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang


class LogisticDespatchSend(models.TransientModel):
    _name = 'logistic.despatch.send'
    _inherits = {'mail.compose.message':'composer_id'}
    _description = 'Logistic Despatch Send'

    is_email = fields.Boolean('Email', default=lambda self: self.env.company.invoice_is_email)
    despatch_without_email = fields.Text(compute='_compute_despatch_without_email', string='despatch(s) that will not be sent')
    is_print = fields.Boolean('Print', default=lambda self: self.env.company.invoice_is_print)
    printed = fields.Boolean('Is Printed', default=False)
    despatch_ids = fields.Many2many('logistic.despatch', 'logistic_logistic_despatch_send_rel', string='Despatchs')
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=True, ondelete='cascade')
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True,
        domain="[('model', '=', 'logistic.despatch')]"
        )

    @api.model
    def default_get(self, fields):
        res = super(LogisticDespatchSend, self).default_get(fields)
        res_ids = self._context.get('active_ids')

        despatchs = self.env['logistic.despatch'].browse(res_ids)
        if not despatchs:
            raise UserError(_("You can only send despatchs."))

        composer = self.env['mail.compose.message'].create({
            'composition_mode': 'comment' if len(res_ids) == 1 else 'mass_mail',
        })
        res.update({
            'despatch_ids': res_ids,
            'composer_id': composer.id,
        })
        return res

    @api.onchange('despatch_ids')
    def _compute_composition_mode(self):
        for wizard in self:
            wizard.composer_id.composition_mode = 'comment' if len(wizard.despatch_ids) == 1 else 'mass_mail'

    @api.onchange('template_id')
    def onchange_template_id(self):
        for wizard in self:
            if wizard.composer_id:
                wizard.composer_id.template_id = wizard.template_id.id
                wizard._compute_composition_mode()
                wizard.composer_id.onchange_template_id_wrapper()

    @api.onchange('is_email')
    def onchange_is_email(self):
        if self.is_email:
            if not self.composer_id:
                res_ids = self._context.get('active_ids')
                self.composer_id = self.env['mail.compose.message'].create({
                    'composition_mode': 'comment' if len(res_ids) == 1 else 'mass_mail',
                    'template_id': self.template_id.id
                })
            else:
                self.composer_id.template_id = self.template_id.id
            self.composer_id.onchange_template_id_wrapper()

    @api.onchange('is_email')
    def _compute_despatch_without_email(self):
        for wizard in self:
            if wizard.is_email and len(wizard.despatch_ids) > 1:
                despatchs = self.env['logistic.despatch'].search([
                    ('id', 'in', self.env.context.get('active_ids')),
                    ('partner_id.email', '=', False)
                ])
                if despatchs:
                    wizard.despatch_without_email = "%s\n%s" % (
                        _("The following despatch(s) will not be sent by email, because the receiver don't have email address."),
                        "\n".join([i.name for i in despatchs])
                        )
                else:
                    wizard.despatch_without_email = False
            else:
                wizard.despatch_without_email = False

    def _send_email(self):
        if self.is_email:
            self.composer_id.send_mail()
            if self.env.context.get('mark_despatch_as_sent'):
                self.mapped('despatch_ids').sudo().write({'despatch_sent': True})
            for inv in self.despatch_ids:
                if hasattr(inv, 'attachment_ids') and inv.attachment_ids:
                    inv._message_set_main_attachment_id([(False,att) for att in inv.attachment_ids.ids])

    def _print_document(self):
        """ to override for each type of models that will use this composer."""
        self.ensure_one()
        return False
        #action = self.despatch_ids.action_despatch_print()
        #action.update({'close_on_report_download': True})
        #return action

    def send_and_print_action(self):
        self.ensure_one()
        # Send the mails in the correct language by splitting the ids per lang.
        # This should ideally be fixed in mail_compose_message, so when a fix is made there this whole commit should be reverted.
        # basically self.body (which could be manually edited) extracts self.template_id,
        # which is then not translated for each customer.
        if self.composition_mode == 'mass_mail' and self.template_id:
            active_ids = self.env.context.get('active_ids', self.res_id)
            active_records = self.env[self.model].browse(active_ids)
            langs = active_records.mapped('partner_id.lang')
            default_lang = get_lang(self.env)
            for lang in (set(langs) or [default_lang]):
                active_ids_lang = active_records.filtered(lambda r: r.partner_id.lang == lang).ids
                self_lang = self.with_context(active_ids=active_ids_lang, lang=lang)
                self_lang.onchange_template_id()
                self_lang._send_email()
        else:
            self._send_email()
        if self.is_print:
            return self._print_document()
        return {'type': 'ir.actions.act_window_close'}

    def save_as_template(self):
        self.ensure_one()
        self.composer_id.save_as_template()
        self.template_id = self.composer_id.template_id.id
        action = _reopen(self, self.id, self.model, context=self._context)
        action.update({'name': _('Send Despatch')})
        return action