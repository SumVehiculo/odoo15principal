# -*- coding: utf-8 -*-
from odoo import models, fields, api

# Definir la clase del tablero
class Board(models.Model):
	_inherit = 'board.board'

	# Agregar el campo "is_coupled"
	graph_id = fields.Many2one('board.graph', string='Gráfico', readonly=True)
	is_coupled = fields.Boolean(string='Acoplamiento', default=True)

	# Sobrescribir el método "save"
	# @api.multi
	def save(self):
		# Establecer el valor del campo "graph_id" a NULL
		for board in self:
			if not board.is_coupled:
				board.graph_id = None

		# Guardar el tablero
		super(Board, self).save()