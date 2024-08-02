from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
	_inherit = 'account.move'

	def _post(self, soft=True):
		posted = super()._post(soft)
		for move in posted:
			for asset in move.line_ids.asset_ids:
				asset.invoice_id_it = posted.id
				asset.partner_id = posted.partner_id.id
		return posted

	@api.model
	def _prepare_move_for_asset_depreciation(self, vals):
		t = super(AccountMove,self)._prepare_move_for_asset_depreciation(vals)
		doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
		asset = vals['asset_id']
		t['ref'] = asset.invoice_id_it.ref if asset.invoice_id_it else None
		t['glosa'] = vals['move_ref']
		t['line_ids'][0][2]['partner_id'] = asset.partner_id.id if asset.partner_id else None
		t['line_ids'][0][2]['type_document_id'] = doc.id
		t['line_ids'][0][2]['nro_comp'] = asset.invoice_id_it.ref if asset.invoice_id_it else None
		t['line_ids'][1][2]['partner_id'] = asset.partner_id.id if asset.partner_id else None
		t['line_ids'][1][2]['type_document_id'] = doc.id
		t['line_ids'][1][2]['nro_comp'] = asset.invoice_id_it.ref if asset.invoice_id_it else None
		return t