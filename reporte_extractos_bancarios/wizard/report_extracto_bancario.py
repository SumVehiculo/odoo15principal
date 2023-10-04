from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta
from io import BytesIO
import re
import uuid

class report_extracto_bancario(models.TransientModel):
	_name = 'report.extracto.bancario'

	name = fields.Char()
	company_id = fields.Many2one(
		'res.company',
		string=u'Compañia',
		required=True, 
		default=lambda self: self.env.company,
		readonly=True
	)

	date_from = fields.Date(
		string=u'Fecha Inicial',
		
	)

	date_to = fields.Date(
		string=u'Fecha Final',
		
	)

	journal_id = fields.Many2one(
		'account.journal',
		string='Banco',
		domain="[('type','=','bank')]"
	)


	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Extrato_Bancario.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO VENTAS############
		worksheet = workbook.add_worksheet("EXTRACTO BANCARIO")
		worksheet.set_tab_color('blue')
		x=0
		
		worksheet.merge_range(x,0,x,12, "EXTRACTO BANCARIO", formats['especial5'] )
		x+=2
		worksheet.write(x,0,u"Diario:",formats['especial2'])
		worksheet.merge_range(x,1,x,12,self.journal_id.name,formats['especial2'])
		x+=1
		worksheet.write(x,0,"Fecha Inicial:",formats['especial2'])
		worksheet.merge_range(x,1,x,2,str(self.date_from.strftime('%Y/%m/%d')),formats['especial2'])
		
		worksheet.write(x,3,"Fecha Final:",formats['especial2'])
		worksheet.merge_range(x,4,x,5,str(self.date_to.strftime('%Y/%m/%d')),formats['especial2'])
		x+=1
		worksheet.write(x,0,"Saldo Inicial:",formats['especial2'])
		worksheet.write(x,3,"Saldo Final:",formats['especial2'])
		x+=2
		
		worksheet = ReportBase.get_headers(worksheet,self.get_header(),x,0,formats['boldbord'])
		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()
		c = 1
		x+=1

		#DECLARANDO TOTALES
		#exp, venta_g, inaf, exo, isc_v, otros_v, icbper, igv_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0
		saldo_i = 0
		saldo_f = 0
		cont_id = 0
		for line in res:
			
			if cont_id == 0:
				saldo_i = line['balance_start']
			else:
				saldo_f = line['balance_end_real']
			
			worksheet.write(x,0,line['date'] if line['date'] else '',formats['dateformat'])
			worksheet.write(x,1,line['payment_ref'] if line['payment_ref'] else '',formats['especial1'])
			worksheet.write(x,2,line['partner_id'] if line['partner_id'] else '',formats['especial1'])
			worksheet.write(x,3,line['type_document_id'] if line['type_document_id'] else '',formats['especial1'])
			worksheet.write(x,4,line['ref'] if line['ref'] else '',formats['especial1'])
			worksheet.write(x,5,line['catalog_payment_id'] if line['catalog_payment_id'] else '',formats['especial1'])
			worksheet.write(x,6,line['amount'] if line['amount'] else '0.00',formats['numberdos'])
			worksheet.write(x,7,'SI' if line['is_reconciled'] else 'NO',formats['especial1'])
					
			#tot += line.amount if line.amount else 0
			x += 1
			cont_id +=1

		worksheet.write(4,1,str(saldo_i),formats['numberdosespecial'])
		worksheet.write(4,4,str(saldo_f),formats['numberdosespecial'])
		
		
		widths = [10,50,46,10,23,20,15,18]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Extrato_Bancario.xlsx', 'rb')
		return self.env['popup.it'].get_file('Extrato_Bancario.xlsx',base64.encodebytes(b''.join(f.readlines())))

	

	def get_header(self):
	
		HEADERS = ['FECHA','DESCRIPCIÓN','PARTNER','TD','REFERENCIA','MEDIO DE PAGO','MONTO','CONCILIADO']
	
		return HEADERS


	def _get_sql(self):
		
		sql = """SELECT am.date,
						abs.balance_start,
						abs.balance_end_real,  
						absl.payment_ref, 
						rp.name as partner_id, 
						ldt.code as type_document_id,
						am.ref, 
						ecp.name as catalog_payment_id,
						absl.amount, 
						absl.is_reconciled
					FROM account_bank_statement_line as absl
					LEFT JOIN res_partner rp ON rp.id = absl.partner_id
					LEFT JOIN l10n_latam_document_type ldt ON ldt.id = absl.type_document_id
					LEFT JOIN einvoice_catalog_payment ecp ON ecp.id = absl.catalog_payment_id
					LEFT JOIN account_bank_statement abs ON abs.id = absl.statement_id
					LEFT JOIN account_move am ON am.id = absl.move_id
					WHERE (am.date BETWEEN '%s' AND '%s')
							AND abs.company_id = %d
							AND abs.journal_id = %d
				""" % (	self.date_from.strftime('%Y/%m/%d'),
						self.date_to.strftime('%Y/%m/%d'),
						self.company_id.id,
						self.journal_id.id)
		
		return sql
