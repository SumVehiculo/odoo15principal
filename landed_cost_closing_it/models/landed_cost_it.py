# -*- coding: utf-8 -*-

from mimetypes import init
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO

class LandedCostIt(models.Model):
	_inherit = 'landed.cost.it'

	def _check_journal_period_close(self):
		for landed in self:
			period = self.env['landed.cost.closing.it'].search([('company_id','=',landed.company_id.id),('date_start','<=',landed.date_kardex.date()),('date_end','>=',landed.date_kardex.date())],limit=1)
			if period:
				if period.state == 'done':
					raise UserError('No puede agregar/modificar entradas anteriores e inclusive a la fecha de bloqueo de cierre de GV %s - %s.'%(period.date_start.strftime('%Y/%m/%d'),period.date_end.strftime('%Y/%m/%d')))
		return True

	def write(self, vals):
		res = True
		for landed in self:
			landed._check_journal_period_close()
			res |= super(LandedCostIt, landed).write(vals)
		return res
			
	@api.model_create_multi
	def create(self, vals_list):
		rslt = super(LandedCostIt, self).create(vals_list)
		rslt._check_journal_period_close()
		return rslt

	def unlink(self):
		self._check_journal_period_close()
		res = super(LandedCostIt, self).unlink()
		return res

class LandedCostItLine(models.Model):
	_inherit = 'landed.cost.it.line'

	@api.model_create_multi
	def create(self, vals_list):
		res = super(LandedCostItLine, self).create(vals_list)
		landed = res.mapped('gastos_id')
		landed._check_journal_period_close()
		return res

	def write(self, vals):
		result = True
		for line in self:
			line.gastos_id._check_journal_period_close()
			result |= super(LandedCostItLine, line).write(vals)

		return result

	def unlink(self):
		landed = self.mapped('gastos_id')
		landed._check_journal_period_close()
		res = super(LandedCostItLine, self).unlink()
		return res