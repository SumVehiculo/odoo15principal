# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
_logger = logging.getLogger(__name__)


class TemplateSaleFinanceWizard(models.TransientModel):
	_name = 'template.sale.finance.wizard'
	_description = _('TemplateSaleFinanceWizard')

	name = fields.Char(_('Nombre'), default="Reporte Ventas Financieras")
	
	date_start = fields.Date(
		string=_('Fecha Inicio'),
		default=lambda self: fields.Date.context_today(self).replace(month=1, day=1),
		required=True
	)
	date_end = fields.Date(
		string=_('Fecha Fin'),
		default=fields.Date.context_today,
		required=True, 
	)
	
	company_id = fields.Many2one(
		string=_('Company'), 
		comodel_name='res.company', 
		required=True, 
		default=lambda self: self.env.company,
		readonly=True
	)

	type_show = fields.Selection(
		string=_('Mostrar en'),
		selection=[
			('screen', 'Pantalla'),
			('excel', 'Excel'),
		],
		default='screen',
		required=True
	)
	
	def get_report(self):
		for record in self:
			if record.type_show == 'screen':
				return self.get_screen()
			else:
				return self.get_excel()

	def get_screen(self):
		self._cr.execute("""DROP VIEW IF EXISTS template_sale_finance CASCADE;
				CREATE OR REPLACE VIEW template_sale_finance AS 
				(SELECT row_number() OVER () AS id, * FROM (%s)T)"""%(self._get_sql()))
		return {
				'name': 'VENTAS FINANCIADAS',
				'type': 'ir.actions.act_window',
				'res_model': 'template.sale.finance',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}


	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'plantilla_ventas_financiadas.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("VENTAS FINANCIADAS")
		worksheet.set_tab_color('blue')

		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,12, "PLANTILLA DE VENTAS FINANCIADAS", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,12,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_start.strftime('%Y/%m/%d')),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_end.strftime('%Y/%m/%d')),formats['especial2'])
			x+=2
		
		worksheet = ReportBase.get_headers(worksheet,self.get_header(),x,0,formats['boldbord'])
		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()
		x+=1
		for line in res:
			worksheet.write(x,0,line['account'] if line['account'] else '',formats['especial1'])
			worksheet.write(x,1,line['debit'] if line['debit'] else '',formats['numberdos'])
			worksheet.write(x,2,line['credit'] if line['credit'] else '',formats['numberdos'])
			worksheet.write(x,3,line['currency'] if line['currency'] else '',formats['especial1'])
			worksheet.write(x,4,line['amount_currency'] if line['amount_currency'] else '',formats['numberdos'])
			worksheet.write(x,5,line['tc'] if line['tc'] else '',formats['numberdos'])
			worksheet.write(x,6,line['partner'] if line['partner'] else '',formats['especial1'])
			worksheet.write(x,7,line['td'] if line['td'] else '',formats['especial1'])
			worksheet.write(x,8,line['nro_comp'] if line['nro_comp'] else '',formats['especial1'])
			worksheet.write(x,9,line['date'] if line['date'] else '',formats['dateformat'])
			worksheet.write(x,10,line['date_sale'] if line['date_sale'] else '',formats['dateformat'])
			worksheet.write(x,11,line['cta_analytic'] if line['cta_analytic'] else '',formats['especial1'])
			worksheet.write(x,12,line['analytic_tags'] if line['analytic_tags'] else '0.0000',formats['especial1'])
			x += 1
		

		widths = [15,12,12,10,12,6,15,6,15,12,12,20,25]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'plantilla_ventas_financiadas.xlsx', 'rb')

		return self.env['popup.it'].get_file('Plantilla Ventas Financiadas.xlsx',base64.encodebytes(b''.join(f.readlines())))
	
	def get_header(self):
		HEADERS = ['CUENTA','DEBITO','CREDITO','MONEDA','IMPORTE MONEDA','TC','CLIENTE','TD','NRO COMP','FECHA DOC','FECHA DEL PEDIDO','CUENTA ANALITICA','ETIQUETAS ANALITICAS']
		return HEADERS
	
	def _get_sql(self):
		sql = """
			SELECT aa.code AS account,
				sum(aml.debit) as debit,
				sum(aml.credit) as credit,
				rc.name as currency,
				sum(abs(aml.amount_currency)) as amount_currency,
				aml.tc,
				rp.vat as partner,
				ec1.code AS td,
				aml.nro_comp,
				am.date as date,
				so.date_order as sale_date,
				ana.name as cta_analytic,
				aat_rel.analytic_tags as analytic_tags
			FROM sale_order_line_invoice_rel sol_aml
			LEFT JOIN account_move_line aml ON aml.id = sol_aml.invoice_line_id
			LEFT JOIN account_account aa ON aa.id = aml.account_id
			LEFT JOIN account_move am ON am.id = aml.move_id
			LEFT JOIN res_partner rp ON rp.id = aml.partner_id
			LEFT JOIN res_currency rc ON rc.id = am.currency_id
			LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = aml.type_document_id
			LEFT JOIN sale_order_line sol ON sol.id = sol_aml.order_line_id
			LEFT JOIN sale_order so ON so.id = sol.order_id
			LEFT JOIN account_analytic_account ana ON ana.id = aml.analytic_account_id
			LEFT JOIN
			(SELECT aml.id AS id,
					array_to_string(ARRAY_AGG(aat.name), ', ') AS analytic_tags
			FROM account_analytic_tag_account_move_line_rel AS aataml_rel
			LEFT JOIN account_analytic_tag AS aat ON aat.id = aataml_rel.account_analytic_tag_id
			LEFT JOIN account_move_line AS aml ON aml.id = aataml_rel.account_move_line_id
			GROUP BY aml.id) AS aat_rel ON aat_rel.id = aml.id
			WHERE am.state='posted'
			AND aml.account_id is not null
			AND am.company_id = %d
			AND (am.date between '%s' and '%s') 
			GROUP BY aa.code, rc.name, rp.vat, ec1.code, aml.nro_comp, am.date, so.date_order, ana.name, aat_rel.analytic_tags, aml.tc
			"""%(
				self.company_id.id,
				self.date_start.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				)
		return sql