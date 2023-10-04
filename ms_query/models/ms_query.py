from odoo import fields, api, models, _
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime
import pytz
from pytz import timezone

class MsQuery(models.Model):
	_name = "ms.query"
	_description = "Execute Query"
	_inherit = ['mail.thread']
	
	backup = fields.Text('Backup Syntax', help="Backup your query if needed")
	name = fields.Text('Syntax', required=True)
	result = fields.Text('Result', default='[]')

	def get_real_datetime(self):
		if not self.env.user.tz :
			action = self.env.ref('base.action_res_users')
			msg = _("Please set your timezone in Users menu.")
			raise RedirectWarning(msg, action.id, _("Go to Users menu"))
		return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz))

	def get_credentials(self):
		wizard = self.env['login.sql.wizard'].create({
			'ms_query_id': self.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_login_sql_wizard_form' % module)
		return {
			'name':u'Ingresar PIN',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'login.sql.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def execute_query(self):
		if not self.name :
			return
		prefix = self.name[:6].upper()
		try :
			self._cr.execute(self.name)
		except Exception as e :
			raise UserError(e)

		if prefix == 'SELECT' :
			result = self._cr.dictfetchall()
			if result :
				self.result = '\n\n'.join(str(res) for res in result)
			else:
				self.result = "Data not found"
		elif prefix == 'UPDATE' :
			self.result = '%d row(s) affected'%(self._cr.rowcount)
		else :
			self.result = 'Successful'
		self.message_post(body='%s<br><br>Executed on %s'%(self.name,str(self.get_real_datetime())[:19]))
