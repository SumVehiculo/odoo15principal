# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class MassivePaymentDetractionsWizard(models.TransientModel):
	_inherit = 'massive.payment.detractions.wizard'

	def get_txt(self):
		rslt = super(MassivePaymentDetractionsWizard, self).get_txt()
		self.multipayment_id.txt_emited = True
		return rslt