# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class bank_loans(models.Model):
	_name = 'bank.loans'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	_description = 'Prestamos'
	

	name = fields.Char('name',default='Prestamo')
	partner_id = fields.Many2one('res.partner', string='Entidad Bancaria',tracking=True)
	date_loan = fields.Date(string='Fecha de Prestamo',tracking=True,default=fields.Date.context_today)
	rate_int = fields.Float(u'Tasa de Interés',tracking=True)
	cuotas =  fields.Integer(u'Cuotas',tracking=True)
	lines_ids = fields.One2many('bank.loans.lines', 'loan_id', string='Detalle',copy=False)
	company_id = fields.Many2one('res.company', string=u'Compañia',required=True, readonly=True, default=lambda self: self.env.company.id)

	nro_comp = fields.Char('Nro Comprobante',required=True,tracking=True)
	cap_pres = fields.Float(u'Capital Prestado',tracking=True)
	inters = fields.Float(u'Intereses',tracking=True)
	amount_total_debt = fields.Float(u'Total Deuda',compute="_compute_amount_total_debt")
	bal_init = fields.Float(u'Saldo Inicial',tracking=True)
	amount_total_amort = fields.Float(u'Amortizaciones',compute="_compute_amount_total_amort")
	amount_debt = fields.Float(u'Saldo Adeudado',compute="_compute_amount_debt")
	
	state = fields.Selection([
		('draft', 'BORRADOR'),
		('done', 'VALIDADO')
	], string='Estado',tracking=True,copy=False,default='draft')

	move_id = fields.Many2one('account.move', string='Asiento',tracking=True,copy=False)
	journal_id = fields.Many2one('account.journal', string='Caja o Banco',tracking=True,copy=False)
	interest_account_id = fields.Many2one('account.account', string='Cuenta de Interes Diferido',tracking=True,copy=False)
	expense_account_id = fields.Many2one('account.account', string='Cuenta de Gastos Interes',tracking=True,copy=False)
	due_account_id = fields.Many2one('account.account', string='Cuenta de Deuda Prestamo',tracking=True,copy=False)
	currency_id = fields.Many2one('res.currency', string='Moneda',compute="_compute_currency_id")
	tc = fields.Float(u'Tipo de Cambio',tracking=True,default=1)
	#########################################################################################

	@api.onchange('date_loan')
	def _onchange_tc(self):
		for record in self:							
			type_now=self.env['res.currency.rate'].sudo().search([('name','=',record.date_loan),('company_id','=',record.company_id.id)])			
			if type_now:
				record.tc = type_now.sale_type					
	
		

	@api.depends('journal_id','journal_id.currency_id')
	def _compute_currency_id(self):
		for record in self:
			record.currency_id = (self.env['res.currency'].search([('name','=','PEN')],limit=1).id if self.env['res.currency'].search([('name','=','PEN')],limit=1).id else False)
			if record.journal_id.currency_id:
				record.currency_id = record.journal_id.currency_id.id

	def action_post(self):
		for i in self:
			i.state = 'done'
	
	def create_account(self):
		for i in self:
			
			i.validate_fields()
			doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
			data=i.libray_data_move(doc)
			obj_move = self.env['account.move'].create(data)
			i.move_id=obj_move.id
			obj_move.action_post()
	
	def validate_fields(self):
		for i in self:
			if not i.nro_comp:
				raise ValidationError(u'Es necesario el campo "Nro Comprobante"')
			if not i.interest_account_id:
				raise ValidationError(u'Es necesario el campo "Cuenta de Interes Diferido"')
			if not i.due_account_id:
				raise ValidationError(u'Es necesario el campo "Cuenta de Deuda Prestamo"')
			if not i.company_id.account_journal_payment_credit_account_id:
				raise ValidationError(u'No esta configurada la cuenta de pagos pendientes en los AJUSTES DE CONTABILIDAD')
			if not i.company_id.account_journal_payment_debit_account_id:
				raise ValidationError(u'No esta configurada la cuenta de cobros pendientes en los AJUSTES DE CONTABILIDAD')

	def libray_data_line(self,doc):
		for i in self:
			move_lines = []
			account = [i.company_id.account_journal_payment_debit_account_id.id,i.interest_account_id.id,i.due_account_id.id]
			amount_currency = [i.cap_pres,i.inters,i.amount_total_debt*-1]
			if i.currency_id.name == 'USD':
				debit =  [i.cap_pres*i.tc,i.inters*i.tc,0]
				credit =  [0,0,i.amount_total_debt*i.tc]
			else:
				debit =  [i.cap_pres,i.inters,0]
				credit =  [0,0,i.amount_total_debt]
			for r in range(3):
				line_firt = (0,0,{
							'account_id': account[r],
							'currency_id': i.currency_id.id,
							'amount_currency': float(amount_currency[r]),
							'debit':debit[r],
							'credit':credit[r],
							'name': i.nro_comp,
							'partner_id': i.partner_id.id,
							'company_id': i.company_id.id,		
							'nro_comp': i.nro_comp,
							'type_document_id': doc.id,
							'tc': i.tc,
							})
				#raise ValidationError(amount_currency[r])			
				move_lines.append(line_firt)
			return move_lines
	
	def libray_data_move(self,doc):
		for i in self:		
			data = {
				'journal_id': i.journal_id.id,
				'ref': i.nro_comp,
				'date': i.date_loan,
				'company_id': i.company_id.id,
				'glosa': "PRESTAMO SEGUN COMPROBANTE %s"%(i.nro_comp),
				'currency_rate': i.tc,
				'currency_id': i.currency_id.id,
				'move_type':'entry',
				'line_ids':i.libray_data_line(doc)
			}			
		return data
	
	def unlink(self):
		for i in self:
			if i.state == 'done':
				raise ValidationError(u'EL PRESTAMO NO PUEDE SER ELIMINADO PORQUE ESTA VALIDADO')
			return super(bank_loans,self).unlink()
	@api.depends('lines_ids','lines_ids.move_id')
	def _compute_amount_total_amort(self):
		for record in self:
			values = record.lines_ids.filtered(lambda l: l.move_id).mapped('quota')
			if values:
				record.amount_total_amort = sum(values)
			else:
				record.amount_total_amort = 0

	@api.depends('cap_pres','inters')
	def _compute_amount_total_debt(self):
		for i in self:
			i.amount_total_debt = i.cap_pres + i.inters

	@api.depends('bal_init','amount_total_amort')
	def _compute_amount_debt(self):
		for i in self:
			i.amount_debt = i.bal_init-i.amount_total_amort

	def action_wizard(self):
		return {
			'name': 'Importar Lines',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'bank.loans.lines.import',
			'context': {'default_loan_id': self.id},
			'target': 'new',
		}
	def open_move(self):
		return {
			'view_mode': 'form',
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.move_id.id,
		}
	
	def action_draft(self):
		for i in self:
			if i.move_id or i.amount_total_amort !=0:
				raise ValidationError(u'PRIMERO ELIMINE TODOS LOS ASIENTOS RELACIAONADOS CON EL PRESTAMO')
			else:
				i.state = 'draft'
