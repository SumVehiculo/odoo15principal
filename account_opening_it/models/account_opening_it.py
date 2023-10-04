# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid
from datetime import datetime

class AccountOpeningIt(models.Model):
	_name = 'account.opening.it'
	_description = 'Account Opening It'

	@api.depends('from_fiscal_year_id','to_fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = (i.from_fiscal_year_id.name if i.from_fiscal_year_id else '') + ' - ' + (i.to_fiscal_year_id.name if i.to_fiscal_year_id else '')

	name = fields.Char(compute=_get_name,store=True)
	from_fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio Anterior',required=True)
	to_fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio Actual',required=True)
	journal_id = fields.Many2one('account.journal',string='Diario Apertura',required=True)
	account_id = fields.Many2one('account.account',string='Cuenta de Resultado Acumulado',required=True)
	partner_id = fields.Many2one('res.partner',string='Partner Apertura',required=True)
	ref = fields.Char(string='Documento Apertura',required=True)
	state = fields.Selection([('draft','BORRADOR'),
							('done','REALIZADO')],string='Estado',default='draft')
	move_ids = fields.One2many('account.move','opening_id_it',string='Asientos de Apertura')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	def unlink(self):
		if self.state == 'done':
			raise UserError("No se puede eliminar una Apertura Contable si no esta en estado Borrador.")
		return super(AccountOpeningIt,self).unlink()
	
	def preview_opening(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Apertura_contable.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("ASIENTO PRINCIPAL")
		worksheet.set_tab_color('blue')

		HEADERS = ['CUENTA','DEBE','HABER','MONEDA','IMPORTE EN MONEDA','TC']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		accounts = []

		self.env.cr.execute("""select a.account_id,c.currency_id,
							case when sum(coalesce(a.balance,0))> 0 then sum(coalesce(a.balance,0)) else 0 end as activo,
							case when sum(coalesce(a.balance,0))< 0 then abs(sum(coalesce(a.balance,0))) else 0 end as pasivo,
							sum(coalesce(a.amount_currency,0)) as amount_currency
							from account_move_line a
							left join account_move b on b.id=a.move_id
							left join account_account c on c.id=a.account_id
							where b.date between '%s' and '%s' and b.company_id=%d and b.state='posted' and c.clasification_sheet='0' AND a.display_type IS NULL AND a.account_id IS NOT NULL
							group by a.account_id,c.currency_id
							having sum(coalesce(a.balance,0)) <> 0"""%(self.from_fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			self.from_fiscal_year_id.date_to.strftime('%Y/%m/%d'),
			self.company_id.id))

		res = self.env.cr.dictfetchall()
		doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
		sum_debit = sum_credit = 0
		for elem in res:
			account_id = self.env['account.account'].browse(elem['account_id'])
			if account_id.is_document_an:
				accounts.append(elem)
			worksheet.write(x,0,account_id.code if account_id else '',formats['especial1'])
			worksheet.write(x,1,elem['activo'] if elem['activo'] else 0,formats['numberdos'])
			worksheet.write(x,2,elem['pasivo'] if elem['pasivo'] else 0,formats['numberdos'])
			worksheet.write(x,3,account_id.currency_id.name if account_id.currency_id else '',formats['especial1'])
			worksheet.write(x,4, elem['amount_currency'] if account_id.currency_id else 0,formats['numberdos'])
			worksheet.write(x,5,(abs(elem['activo'] - elem['pasivo'])/abs(elem['amount_currency']) if abs(elem['amount_currency']) != 0 else 0) if account_id.currency_id else 1,formats['numberdos'])
			sum_debit += elem['activo']
			sum_credit += elem['pasivo']
			x += 1
		
		if sum_debit > sum_credit:
			worksheet.write(x,0,self.account_id.code if self.account_id else '',formats['especial1'])
			worksheet.write(x,1,0,formats['numberdos'])
			worksheet.write(x,2,sum_debit-sum_credit,formats['numberdos'])
			worksheet.write(x,3,'',formats['especial1'])
			worksheet.write(x,4,0,formats['numberdos'])
			worksheet.write(x,5,1,formats['numberdos'])
		
		if sum_debit < sum_credit:
			worksheet.write(x,0,self.account_id.code if self.account_id else '',formats['especial1'])
			worksheet.write(x,1,sum_credit-sum_debit,formats['numberdos'])
			worksheet.write(x,2,0,formats['numberdos'])
			worksheet.write(x,3,'',formats['especial1'])
			worksheet.write(x,4,0,formats['numberdos'])
			worksheet.write(x,5,1,formats['numberdos'])
			
		
		widths = [15,12,12,10,15,7]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		worksheet = workbook.add_worksheet("DETALLADO")
		worksheet.set_tab_color('green')
		HEADERS = ['CUENTA','TD','NRO COMPROBANTE','SOCIO','FECHA DOC','FECHA VEN','DEBE','HABER','MONEDA','IMPORTE EN MONEDA','TC']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		for account in accounts:
			account_id = self.env['account.account'].browse(account['account_id'])
			self.env.cr.execute("""SELECT T.*, ei.code as td_sunat, rp.vat as doc_partner,
			case when T2.fecha_emision is null then T.fecha_con else T2.fecha_emision end as fecha_doc
			FROM 
			(select a.partner_id,a.account_id,a.type_document_id,
			a.nro_comp as nro_comprobante,b.currency_id,sum(coalesce(a.balance,0)) as saldo_mn,
			sum(coalesce(a.amount_currency,0)) as saldo_me, min(a.date) as fecha_con, min(a.date_maturity) as fecha_ven
			from account_move_line a
			left join account_account b on b.id=a.account_id
			left join account_move c on c.id=a.move_id
			where (c.date between '%s' and '%s') and c.state='posted' and b.is_document_an = True AND a.display_type IS NULL AND a.account_id = %d
			and a.company_id = %d 
			group by a.partner_id,a.account_id,a.type_document_id,a.nro_comp,b.currency_id
			having sum(coalesce(a.balance,0))<>0)T

			left join
			(select a2.id as move_id,a1.id as move_line_id,a1.account_id,a1.partner_id,a1.type_document_id,a1.nro_comp,
			a2.date as fecha_contable,
			a2.invoice_date as fecha_emision,
			a1.date_maturity as fecha_vencimiento,
			a2.glosa as glosa,
			a1.debit-a1.credit as monto_ini_mn,a1.amount_currency as monto_ini_me,
			a2.currency_id
			from account_move_line a1
			left join account_move a2 on a2.id=a1.move_id
			left join account_account a3 on a3.id=a1.account_id
			where a2.move_type in ('out_receipt','in_receipt','out_invoice','in_invoice','out_refund','in_refund') and
			a3.internal_type in ('payable','receivable') and a2.state='posted' and a1.company_id=%d
			)T2 on (T2.account_id=T.account_id and T2.partner_id=T.partner_id and T2.type_document_id=T.type_document_id and T2.nro_comp=T.nro_comprobante)

			LEFT JOIN l10n_latam_document_type ei ON ei.id = T.type_document_id
			LEFT JOIN res_partner rp on rp.id = T.partner_id"""%(self.from_fiscal_year_id.date_from.strftime('%Y/%m/%d'),
																self.from_fiscal_year_id.date_to.strftime('%Y/%m/%d'),
																account_id.id,
																self.company_id.id,
																self.company_id.id))
			line_data = self.env.cr.dictfetchall()
			for line in line_data:
				worksheet.write(x,0,account_id.code if account_id else '',formats['especial1'])
				worksheet.write(x,1,line['td_sunat'] if line['td_sunat'] else '',formats['especial1'])
				worksheet.write(x,2,line['nro_comprobante'] if line['nro_comprobante'] else '',formats['especial1'])
				worksheet.write(x,3,line['doc_partner'] if line['doc_partner'] else '',formats['especial1'])
				worksheet.write(x,4,line['fecha_doc'] if line['fecha_doc'] else '',formats['dateformat'])
				worksheet.write(x,5,line['fecha_ven'] if line['fecha_ven'] else '',formats['dateformat'])
				worksheet.write(x,6,line['saldo_mn'] if line['saldo_mn'] > 0 else 0,formats['numberdos'])
				worksheet.write(x,7,0 if line['saldo_mn'] > 0 else abs(line['saldo_mn']),formats['numberdos'])
				worksheet.write(x,8,account_id.currency_id.name if account_id.currency_id else '',formats['especial1'])
				worksheet.write(x,9,line['saldo_me'] if account_id.currency_id else 0,formats['numberdos'])
				worksheet.write(x,10,(abs(line['saldo_mn'])/abs(line['saldo_me']) if abs(line['saldo_me']) != 0 else 1) if account_id.currency_id else 1,formats['numberdos'])
				x += 1
			
			worksheet.write(x,0,account_id.code if account_id else '',formats['especial1'])
			worksheet.write(x,1,doc.code,formats['especial1'])
			worksheet.write(x,2,self.ref,formats['especial1'])
			worksheet.write(x,3,self.partner_id.name,formats['especial1'])
			worksheet.write(x,4,'',formats['dateformat'])
			worksheet.write(x,5,'',formats['dateformat'])
			worksheet.write(x,6,account['pasivo'],formats['numberdos'])
			worksheet.write(x,7,account['activo'],formats['numberdos'])
			worksheet.write(x,8,account_id.currency_id.name if account_id.currency_id else '',formats['especial1'])
			worksheet.write(x,9,(account['amount_currency'] *-1) if account_id.currency_id else 0,formats['numberdos'])
			worksheet.write(x,10,(abs(account['pasivo']-account['activo'])/abs(account['amount_currency']) if abs(account['amount_currency']) != 0 else 1) if account_id.currency_id else 1,formats['numberdos'])
			x += 1
		widths = [15,10,17,15,12,12,12,12,10,15,7]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		workbook.close()

		f = open(direccion +'Apertura_contable.xlsx', 'rb')
		return self.env['popup.it'].get_file('Preview - Apertura Contable.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def generate_opening(self):
		lines = []
		accounts = []
		#######PRIMER ASIENTO
		self.env.cr.execute("""select a.account_id,c.currency_id,
							case when sum(coalesce(a.balance,0))> 0 then sum(coalesce(a.balance,0)) else 0 end as activo,
							case when sum(coalesce(a.balance,0))< 0 then abs(sum(coalesce(a.balance,0))) else 0 end as pasivo,
							sum(coalesce(a.amount_currency,0)) as amount_currency
							from account_move_line a
							left join account_move b on b.id=a.move_id
							left join account_account c on c.id=a.account_id
							where b.date between '%s' and '%s' and b.company_id=%d and b.state='posted' and c.clasification_sheet='0' AND a.display_type IS NULL AND a.account_id IS NOT NULL
							group by a.account_id,c.currency_id
							having sum(coalesce(a.balance,0)) <> 0"""%(self.from_fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			self.from_fiscal_year_id.date_to.strftime('%Y/%m/%d'),
			self.company_id.id))

		res = self.env.cr.dictfetchall()

		doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
		sum_debit = sum_credit = 0

		for elem in res:
			account_id = self.env['account.account'].browse(elem['account_id'])
			if account_id.is_document_an:
				accounts.append(elem)
			vals = (0,0,{
				'account_id': account_id.id,
				'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'debit': elem['activo'],
				'credit': elem['pasivo'],
				'currency_id': account_id.currency_id.id if account_id.currency_id else None,
				'amount_currency': elem['amount_currency'] if account_id.currency_id else 0,
				'partner_id': self.partner_id.id if account_id.is_document_an else None,
				'type_document_id': doc.id if account_id.is_document_an else None,
				'nro_comp': self.ref if account_id.is_document_an else None,
				'company_id': self.company_id.id,
				'amount_residual':0,
				'amount_residual_currency':0,
				'reconciled': True,
				'tc': (abs(elem['activo'] - elem['pasivo'])/abs(elem['amount_currency']) if abs(elem['amount_currency']) != 0 else 0) if account_id.currency_id else 1,
			})
			sum_debit += elem['activo']
			sum_credit += elem['pasivo']
			lines.append(vals)
		
		if sum_debit > sum_credit:
			vals = (0,0,{
				'account_id': self.account_id.id,
				'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'debit': 0,
				'credit': sum_debit-sum_credit,
				'company_id': self.company_id.id,
				'amount_residual':0,
				'amount_residual_currency':0,
				'reconciled': True,
			})
			lines.append(vals)
		
		if sum_debit < sum_credit:
			vals = (0,0,{
				'account_id': self.account_id.id,
				'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'debit': sum_credit-sum_debit,
				'credit': 0,
				'company_id': self.company_id.id,
				'amount_residual':0,
				'amount_residual_currency':0,
				'reconciled': True,
			})
			lines.append(vals)
		
		move = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': self.journal_id.id,
				'date': self.to_fiscal_year_id.date_from,
				'line_ids':lines,
				'ref': 'APERTURA',
				'glosa': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'is_opening_close':True,
				'opening_id_it': self.id,
				'move_type':'entry'})
		
		move.action_post()

		for account in accounts:
			account_id = self.env['account.account'].browse(account['account_id'])

			self.env.cr.execute("""select a.partner_id,a.account_id,a.type_document_id,a.nro_comp as nro_comprobante,b.currency_id,sum(coalesce(a.balance,0)) as saldo_mn,
			sum(coalesce(a.amount_currency,0)) as saldo_me, min(a.date) as fecha_con, min(a.date_maturity) as fecha_ven from account_move_line a
			left join account_account b on b.id=a.account_id
			left join account_move c on c.id=a.move_id
			where (c.date between '%s' and '%s')  and c.state='posted' and b.is_document_an = True AND a.display_type IS NULL AND a.account_id = %d
			and a.company_id = %d 
			group by a.partner_id,a.account_id,a.type_document_id,a.nro_comp,b.currency_id
			having sum(coalesce(a.balance,0))<>0"""%(self.from_fiscal_year_id.date_from.strftime('%Y/%m/%d'),
																self.from_fiscal_year_id.date_to.strftime('%Y/%m/%d'),
																account_id.id,
																self.company_id.id))
			
			line_data = self.env.cr.dictfetchall()
			line_account = []
			for line in line_data:
				vals = (0,0,{
					'account_id': account_id.id,
					'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
					'debit': line['saldo_mn'] if line['saldo_mn'] > 0 else 0,
					'credit': 0 if line['saldo_mn'] > 0 else abs(line['saldo_mn']),
					'currency_id': account_id.currency_id.id if account_id.currency_id else None,
					'amount_currency': line['saldo_me'] if account_id.currency_id else 0,
					'partner_id': line['partner_id'],
					'type_document_id': line['type_document_id'],
					'nro_comp': line['nro_comprobante'],
					'company_id': self.company_id.id,
					'amount_residual':0,
					'amount_residual_currency':0,
					'reconciled': True,
					'date_maturity': line['fecha_ven'] if line['fecha_ven'] else None,
					'tc': (abs(line['saldo_mn'])/abs(line['saldo_me']) if abs(line['saldo_me']) != 0 else 1) if account_id.currency_id else 1,
				})
				line_account.append(vals)
			
			vals = (0,0,{
					'account_id': account_id.id,
					'name': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
					'debit': account['pasivo'],
					'credit': account['activo'],
					'currency_id': account_id.currency_id.id if account_id.currency_id else None,
					'amount_currency': (account['amount_currency'] *-1) if account_id.currency_id else 0,
					'partner_id': self.partner_id.id,
					'type_document_id': doc.id,
					'nro_comp': self.ref,
					'company_id': self.company_id.id,
					'amount_residual':0,
					'amount_residual_currency':0,
					'reconciled': True,
					'tc': (abs(account['pasivo']-account['activo'])/abs(account['amount_currency']) if abs(account['amount_currency']) != 0 else 1) if account_id.currency_id else 1,
				})
			line_account.append(vals)

			move_account = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': self.journal_id.id,
				'date': self.to_fiscal_year_id.date_from,
				'line_ids':line_account,
				'ref': 'APERTURA ' + account_id.code,
				'glosa': 'POR LOS SALDOS INICIALES AL APERTURAR EL EJERCICIO %s'%(self.to_fiscal_year_id.name),
				'is_opening_close':True,
				'opening_id_it': self.id,
				'payment_state': 'paid',
				'move_type':'entry'})
		
			move_account.action_post()

		self.move_ids.action_concile_special()

		self.state = 'done'

	def get_amount_currency_account(self,account_id):
		self.env.cr.execute("""SELECT sum(coalesce(aml.amount_currency,0)) as amount_currency from account_move_line aml
		left join account_move am on am.id = aml.move_id
		where aml.account_id = %d and am.state = 'posted' and aml.company_id = %d
		AND (CASE
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
				WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
				ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer BETWEEN '%s' AND '%s')"""%(account_id.id,self.company_id.id,self.from_fiscal_year_id.name + '00',self.from_fiscal_year_id.name+'12'))

		res = self.env.cr.dictfetchall()
		if len(res) > 0:
			amount_currency = res[0]['amount_currency'] if res[0]['amount_currency'] else 0
			return amount_currency
		else:
			return 0

	def cancel_opening(self):
		for move in self.move_ids:
			if move.state =='draft':
				pass
			else:
				move.button_cancel()
			move.line_ids.unlink()
			move.name = "/"
			move.unlink()

		self.state = 'draft'
	
	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)