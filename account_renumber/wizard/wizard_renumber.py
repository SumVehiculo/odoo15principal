# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *

class WizardRenumber(models.TransientModel):
	_name = 'wizard.renumber'
	_description = 'Wizard Renumber'	

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string='Periodo')
	first_number = fields.Integer(string=u'Primer Número',default=1)
	journal_ids = fields.Many2many('account.journal','account_renumber_journal_rel','id_wizard_renumber','id_journal_wizard',string=u'Libros', required=True)

	def renumber(self):
		if len(self.journal_ids)<1:
			raise UserError("Debe seleccionar al menos un libro")

		order_by = 'DATE,INVOICE_DATE'

		for journal in self.journal_ids:
			if journal.type == 'sale':
				order_by = 'MOVE_TYPE, REF'
			sql = """UPDATE ACCOUNT_MOVE SET NAME = T.RNUM FROM
				(
				SELECT JOURNAL_ID, NAME, ID,INVOICE_DATE,DATE,
				'%s'||'-'||LPAD(((ROW_NUMBER() OVER (PARTITION BY JOURNAL_ID ORDER BY %s)::TEXT)::INTEGER+%s)::TEXT, 6, '0') AS RNUM
				FROM ACCOUNT_MOVE
				WHERE JOURNAL_ID = %s AND (DATE  BETWEEN '%s' AND '%s') AND IS_OPENING_CLOSE = FALSE AND STATE = 'posted' AND COMPANY_ID = %s
				ORDER BY JOURNAL_ID)T
				WHERE ACCOUNT_MOVE.ID =T.ID""" % (self.period_id.code[4:],order_by,str(self.first_number-1),str(journal.id),self.period_id.date_start.strftime('%Y/%m/%d'),self.period_id.date_end.strftime('%Y/%m/%d'),str(self.company_id.id))

			self.env.cr.execute(sql)
			sql = """
				SELECT (ROW_NUMBER() OVER (PARTITION BY JOURNAL_ID ORDER BY %s)::TEXT)::INTEGER+%s AS rnum
				FROM ACCOUNT_MOVE
				WHERE JOURNAL_ID = %s AND (DATE  BETWEEN '%s' AND '%s') AND IS_OPENING_CLOSE = FALSE AND STATE = 'posted' AND COMPANY_ID = %s
				ORDER BY JOURNAL_ID""" % (order_by,str(self.first_number-1),str(journal.id),self.period_id.date_start.strftime('%Y/%m/%d'),self.period_id.date_end.strftime('%Y/%m/%d'),str(self.company_id.id))

			self.env.cr.execute(sql)
			res = self.env.cr.dictfetchall()
			if res:
				busqueda = self.env['ir.sequence.date_range'].search([('date_from','=',self.period_id.date_start),('date_to','=',self.period_id.date_end),('sequence_id','=',journal.sequence_id_it.id)])
				busqueda.number_next_actual = int(res[len(res)-1]['rnum'])+1
		return self.env['popup.it'].get_message('SE GENERO EXITOSAMENTE')