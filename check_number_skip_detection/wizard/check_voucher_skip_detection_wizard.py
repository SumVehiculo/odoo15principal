# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta

class CheckVoucherSkipDetectionWizard(models.TransientModel):
	_name = 'check.voucher.skip.detection.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string='Periodo')
	journal_id = fields.Many2one('account.journal',string='Diario')
	
	def get_report(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Consistencia.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO COMPRAS############
		worksheet = workbook.add_worksheet("Hoja 1")
		worksheet.set_tab_color('blue')

		HEADERS = ['NUMERO','DIARIO']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		res = self._get_print()
		x=1
		for line in res:
			worksheet.write(x,0,line[0],formats['especial1'])
			worksheet.write(x,1,line[1],formats['especial1'])
			x+=1

		widths = [20,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Consistencia.xlsx', 'rb')
		return self.env['popup.it'].get_file('Vouchers Faltantes.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_print(self):

		sql = """
			select right(am.name,6) as check_number, am.journal_id, aj.code from account_move am 
			left join account_journal aj on aj.id = am.journal_id 
			where aj.company_id = %d and (am.date between '%s' and '%s') and am.state = 'posted' and am.journal_id = %d
			order by am.journal_id , am.name
		""" % (self.company_id.id,
			self.period_id.date_start.strftime('%Y/%m/%d'),
			self.period_id.date_end.strftime('%Y/%m/%d'),
			self.journal_id.id)
		self.env.cr.execute(sql)
		c=0
		journal_id = None
		arr = []
		res = self.env.cr.dictfetchall()
		digits_number = '000000'
		for line in res:
			c+=1
			if not journal_id:
				journal_id = line['journal_id']
			if journal_id != line['journal_id']:
				journal_id = line['journal_id']
				c=1
			while int(line['check_number']) != c:
				numm = str(c)
				vou = self.period_id.date_start.strftime('%m') + '-' + digits_number[:-len(numm)] + numm
				arr.append([vou,line['code']])
				c += 1
		
		return arr
