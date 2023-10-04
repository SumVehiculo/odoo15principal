# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta

class CheckVoucherSkipDetection2Wizard(models.TransientModel):
	_name = 'check.voucher.skip.detection2.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string='Periodo')
	
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
			worksheet.write(x,0,line['voucher_faltante'],formats['especial1'])
			worksheet.write(x,1,line['diario'],formats['especial1'])
			x+=1

		widths = [20,80]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Consistencia.xlsx', 'rb')
		return self.env['popup.it'].get_file('Vouchers Faltantes segun Numeracion.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_print(self):

		sql = """
			select diario,voucher as voucher_faltante from (
			select b1.diario,right(b1.voucher,9) as voucher ,b2.nombre from (
			select a2.name as diario ,a2.code||'-'||lpad(extract(month from a1.date)::varchar,2,'0') || '-' ||lpad(row_number() over (partition by a1.journal_id)::varchar,6,'0') as voucher
			from account_move a1
			left join account_journal a2 on a2.id=a1.journal_id
			where (date between '%s' and '%s') and a1.company_id = %d)b1 
			left join (select a2.code||'-'||a1.name as nombre from account_move a1 
			left join account_journal a2 on a2.id=a1.journal_id) b2 on b2.nombre=b1.voucher
			where b2.nombre is  null 
			order by  b1.diario,b1.voucher)c
		""" % (
			self.period_id.date_start.strftime('%Y/%m/%d'),
			self.period_id.date_end.strftime('%Y/%m/%d'),
			self.company_id.id)
		self.env.cr.execute(sql)
		res = self.env.cr.dictfetchall()
		return res
