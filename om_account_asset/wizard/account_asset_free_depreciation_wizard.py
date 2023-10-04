# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountAssetFreeDepreciationWizard(models.TransientModel):
	_name = 'account.asset.free.depreciation.wizard'
	_description = 'Account Asset Free Depreciation Wizard'

	period = fields.Many2one('account.period',string='Periodo',required=True)
	
	def asset_compute(self):
		self.ensure_one()
		self.env.cr.execute("""UPDATE account_asset_depreciation_line al SET move_check=false, move_posted_check=false, move_id=null FROM(
							SELECT aal.id AS depreciation_id FROM account_asset_depreciation_line aal
							LEFT JOIN account_asset_asset aaa ON aaa.id = aal.asset_id
							WHERE aal.move_id IS NULL AND (aal.depreciation_date between '%s' and '%s')
							AND aaa.company_id = %d
							)T WHERE al.id = T.depreciation_id"""%(self.period.date_start.strftime('%Y/%m/%d'), self.period.date_end.strftime('%Y/%m/%d'),self.env.company.id))
		
		return self.env['popup.it'].get_message(u'Se liberaron las lineas de depreciación.')