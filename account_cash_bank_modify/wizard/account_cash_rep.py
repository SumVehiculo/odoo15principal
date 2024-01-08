# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountCashRep(models.TransientModel):
	_inherit = 'account.cash.rep'

	def _get_sql(self):
		if self.account_ids:
			sql_acc = "'{%s}'" % (','.join(str(i) for i in self.account_ids.ids))
		else:
			param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
			if not param.cash_account_prefix_ids:
				raise UserError(u'Debe configurar sus cuentas para Caja en los parametros principales de Contabilidad.')
			sql_acc = "'{%s}'" % (','.join(str(i) for i in param.cash_account_prefix_ids.ids))
		sql = """
		select periodo::text, fecha, libro, voucher, cuenta,
		debe, haber,saldo, moneda, tc, debe_me, haber_me, saldo_me,
		cta_analitica, glosa, td_partner,doc_partner, partner, 
		td_sunat,nro_comprobante, fecha_doc, fecha_ven
		from get_mayorg('%s','%s',%d,%s)
		""" % (self.date_from.strftime('%Y/%m/%d'),
			self.date_to.strftime('%Y/%m/%d'),
			self.company_id.id,
			sql_acc)
		
		return sql