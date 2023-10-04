# -*- coding: utf-8 -*-

from ast import Pass
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools
from ast import literal_eval


#class StockPicking(models.Model):
    #_inherit = 'stock.picking'
    #@api.model
    #def create(self,vals):
        #res = super(StockPicking,self).create(vals)
        #res.no_inmediate_transfer()
        #return res
    #def write(self,vals):
        #res = super(StockPicking,self).write(vals)
        #if 'permiso_especial' in self.env.context:
            #pass
        #else:
            #for i in self:
                #i.no_inmediate_transfer()
        #return res
    
    
    #def no_inmediate_transfer(self):        
        #for i in self:
            #if i.immediate_transfer == True:
                #i.with_context({'permiso_especial':1}).immediate_transfer = False
            #else:
                #pass
            
class PickingType(models.Model):
    _inherit = "stock.picking.type"    
    
    def _get_action(self, action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        if self:
            action['display_name'] = self.display_name

        default_immediate_tranfer = False
        if self.env['ir.config_parameter'].sudo().get_param('stock.no_default_immediate_tranfer'):
            default_immediate_tranfer = False

        context = {
            'search_default_picking_type_id': [self.id],
            'default_picking_type_id': self.id,
            'default_immediate_transfer': default_immediate_tranfer,
            'default_company_id': self.company_id.id,
        }

        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        return action
