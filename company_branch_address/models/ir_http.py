from odoo import models
from odoo.http import request
import logging
log = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
	_inherit = 'ir.http'

	def session_info(self):
		log.info('-----------------------session_info-----------')
		result = super(IrHttp, self).session_info()
		result['user_company_branch_addresses'] = {
			'allowed_branches':[],
			'current_branch':[1,'asdasd']
		}
		return result