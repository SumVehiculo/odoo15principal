# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid

class AccountClosingIt(models.Model):
	_name = 'account.closing.it'
	_description = 'Account Closing IT'

	@api.depends('fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = i.fiscal_year_id.name

	name = fields.Char(compute=_get_name,store=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',required=True)
	period = fields.Many2one('account.period',string='Periodo Cierre',required=True)
	journal_id = fields.Many2one('account.journal',string='Diario Cierre',required=True)
	state = fields.Selection([('draft','BORRADOR'),
							('0','BALANCE COMPROBACION'),
							('1','COSTO DE VENTAS'),
							('2',u'CIERRE CLASE 9'),
							('3','CIERRE CUENTAS RESULTADOS'),
							('4','CIERRE ACTIVO Y PASIVO')],string='Estado',default='draft')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	account_move_id = fields.Many2one('account.move',string='Asiento de Cierre')
	asiento_1 = fields.Many2one('account.move',string='Asiento Costo de Ventas')
	asiento_2 = fields.Many2one('account.move',string='Asiento Cancelacion Clase 9')
	asiento_3 = fields.Many2one('account.move',string='Asiento Cancelacion Ingresos y Gastos')
	asiento_4 = fields.Many2one('account.move',string='Asiento Traslado a Resultados Acumulados')
	asiento_5 = fields.Many2one('account.move',string='Asiento Cancelacion Activo y Pasivo')

	diff_res = fields.Float(string='Diferencia Asiento Resultados',digits=(12,2))
	diff_ap = fields.Float(string='Diferencia Asiento AyP',digits=(12,2))

	@api.model
	def _create_savepoint(self):
		rollback_name = '%s_%s' % (
			self._name.replace('.', '_'), uuid.uuid1().hex)
		req = "SAVEPOINT %s" % (rollback_name)
		self.env.cr.execute(req)
		return rollback_name

	@api.model
	def _rollback_savepoint(self, rollback_name):
		req = "ROLLBACK TO SAVEPOINT %s" % (rollback_name)
		self.env.cr.execute(req)

	def unlink(self):
		if self.account_move_id:
			raise UserError("No se puede eliminar un Cierre Contable si tiene asiento.")
		return super(AccountClosingIt,self).unlink()
	
	def preview_closing(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Cierre_contable.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("ASIENTO PRINCIPAL")
		worksheet.set_tab_color('blue')

		HEADERS = ['CUENTA','DEBE','HABER','MONEDA','IMPORTE EN MONEDA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		lines = []
		self.cierre_contable_0()
		lines += self.cierre_contable_1()
		lines += self.cierre_contable_2()
		lines += self.cierre_contable_3()
		lines += self.cierre_contable_4()

		for line in lines:
			account_id = self.env['account.account'].browse(line[2]['account_id'])
			worksheet.write(x,0,account_id.code if account_id else '',formats['especial1'])
			worksheet.write(x,1,line[2]['debit'] if line[2]['debit'] else 0,formats['numberdos'])
			worksheet.write(x,2,line[2]['credit'] if line[2]['credit'] else 0,formats['numberdos'])
			worksheet.write(x,3,account_id.currency_id.name if account_id.currency_id else '',formats['especial1'])
			worksheet.write(x,4,0,formats['numberdos'])
			x+=1
		
		widths = [15,12,12,10,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		workbook.close()

		f = open(direccion +'Cierre_contable.xlsx', 'rb')
		return self.env['popup.it'].get_file('Preview - Cierre Contable.xlsx',base64.encodebytes(b''.join(f.readlines())))

	'''
	def cancelar(self):
		if self.state == '0':
			self.env.cr.execute("""DELETE FROM cierre_contable_view WHERE cierre_id = %s"""%(str(self.id)))
			self.state = 'draft'

		if self.state == '1':
			if self.asiento_1.id:
				self.asiento_1.button_cancel()
				self.asiento_1.line_ids.unlink()
				self.asiento_1.name = "/"
				self.asiento_1.unlink()
			self.env.cr.execute("""UPDATE cierre_contable_view SET debit_costo = 0, credit_costo = 0, deudor = 0, acreedor = 0 WHERE cierre_id = %s"""%(str(self.id)))
			self.state = '0'

		elif self.state == '2':
			if self.asiento_2.id:
				self.asiento_2.button_cancel()
				self.asiento_2.line_ids.unlink()
				self.asiento_2.name = "/"
				self.asiento_2.unlink()
			self.env.cr.execute("""UPDATE cierre_contable_view SET debit_clase9 = 0, credit_clase9 = 0 WHERE cierre_id = %s"""%(str(self.id)))
			self.state = '1'

		elif self.state == '3':
			if self.asiento_3.id:
				self.asiento_3.button_cancel()
				self.asiento_3.line_ids.unlink()
				self.asiento_3.name = "/"
				self.asiento_3.unlink()
			if self.asiento_4.id:
				self.asiento_4.button_cancel()
				self.asiento_4.line_ids.unlink()
				self.asiento_4.name = "/"
				self.asiento_4.unlink()
			self.diff_res = 0
			self.env.cr.execute("""UPDATE cierre_contable_view SET debit_resultado = 0, credit_resultado = 0 WHERE cierre_id = %s"""%(str(self.id)))
			self.state = '2'

		elif self.state == '4':
			if self.asiento_5.id:
				self.asiento_5.button_cancel()
				self.asiento_5.line_ids.unlink()
				self.asiento_5.name = "/"
				self.asiento_5.unlink()
			self.diff_ap = 0
			self.env.cr.execute("""UPDATE cierre_contable_view SET debit_ap = 0, credit_ap = 0 WHERE cierre_id = %s"""%(str(self.id)))
			self.state = '3'
	'''

	def cierre_contable_oficial(self):
		if self.account_move_id:
			raise UserError('Ya existe un Asiento de Cierre.')
		
		lines = []
		self.cierre_contable_0()
		lines += self.cierre_contable_1()
		lines += self.cierre_contable_2()
		lines += self.cierre_contable_3()
		lines += self.cierre_contable_4()

		if len(lines)>0:
			move_id = self.env['account.move'].create({
				'company_id': self.company_id.id,
				'journal_id': self.journal_id.id,
				'date': self.fiscal_year_id.date_to,
				'line_ids':lines,
				'ref': 'CIERRE - '+self.fiscal_year_id.name,
				'glosa': 'ASIENTO DE CIERRE - %s'%(self.fiscal_year_id.name),
				'is_opening_close':True,
				'move_type':'entry'})
			move_id.post()
			self.account_move_id = move_id.id
			return self.env['popup.it'].get_message(u'Se generó correctamente el asiento de cierre.')	
		else:
			return self.env['popup.it'].get_message(u'Probablemente este intentando generar un asiento vacío.')	

	def cierre_contable_0(self):
		self.env.cr.execute(""" 
			CREATE TABLE IF NOT EXISTS cierre_contable_view (
				id serial PRIMARY KEY,
				cierre_id integer,
				m_close varchar(3),
				account_id integer,
				debit numeric (12, 2),
				credit numeric (12, 2),
				saldo_deudor numeric (12, 2),
				saldo_acreedor numeric (12, 2),
				debit_costo numeric (12, 2),
				credit_costo numeric (12, 2),
				deudor numeric (12, 2),
				acreedor numeric (12, 2),
				debit_resultado numeric (12, 2),
				credit_resultado numeric (12, 2),
				debit_clase9 numeric (12, 2),
				credit_clase9 numeric (12, 2),
				debit_ap numeric (12, 2),
				credit_ap numeric (12, 2)
				);""")
		'''
		self.env.cr.execute("""SELECT DISTINCT G.code 
								FROM
								(SELECT 
								aa.code
								FROM 
								(SELECT account_id
								FROM vst_diariog
								WHERE periodo::int between '%s'::int and '%s'::int
								AND account_id is not null
								AND company_id = %s
								GROUP BY account_id)T
								LEFT JOIN account_account aa ON aa.id = T.account_id
								WHERE aa.m_close is null
								union all
								SELECT
								aa2.code
								FROM
								(SELECT account_id
								FROM vst_diariog
								WHERE periodo::int between '%s'::int and '%s'::int
								AND account_id is not null
								AND company_id = %s
								GROUP BY account_id)T
								LEFT JOIN account_account aa ON aa.id = T.account_id
								LEFT JOIN account_account aa2 ON aa2.id = aa.account_close_id
								WHERE aa.m_close = '1' AND aa2.m_close is null)G
							""" % (str(self.fiscal_year_id.name)+'00',
			str(self.fiscal_year_id.name)+'12',
			str(self.company_id.id),
			str(self.fiscal_year_id.name)+'00',
			str(self.fiscal_year_id.name)+'12',
			str(self.company_id.id)))

		acc = self.env.cr.dictfetchall()
		
		if len(acc) > 0:
			docname = 'Cuentas sin cierre.csv'

			#Get CSV
			sql_query = """SELECT DISTINCT G.code 
								FROM
								(SELECT 
								aa.code
								FROM 
								(SELECT account_id
								FROM vst_diariog
								WHERE periodo::int between '%s'::int and '%s'::int
								AND account_id is not null
								AND company_id = %d
								GROUP BY account_id)T
								LEFT JOIN account_account aa ON aa.id = T.account_id
								WHERE aa.m_close is null
								union all
								SELECT
								aa2.code
								FROM
								(SELECT account_id
								FROM vst_diariog
								WHERE periodo::int between '%s'::int and '%s'::int
								AND account_id is not null
								AND company_id = %d
								GROUP BY account_id)T
								LEFT JOIN account_account aa ON aa.id = T.account_id
								LEFT JOIN account_account aa2 ON aa2.id = aa.account_close_id
								WHERE aa.m_close = '1' AND aa2.m_close is null)G	
							""" % (str(self.fiscal_year_id.name)+'00',
			self.fiscal_year_id.name+'12',
			self.company_id.id,
			self.fiscal_year_id.name+'00',
			self.fiscal_year_id.name+'12',
			self.company_id.id)

			self.env.cr.execute(sql_query)
			sql_query = "COPY (%s) TO STDOUT WITH %s" % (sql_query, "CSV DELIMITER ','")
			rollback_name = self._create_savepoint()

			try:
				output = BytesIO()
				self.env.cr.copy_expert(sql_query, output)
				res = base64.b64encode(output.getvalue())
				output.close()
			finally:
				self._rollback_savepoint(rollback_name)

			res = res.decode('utf-8')

			return self.env['popup.it'].get_file(docname,res)
		'''
		self.env.cr.execute("""DELETE FROM cierre_contable_view WHERE cierre_id = %s"""%(str(self.id)))
		self.env.cr.execute(""" 
			INSERT INTO cierre_contable_view (cierre_id, m_close,account_id,debit,credit,saldo_deudor,saldo_acreedor,debit_costo,credit_costo,deudor,acreedor,debit_resultado,credit_resultado,debit_clase9,credit_clase9,debit_ap,credit_ap)
			select
			%s as cierre_id,
			aa.m_close,
			T.account_id,
			T.debit,
			T.credit,
			T.saldo_deudor,
			T.saldo_acreedor,
			0 as debit_costo,
			0 as credit_costo,
			0 as deudor,
			0 as acreedor,
			0 as debit_resultado,
			0 as credit_resultado,
			0 as debit_clase9,
			0 as credit_clase9,
			0 as debit_ap,
			0 as credit_ap from 
			(select account_id,sum(debe) as debit,sum(haber)as credit,
			case when sum(debe-haber)>0 then sum(debe-haber) else 0 end as saldo_deudor,
			case when sum(haber-debe)>0 then sum(haber-debe) else 0 end as saldo_acreedor
			from get_diariog('%s','%s',%d)
			where account_id is not null
			group by account_id)T
			LEFT JOIN account_account aa ON aa.id = T.account_id;
			""" % (str(self.id),
			self.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			self.fiscal_year_id.date_to.strftime('%Y/%m/%d'),
			self.company_id.id))

		#SI LAS CUENTAS DE CIERRE NO EXISTEN EN NUESTRA TABLA SE INSERTAN
		self.env.cr.execute("""SELECT
			aa.account_close_id,
			aa2.m_close
			FROM cierre_contable_view cc 
			LEFT JOIN account_account aa ON aa.id = cc.account_id
			LEFT JOIN account_account aa2 ON aa2.id = aa.account_close_id
			WHERE cc.cierre_id = %s AND
			cc.m_close = '1' AND
			aa.account_close_id is not null""" % (str(self.id)))
		acc = self.env.cr.dictfetchall()
		
		if len(acc) > 0:
			for elemnt in acc:
				self.env.cr.execute("""SELECT * FROM cierre_contable_view WHERE account_id = %s""" % (str(elemnt['account_close_id'])))
				exists = self.env.cr.dictfetchall()
				if len(exists) <= 0:
					self.env.cr.execute("""INSERT INTO cierre_contable_view (cierre_id, m_close,account_id,debit,credit,saldo_deudor,saldo_acreedor,debit_costo,credit_costo,deudor,acreedor,debit_resultado,credit_resultado,debit_clase9,credit_clase9,debit_ap,credit_ap)
					VALUES
					(%s,'%s',%s,0,0,0,0,0,0,0,0,0,0,0,0,0,0);""" % (str(self.id),str(elemnt['m_close']),str(elemnt['account_close_id'])))

		########
		return True

	def cierre_contable_1(self):
		self.env.cr.execute("""UPDATE cierre_contable_view SET debit_costo = saldo_acreedor, credit_costo = saldo_deudor WHERE m_close = '1' AND cierre_id = %s""" % (str(self.id)))

		self.env.cr.execute("""SELECT
								aa.account_close_id,
								sum(cc.saldo_deudor) as saldo_deudor,
								sum(cc.saldo_acreedor) as saldo_acreedor 
								FROM cierre_contable_view cc 
								LEFT JOIN account_account aa ON aa.id = cc.account_id
								WHERE cc.cierre_id = %s AND
								cc.m_close = '1' AND
								aa.account_close_id is not null 
								group by aa.account_close_id""" % (str(self.id)))

		res = self.env.cr.dictfetchall()
		if len(res) > 0:
			for line in res:
				self.env.cr.execute("""UPDATE cierre_contable_view SET debit_costo = %s, credit_costo = %s WHERE cierre_id = %s AND account_id = %s""" % (str(line['saldo_deudor']),str(line['saldo_acreedor']),str(self.id),str(line['account_close_id'])))

		self.env.cr.execute("""SELECT id,account_id,saldo_deudor,saldo_acreedor,debit_costo,credit_costo FROM cierre_contable_view WHERE cierre_id = %s""" % (str(self.id)))
		data = self.env.cr.dictfetchall()
		if len(data) > 0:
			for line in data:
				deudor = 0
				acreedor = 0
				amount_logic = (line['saldo_deudor']+line['debit_costo'])-(line['saldo_acreedor']+line['credit_costo'])
				if amount_logic != 0:
					deudor = amount_logic if amount_logic > 0 else 0
					acreedor = 0 if amount_logic > 0 else abs(amount_logic)
				self.env.cr.execute("""UPDATE cierre_contable_view SET deudor = %s, acreedor = %s WHERE cierre_id = %s AND account_id = %s AND id =%s"""%(str(deudor),str(acreedor),str(self.id),str(line['account_id']),str(line['id'])))

		self.env.cr.execute("""SELECT account_id,debit_costo,credit_costo FROM cierre_contable_view WHERE cierre_id = %s
							AND (debit_costo <> 0 OR credit_costo <> 0)""" % (str(self.id)))

		tabla = self.env.cr.dictfetchall()
		lineas = []
		for line in tabla:
			vals = (0,0,{
				'account_id': line['account_id'],
				'name': 'ASIENTO DE CIERRE',
				'debit': line['debit_costo'],
				'credit': line['credit_costo'],
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		return lineas
		#if len(lineas)>0:
		#	move_id = self.env['account.move'].create({
		#		'company_id': self.company_id.id,
		#		'journal_id': self.journal_id.id,
		#		'date': self.fiscal_year_id.date_to,
		#		'line_ids':lineas,
		#		'ref': 'CIERRE-'+self.fiscal_year_id.name,
		#		'glosa': 'CANCELACION DEL COSTO DE VENTAS',
		#		'is_opening_close':True,
		#		'type':'entry'})
		#	move_id.post()
			#self.asiento_1 = move_id.id
		#self.state = '1'

	def cierre_contable_2(self):
		self.env.cr.execute("""UPDATE cierre_contable_view SET debit_clase9 = acreedor, credit_clase9 = deudor WHERE m_close = '2' AND cierre_id = %s""" % (str(self.id)))
		self.env.cr.execute("""SELECT account_id,debit_clase9,credit_clase9 FROM cierre_contable_view WHERE cierre_id = %s
							AND (debit_clase9 <> 0 OR credit_clase9 <> 0)""" % (str(self.id)))

		tabla = self.env.cr.dictfetchall()
		lineas = []
		for line in tabla:
			vals = (0,0,{
				'account_id': line['account_id'],
				'name': 'ASIENTO DE CIERRE',
				'debit': line['debit_clase9'],
				'credit': line['credit_clase9'],
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		return lineas
		#if len(lineas)>0:
		#	move_id = self.env['account.move'].create({
		#		'company_id': self.company_id.id,
		#		'journal_id': self.journal_id.id,
		#		'date': self.fiscal_year_id.date_to,
		#		'line_ids':lineas,
		#		'ref': 'CIERRE-'+self.fiscal_year_id.name,
		#		'glosa': 'CANCELACION DE CLASE 9',
		#		'is_opening_close':True,
		#		'type':'entry'})
		#	move_id.post()
		#	self.asiento_2 = move_id.id
		#self.state = '2'

	def cierre_contable_3(self):
		self.env.cr.execute("""UPDATE cierre_contable_view SET debit_resultado = acreedor, credit_resultado = deudor WHERE m_close = '3' AND cierre_id = %s""" % (str(self.id)))
		self.env.cr.execute("""SELECT account_id,debit_resultado,credit_resultado FROM cierre_contable_view WHERE cierre_id = %s
							AND (debit_resultado <> 0 OR credit_resultado <> 0)""" % (str(self.id)))

		tabla = self.env.cr.dictfetchall()
		lineas = []
		sum_debit = 0
		sum_credit = 0
		for line in tabla:
			vals = (0,0,{
				'account_id': line['account_id'],
				'name': 'ASIENTO DE CIERRE',
				'debit': line['debit_resultado'],
				'credit': line['credit_resultado'],
				'company_id': self.company_id.id,
			})
			sum_debit+=line['debit_resultado']
			sum_credit+=line['credit_resultado']
			lineas.append(vals)

		balance_sheet_account = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).balance_sheet_account
		profit_result_account = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).profit_result_account
		if not balance_sheet_account:
			raise UserError(u'No existe Cuenta Cierre Contable Utilidad en Parametros Principales de Contabilidad para su Compañía')
		if not profit_result_account:
			raise UserError(u'No existe Cuenta Resultados A.C. Ganancia en Parametros Principales de Contabilidad para su Compañía')

		lost_sheet_account = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).lost_sheet_account
		lost_result_account = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).lost_result_account
		if not lost_sheet_account:
			raise UserError(u'No existe Cuenta Cierre Contable Perdida en Parametros Principales de Contabilidad para su Compañía')
		if not lost_result_account:
			raise UserError(u'No existe Cuenta Resultados A.C. Perdida en Parametros Principales de Contabilidad para su Compañía')
		if (sum_debit - sum_credit) != 0:
			vals = (0,0,{
				'account_id': balance_sheet_account.id if (sum_debit - sum_credit) > 0 else lost_sheet_account.id,
				'name': 'ASIENTO DE CIERRE',
				'debit': 0 if (sum_debit - sum_credit) > 0 else abs(sum_debit - sum_credit),
				'credit': (sum_debit - sum_credit) if (sum_debit - sum_credit) > 0 else 0,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)

		#if len(lineas)>0:
		#	move_id = self.env['account.move'].create({
		#		'company_id': self.company_id.id,
		#		'journal_id': self.journal_id.id,
		#		'date': self.fiscal_year_id.date_to,
		#		'line_ids':lineas,
		#		'ref': 'CIERRE-'+self.fiscal_year_id.name,
		#		'glosa': 'CANCELACION INGRESOS Y GASTOS',
		#		'is_opening_close':True,
		#		'type':'entry'})
		#	move_id.post()
		#	self.asiento_3 = move_id.id

		###TRASLADO A RESULTADOS ACUMULADOS
		#lineas_profit = []
		if (sum_debit - sum_credit) != 0:
			vals_prof = (0,0,{
				'account_id': balance_sheet_account.id if (sum_debit - sum_credit) > 0 else lost_sheet_account.id,
				'name': 'ASIENTO DE CIERRE',
				'debit': (sum_debit - sum_credit) if (sum_debit - sum_credit) > 0 else 0,
				'credit': 0 if (sum_debit - sum_credit) > 0 else abs(sum_debit - sum_credit),
				'company_id': self.company_id.id,
			})
			lineas.append(vals_prof)
			vals_prof = (0,0,{
				'account_id': profit_result_account.id if (sum_debit - sum_credit) > 0 else lost_result_account.id,
				'name': 'ASIENTO DE CIERRE',
				'debit': 0 if (sum_debit - sum_credit) > 0 else abs(sum_debit - sum_credit),
				'credit': (sum_debit - sum_credit) if (sum_debit - sum_credit) > 0 else 0,
				'company_id': self.company_id.id,
			})
			lineas.append(vals_prof)
		self.diff_res = sum_debit - sum_credit
		return lineas
		#if len(lineas_profit)>0:
		#	move_id_profit = self.env['account.move'].create({
		#		'company_id': self.company_id.id,
		#		'journal_id': self.journal_id.id,
		#		'date': self.fiscal_year_id.date_to,
		#		'line_ids':lineas_profit,
		#		'ref': 'CIERRE-'+self.fiscal_year_id.name,
		#		'glosa': 'TRASLADO A RESULTADOS ACUMULADOS',
		#		'is_opening_close':True,
		#		'type':'entry'})
		#	
		#	move_id_profit.post()
		#	self.asiento_4 = move_id_profit.id
		#self.state = '3'

	def cierre_contable_4(self):
		self.env.cr.execute("""UPDATE cierre_contable_view SET debit_ap = acreedor, credit_ap = deudor WHERE m_close = '4' AND cierre_id = %s""" % (str(self.id)))
		self.env.cr.execute("""SELECT ccv.account_id,rc.name AS currency,aa.currency_id,ccv.debit_ap,ccv.credit_ap FROM cierre_contable_view ccv 
								LEFT JOIN account_account aa ON aa.id = ccv.account_id
								LEFT JOIN res_currency rc On rc.id = aa.currency_id
								WHERE ccv.cierre_id = %s AND (ccv.debit_ap <> 0 OR ccv.credit_ap <> 0)""" % (str(self.id)))

		tabla = self.env.cr.dictfetchall()
		lineas = []
		sum_debit = 0
		sum_credit = 0
		for line in tabla:
			vals = (0,0,{
				'account_id': line['account_id'],
				'name': 'ASIENTO DE CIERRE',
				'currency_id': line['currency_id'] if line['currency'] == 'USD' else None,
				'amount_currency': 0 if line['currency'] == 'USD' else None,
				'debit': line['debit_ap'],
				'credit': line['credit_ap'],
				'company_id': self.company_id.id,
			})
			sum_debit += line['debit_ap']
			sum_credit += line['credit_ap']
			lineas.append(vals)

		if abs(sum_debit - sum_credit) > 0:
			profit_result_account = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).profit_result_account
			lost_result_account = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).lost_result_account
			vals = (0,0,{
				'account_id': profit_result_account.id if (sum_debit - sum_credit) < 0 else lost_result_account.id,
				'name': 'ASIENTO DE CIERRE',
				'debit': abs(sum_debit - sum_credit) if (sum_debit - sum_credit) < 0 else 0,
				'credit': 0 if (sum_debit - sum_credit) < 0 else abs(sum_debit - sum_credit),
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
		self.diff_ap = sum_debit - sum_credit
		return lineas
		#if len(lineas)>0:
		#	move_id = self.env['account.move'].create({
		#		'company_id': self.company_id.id,
		#		'journal_id': self.journal_id.id,
		#		'date': self.fiscal_year_id.date_to,
		#		'line_ids':lineas,
		#		'ref': 'CIERRE-'+self.fiscal_year_id.name,
		#		'glosa': 'CANCELACION ACTIVO Y PASIVO',
		#		'is_opening_close':True,
		#		'type':'entry'})
		#	move_id.post()
		#	self.asiento_5 = move_id.id
		#self.state = '4'