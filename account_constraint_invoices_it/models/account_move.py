# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.constrains('ref', 'move_type', 'partner_id', 'journal_id', 'l10n_latam_document_type_id', 'state')
	def _check_duplicate_supplier_reference(self):
		moves = self.filtered(lambda move: move.move_type in ('in_invoice','in_refund','entry') and move.ref)
		if not moves:
			return

		self.env["account.move"].flush([
			"ref", "move_type", "invoice_date", "journal_id",
			"company_id", "partner_id", "commercial_partner_id", "l10n_latam_document_type_id",
		])
		self.env["account.journal"].flush(["company_id","type","register_sunat"])
		self.env["res.partner"].flush(["commercial_partner_id"])

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			JOIN account_journal journal ON journal.id = move.journal_id
			JOIN res_partner partner ON partner.id = move.partner_id
			INNER JOIN account_move move2 ON
				(CASE WHEN move2.ref is not null and move2.ref LIKE '%%-%%' and move2.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund') THEN split_part(replace(move2.ref,' ',''), '-', 1)||'-'||REPLACE(LTRIM(REPLACE(split_part(replace(move2.ref,' ',''), '-', 2), '0', ' ')),' ', '0') ELSE move2.ref END ) = (CASE WHEN move.ref is not null and move.ref LIKE '%%-%%' and move.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund') THEN split_part(replace(move.ref,' ',''), '-', 1)||'-'||REPLACE(LTRIM(REPLACE(split_part(replace(move.ref,' ',''), '-', 2), '0', ' ')),' ', '0') ELSE move.ref END )
				AND move2.l10n_latam_document_type_id = move.l10n_latam_document_type_id
				AND move2.company_id = journal.company_id
				AND move2.commercial_partner_id = partner.commercial_partner_id
				AND move2.move_type in ('in_invoice','in_refund','entry')
				AND move2.id != move.id
			LEFT JOIN account_journal journal2 ON journal2.id = move2.journal_id
			WHERE (journal2.register_sunat = journal.register_sunat AND (journal2.register_sunat in ('1','3'))) AND
			move.id IN %s
		''', [tuple(moves.ids)])
		duplicated_moves = self.browse([r[0] for r in self._cr.fetchall()])
		if duplicated_moves:
			raise ValidationError(_('Duplicated vendor reference detected. You probably encoded twice the same vendor bill/credit note:\n%s') % "\n".join(
				duplicated_moves.mapped(lambda m: "%(partner)s - %(ref)s - %(type_document)s - Tipo (Diario - Registro Sunat):%(type)s" % {'ref': m.ref, 'partner': m.partner_id.display_name, 'type_document': m.l10n_latam_document_type_id.name, 'type': dict(m.journal_id._fields['register_sunat'].selection).get(m.journal_id.register_sunat)})
			))

	@api.constrains('ref', 'move_type','l10n_latam_document_type_id', 'state')
	def _check_duplicate_customer_reference(self):
		moves = self.filtered(lambda move: move.move_type in ('out_invoice','out_refund','entry') and move.ref)
		if not moves:
			return

		self.env["account.move"].flush([
			"ref", "move_type", "invoice_date",
			"company_id","l10n_latam_document_type_id",
		])

		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			JOIN account_journal journal ON journal.id = move.journal_id
			INNER JOIN account_move move2 ON
					(CASE WHEN move2.ref is not null and move2.ref LIKE '%%-%%' and move2.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund') THEN split_part(replace(move2.ref,' ',''), '-', 1)||'-'||REPLACE(LTRIM(REPLACE(split_part(replace(move2.ref,' ',''), '-', 2), '0', ' ')),' ', '0') ELSE move2.ref END ) = (CASE WHEN move.ref is not null and move.ref LIKE '%%-%%' and move.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund') THEN split_part(replace(move.ref,' ',''), '-', 1)||'-'||REPLACE(LTRIM(REPLACE(split_part(replace(move.ref,' ',''), '-', 2), '0', ' ')),' ', '0') ELSE move.ref END )
					AND move2.l10n_latam_document_type_id = move.l10n_latam_document_type_id
					AND move2.company_id = move.company_id
					AND move2.move_type in ('out_invoice','out_refund','entry')
					AND move2.id != move.id
			LEFT JOIN account_journal journal2 ON journal2.id = move2.journal_id
			WHERE (journal2.register_sunat = journal.register_sunat AND (journal2.register_sunat = '2')) AND
			move.id IN %s
		''', [tuple(moves.ids)])
		duplicated_moves = self.browse([r[0] for r in self._cr.fetchall()])
		if duplicated_moves:
			raise ValidationError(_('Referencia de cliente duplicada detectada. Probablemente registró dos veces la misma factura / factura rectificativa del cliente:\n%s') % "\n".join(
				duplicated_moves.mapped(lambda m: "%(ref)s - %(type_document)s" % {'ref': m.ref, 'type_document': m.l10n_latam_document_type_id.name})
			))