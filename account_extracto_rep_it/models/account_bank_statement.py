# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def generate_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Extractos_Bancarios.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("EXTRACTOS BANCARIOS")
		worksheet.set_tab_color('blue')

		formats['numberdosespecial'].set_num_format('"%s" #,##0.00' % self.currency_id.symbol)
		formats['numberdos'].set_num_format('"%s" #,##0.00' % self.currency_id.symbol)

		if self.journal_id.type == 'bank':
			name_rep = 'EXTRACTO BANCARIO'
		elif self.journal_id.type == 'cash' and self.journal_check_surrender:
			name_rep ='RENDICIONES'
		else:
			name_rep ='CAJA CHICA'


		worksheet.merge_range(1,0,1,5, name_rep, formats['especial4'])

		worksheet.write(3,0, "Diario:", formats['especial2'])
		worksheet.write(4,0, "Fecha:", formats['especial2'])
		worksheet.write(3,2, "Saldo Inicial:", formats['especial2'])

		worksheet.write(3,1, self.journal_id.name, formats['especial4'])
		worksheet.write(4,1, self.date, formats['especialdate'])
		worksheet.write_number(3,3, self.balance_start , formats['numberdosespecial'])

		HEADERS = ['FECHA','DESCRIPCION','PARTNER','TD','REFERENCIA','MEDIO DE PAGO','MONTO','CONCILIADO']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,6,0,formats['boldbord'])

		x=7
		tot = 0

		for line in self.line_ids:
			worksheet.write(x,0,line.date if line.date else '',formats['dateformat'])
			worksheet.write(x,1,line.payment_ref if line.payment_ref else '',formats['especial1'])
			worksheet.write(x,2,line.partner_id.name if line.partner_id else '',formats['especial1'])
			worksheet.write(x,3,line.type_document_id.code if line.type_document_id else '',formats['especial1'])
			worksheet.write(x,4,line.ref if line.ref else '',formats['especial1'])
			worksheet.write(x,5,line.catalog_payment_id.code if line.catalog_payment_id else '',formats['especial1'])
			worksheet.write_number(x,6,line.amount if line.amount else '0.00',formats['numberdos'])
			worksheet.write(x,7,'SI' if line.is_reconciled else 'NO',formats['especial1'])
			tot += line.amount if line.amount else 0
			x += 1

		worksheet.write(x+1,1, 'SALDO', formats['especial5'])
		worksheet.write(x+1,6, tot+self.balance_start, formats['numberdosespecialbold'])

		widths = [10,50,46,10,23,20,15,18]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Extractos_Bancarios.xlsx', 'rb')

		return self.env['popup.it'].get_file('%s.xlsx'%(name_rep),base64.encodebytes(b''.join(f.readlines())))

