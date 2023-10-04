# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
	_inherit = 'account.move'

	asset_asset_ids = fields.One2many('account.asset.asset','invoice_id',string='Activos')
	number_asset_asset_ids = fields.Integer(compute="_compute_number_asset_asset_ids")

	@api.depends('asset_asset_ids')
	def _compute_number_asset_asset_ids(self):
		for record in self:
			record.number_asset_asset_ids = len(record.asset_asset_ids)

	@api.model
	def _refund_cleanup_lines(self, lines):
		result = super(AccountInvoice, self)._refund_cleanup_lines(lines)
		for i, line in enumerate(lines):
			for name, field in line._fields.items():
				if name == 'asset_category_id':
					result[i][2][name] = False
					break
		return result

	def action_cancel(self):
		res = super(AccountInvoice, self).action_cancel()
		self.env['account.asset.asset'].sudo().search([('invoice_id', 'in', self.ids)]).write({'active': False})
		return res

	def button_draft(self):
		res = super(AccountInvoice, self).button_draft()
		assets = self.env['account.asset.asset'].sudo().search([('invoice_id', 'in', self.ids)])
		if assets:
			raise UserError(u'Tiene activos que están vinculados a esta factura, primero elimínelos: \n %s'%(','.join(str(asset.name) for asset in assets)))
		return res

	def action_post(self):
		result = super(AccountInvoice, self).action_post()
		for inv in self:
			context = dict(self.env.context)
			context.pop('default_type', None)
			for mv_line in inv.invoice_line_ids:
				mv_line.with_context(context).asset_create()
		return result
	
	def action_open_asset_asset(self):
		self.ensure_one()
		action = self.env.ref('om_account_asset.action_account_asset_asset_form').read()[0]
		domain = [('id', 'in', self.asset_asset_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('om_account_asset.view_account_asset_asset_purchase_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)


class AccountInvoiceLine(models.Model):
	_inherit = 'account.move.line'

	asset_category_id = fields.Many2one('account.asset.category', string='Categoria de Activos')
	asset_start_date = fields.Date(string='Asset Start Date', compute='_get_asset_date', readonly=True, store=True)
	asset_end_date = fields.Date(string='Asset End Date', compute='_get_asset_date', readonly=True, store=True)
	asset_mrr = fields.Float(string='Monthly Recurring Revenue', compute='_get_asset_date', readonly=True,
							 digits="Account", store=True)

	@api.depends('asset_category_id', 'move_id.invoice_date')
	def _get_asset_date(self):
		for rec in self:
			rec.asset_mrr = 0
			rec.asset_start_date = False
			rec.asset_end_date = False
			cat = rec.asset_category_id
			if cat:
				#if cat.method_number == 0 or cat.method_period == 0:
				#	raise UserError(_('The number of depreciations or the period length of '
				#					  'your asset category cannot be 0.'))
				months = cat.method_number * cat.method_period
				if rec.move_id.move_type in ['out_invoice', 'out_refund']:
					rec.asset_mrr = rec.price_subtotal / months if months != 0 else 0
				if rec.move_id.invoice_date:
					start_date = rec.move_id.invoice_date.replace(day=1)
					end_date = (start_date + relativedelta(months=months, days=-1)) if months != 0 else start_date
					rec.asset_start_date = start_date
					rec.asset_end_date = end_date

	def asset_create(self):
		asset = False
		if self.asset_category_id:
			amount = self.price_subtotal
			if self.move_id.currency_id.name != 'PEN':
				amount = self.price_subtotal * self.move_id.currency_rate
			amount_dolars = self.price_subtotal if self.move_id.currency_id.name != 'PEN' else (self.price_subtotal/self.move_id.currency_rate)
			vals = {
				'name': self.name,
				'category_id': self.asset_category_id.id,
				'value': amount,
				'partner_id': self.move_id.partner_id.id,
				'company_id': self.move_id.company_id.id,
				'currency_id': self.move_id.company_currency_id.id,
				'date': self.move_id.invoice_date,
				'first_depreciation_manual_date': self.move_id.invoice_date.replace(day=1) + relativedelta(months=1),
				'invoice_id': self.move_id.id,
				'tipo_cambio_d': self.move_id.currency_rate,
				'bruto_dolares': amount_dolars,
				'cuo':str(self.id),
			}
			changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
			vals.update(changed_vals['value'])
			asset = self.env['account.asset.asset'].create(vals)
			asset.change_method_number()
			asset.change_years_depreciations()
			if self.asset_category_id.open_asset:
				asset.validate()
		return asset

	@api.onchange('asset_category_id')
	def onchange_asset_category_id(self):
		if self.move_id.move_type == 'out_invoice' and self.asset_category_id:
			self.account_id = self.asset_category_id.account_asset_id.id
		elif self.move_id.move_type == 'in_invoice' and self.asset_category_id:
			self.account_id = self.asset_category_id.account_asset_id.id

	@api.onchange('product_uom_id')
	def _onchange_uom_id(self):
		result = super(AccountInvoiceLine, self)._onchange_uom_id()
		self.onchange_asset_category_id()
		return result

	@api.onchange('product_id')
	def _onchange_product_id(self):
		vals = super(AccountInvoiceLine, self)._onchange_product_id()
		if self.product_id:
			if self.move_id.move_type == 'out_invoice':
				self.asset_category_id = self.product_id.product_tmpl_id.deferred_revenue_category_id
			elif self.move_id.move_type == 'in_invoice':
				self.asset_category_id = self.product_id.product_tmpl_id.asset_category_id
		return vals

	def _set_additional_fields(self, invoice):
		if not self.asset_category_id:
			if invoice.type == 'out_invoice':
				self.asset_category_id = self.product_id.product_tmpl_id.deferred_revenue_category_id.id
			elif invoice.type == 'in_invoice':
				self.asset_category_id = self.product_id.product_tmpl_id.asset_category_id.id
			self.onchange_asset_category_id()
		super(AccountInvoiceLine, self)._set_additional_fields(invoice)

	def get_invoice_line_account(self, type, product, fpos, company):
		return product.asset_category_id.account_asset_id or super(AccountInvoiceLine, self).get_invoice_line_account(type, product, fpos, company)
