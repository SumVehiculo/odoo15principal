# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command




class AccountConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    limit_days_invoice = fields.Integer(
        related="company_id.limit_days_invoice",
        string="Limite Factura Vencida",        
        readonly=False,
    )
class Company(models.Model):
    _inherit = "res.company"
    limit_days_invoice = fields.Integer(
        string="Limite Factura Vencida",        
    )


class res_partner(models.Model):
    _inherit = "res.partner"
    credit_limit = fields.Float(string="Límite de Crédito", tracking=True)
    moneda = fields.Many2one("res.currency",string="Moneda", tracking=True)
    
    #credit_actual = fields.Float(string="Credito Actual", compute="get_actual_credit")
    
    #@api.depends('credit_limit')
    #def get_actual_credit(self):
        #for i in self:
            #i.credit_actual = False
            #if i.credit_limit:
                #facturas = self.env['account.move'].sudo().search([('partner_id','=',i.id)])
                #if len(facturas)>0:
                    #credito = 0
                    #for f in facturas:
                        #if f.vencido == "Vencida":
                            #credito += f.amount_total
                    #i.credit_actual = i.credit_limit - credito
          
    @api.constrains('credit_limit')
    def _check_credit_limit(self):
        for i in self:
            i.refresh()
            if i.credit_limit != 0:
                if i.moneda:
                    pass
                else:
                    raise UserError("No Puede Ingresar Un Limite De Crédito Sin Moneda")            
            else:
                pass
          
    def _update_fields_values(self, fields):
        """ Returns dict of write() values for synchronizing ``fields`` """
        values = {}
        for fname in fields:
            field = self._fields[fname]
            if field.type == 'many2one':
                if fname == 'moneda':
                    pass
                else:
                    values[fname] = self[fname].id
            elif field.type == 'one2many':
                raise AssertionError(_('One2Many fields cannot be synchronized as part of `commercial_fields` or `address fields`'))
            elif field.type == 'many2many':
                values[fname] = [Command.set(self[fname].ids)]
            else:
                if fname == 'credit_limit':
                    pass
                else:
                    values[fname] = self[fname]
        return values 
            
    


class account_move(models.Model):
    _inherit = 'account.move'
    vencido = fields.Char(string="Estado", compute="get_vencido")
        
    limit_days_invoice = fields.Integer(
        related="company_id.limit_days_invoice",
        string="Limite Factura Vencida",        
    )
    
    def get_vencido(self):
        for i in self:
            import datetime
            from datetime import timedelta
            i.vencido = "No Vencida"
            if i.amount_residual != 0:
                if (i.invoice_date_due - (datetime.datetime.now()-timedelta(hours=5)).date()).days<(i.limit_days_invoice)*-1:
                    if i.state=='posted':                        
                        if i.move_type in ['out_invoice']:
                            i.vencido = "Vencida"
                else:
                    pass
                              
class sale_history(models.TransientModel):
    _name = "sale.history"
    _description = "historial de ventas"    
    name = fields.Many2one('res.partner', string="Facturas Del Cliente")
    credit = fields.Float(related="name.credit_limit", string="Límite De Crédito")
    moneda = fields.Many2one("res.currency",string="Moneda")
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
        ], string='Status',
        default='draft')
    total_tasa_cambio_text = fields.Text(string="Informacion Adicional")
    
    
    def close(self):
        return {'type': 'ir.actions.act_window_close'}
    
class sale_order(models.Model):
    _inherit = 'sale.order'

    usuario_aprobacion = fields.Many2one('res.users',string='Aprobado por',copy=False)
    fecha_aprobacion = fields.Date(string='Fecha de Aprobación',copy=False)
    
    def action_draft(self):
        t = super(sale_order,self).action_draft()
        for i in self:
            i.usuario_aprobacion = False
            i.fecha_aprobacion = False
        return t
    
    def aprobar(self):
        for i in self:
            if self.env.uid in self.env.ref('sale_order_credit_limit.group_aprobe_credit_limit').users.ids:
                if i.partner_id.credit_limit != 0:
                    i.usuario_aprobacion = self.env.uid
                    import datetime
                    from datetime import timedelta
                    i.fecha_aprobacion = (datetime.datetime.now()-timedelta(hours=5)).date()
                else:
                    raise UserError(u'No Se Puede Aprobar Si El Cliente No Aplica Para Limites Crediticios')
            else:
                raise UserError(u'Usted no puede Aprobar, no se encuentra en el grupo de "Grupo Superar Limite Crediticio"')
        
        
        
    def desaprobar(self):
        for i in self:
            if self.env.uid in self.env.ref('sale_order_credit_limit.group_aprobe_credit_limit').users.ids:
                if i.partner_id.credit_limit != 0:
                    i.usuario_aprobacion = False
                    i.fecha_aprobacion = False
                else:
                    raise UserError(u'No Se Puede Desaprobar Si El Cliente No Aplica Para Limites Crediticios')
            else:
                raise UserError(u'Usted no puede Desaprobar, no se encuentra en el grupo de "Grupo Superar Limite Crediticio"')



    def action_confirm(self):        
        for order in self:        
            if order.partner_id.credit_limit != 0:
                if order.usuario_aprobacion.id != False:
                    pass
                else:
                    facturas = self.env['account.move'].sudo().search([('partner_id','=',order.partner_id.id),('company_id','=',order.company_id.id), ('state','=','posted'),('move_type','in',['out_invoice'])])
                    vencidos = []
                    if len(facturas)>0:
                        for factura in facturas:
                            if factura.vencido == "Vencida":
                                vencidos.append(factura)
                        if len(vencidos)>0:
                            mensaje = ""
                            for m in vencidos:
                                mensaje += str(m.ref)+ " │ Total: "+str(m.amount_total) + " │ Fecha de Vencimiento: "+str(m.invoice_date_due) + "\n"
                            raise UserError("No Se Puede Confirmar La Venta El Cliente Tiene Facturas Vencidas: " + "\n" + mensaje)
                        credito = 0                    
                        credito_mas_venta = 0
                        for f in facturas:
                            if f.amount_residual != 0:                            
                                if f.currency_id == order.partner_id.moneda:
                                    credito += f.amount_residual
                                    credito_mas_venta += f.amount_residual
                                else:
                                    tasa_cambio = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=', f.invoice_date),('company_id','=',f.company_id.id)], limit=1)
                                    if tasa_cambio:
                                        if order.partner_id.moneda.name == 'USD':
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            credito += f.amount_residual / tasa_cambio_valor_venta
                                            credito_mas_venta += f.amount_residual / tasa_cambio_valor_venta    
                                        elif order.partner_id.moneda.name == 'PEN':
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            credito += f.amount_residual * tasa_cambio_valor_venta
                                            credito_mas_venta += f.amount_residual * tasa_cambio_valor_venta
                                        else:
                                            raise UserError("no hay tasa de cambio Las Monedas Autorizadas para Limites de credito de el Contacto Son Soles y Dolares")
                                    else:
                                        raise UserError("no hay tasa de cambio en Dolar a la fecha para la factura " + str(f.name))
                        if order.pricelist_id.currency_id == order.partner_id.moneda:
                            credito_mas_venta += order.amount_total
                        else:
                            import datetime
                            from datetime import timedelta
                            tasa_cambio = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=', (order.date_order - timedelta(hours=5)).date()),('company_id','=',order.company_id.id)], limit=1)
                            if tasa_cambio:
                                if order.partner_id.moneda.name == 'USD':
                                    tasa_cambio_valor_venta = tasa_cambio.sale_type
                                    credito_mas_venta += order.amount_total / tasa_cambio_valor_venta
                                
                                elif order.partner_id.moneda.name == 'PEN':
                                    tasa_cambio_valor_venta = tasa_cambio.sale_type                                    
                                    credito_mas_venta += order.amount_total * tasa_cambio_valor_venta
                                else:
                                    raise UserError("no hay tasa de cambio Las Monedas Autorizadas Para El Limite De Credito Del Contacto Son Soles y Dolares")
                            else:
                                raise UserError("no hay tasa de cambio en Dolar a la fecha para la Actual Venta " + str(order.name))
                        if order.partner_id.credit_limit != 0 and (order.partner_id.credit_limit - credito_mas_venta)<0:
                            raise UserError("El Cliente Tiene "+str(order.partner_id.moneda.symbol)+" "+ str(credito) + " Por Pagar En Facturas. " + " El Credito Del Cliente es: " +str(order.partner_id.moneda.symbol)+" "  + str(order.partner_id.credit_limit) + ". Tu Saldo Restante Es: "+str(order.partner_id.moneda.symbol)+" " +  str(order.partner_id.credit_limit - credito)+" Tu Credito Faltante Con esta Venta Incluida Es: "+  str(order.partner_id.credit_limit - credito_mas_venta))
                    else:
                        venta = 0
                        if order.pricelist_id.currency_id == order.partner_id.moneda:
                            venta += order.amount_total
                            if order.partner_id.moneda != False and (order.partner_id.credit_limit - venta)<0:
                                raise UserError("Esta Venta Superaria El Limite De Credito Total Venta: "+str(order.partner_id.moneda.symbol)+" "+ str(venta) + ". " + " El Credito Del Cliente Es: " +str(order.partner_id.moneda.symbol)+" "  + str(order.partner_id.credit_limit) + ". Tu Saldo Faltante Es: "+str(order.partner_id.moneda.symbol)+" " +  str(order.partner_id.credit_limit - venta))
                        else:
                            import datetime
                            from datetime import timedelta
                            tasa_cambio = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=', (order.date_order - timedelta(hours=5)).date()),('company_id','=',order.company_id.id)], limit=1)
                            if tasa_cambio:
                                if order.partner_id.moneda.name == 'USD':
                                    tasa_cambio_valor_venta = tasa_cambio.sale_type
                                    venta += order.amount_total / tasa_cambio_valor_venta
                                    if order.partner_id.moneda != False and (order.partner_id.credit_limit - venta)<0:
                                        raise UserError("Esta Venta Superaria El Limite De Credito Total Venta: "+str(order.partner_id.moneda.symbol)+" "+ str(venta) + " con Tasa de Cambio: "+str(tasa_cambio.sale_type) + " Tu Credito Actual Es " +str(order.partner_id.moneda.symbol)+" "  + str(order.partner_id.credit_limit) + ". Tu Saldo Faltante Es: "+str(order.partner_id.moneda.symbol)+" " +  str(order.partner_id.credit_limit - venta))
                                elif order.partner_id.moneda.name == 'PEN':
                                    tasa_cambio_valor_venta = tasa_cambio.sale_type
                                    venta += order.amount_total * tasa_cambio_valor_venta
                                    if order.partner_id.moneda != False and (order.partner_id.credit_limit - venta)<0:
                                        raise UserError("Esta Venta Superaria El Limite De Credito Total Venta: "+str(order.partner_id.moneda.symbol)+" "+ str(venta) + " con Tasa de Cambio: "+str(tasa_cambio.sale_type) + " Tu Credito Actual Es " +str(order.partner_id.moneda.symbol)+" "  + str(order.partner_id.credit_limit) + ". Tu Saldo Faltante Es: "+str(order.partner_id.moneda.symbol)+" " +  str(order.partner_id.credit_limit - venta))
                                else:
                                    raise UserError("no hay tasa de cambio Las Monedas Autorizadas Son Soles y Dolares")
                            else:
                                raise UserError("no hay tasa de cambio a la fecha para la Actual Venta " + str(order.name))                    
                        
        t = super(sale_order,self).action_confirm()
        return t



    def view_credit(self):
        for i in self:
            if i.partner_id:
                if i.partner_id.credit_limit != 0:
                    facturas = self.env['account.move'].sudo().search([('partner_id','=',i.partner_id.id),('company_id','=',i.company_id.id), ('state','=','posted'),('move_type','in',['out_invoice'])])
                    facturas_view = []
                    info = ""
                    enviar = False
                    if len(facturas)>0:
                        mensaje = ""
                        vencido_msg = ""
                        monto_total_moneda_cliente = 0.00
                        for f in facturas:                            
                            if f.sudo().vencido == "Vencida" or f.sudo().amount_residual != 0:
                                enviar = True
                                if f.sudo().currency_id == i.partner_id.moneda:
                                    if f.sudo().vencido == "Vencida":
                                        vencido_msg = " │ "+ "Factura Vencida"
                                    mensaje += str(f.sudo().name) + " │ "+ "Facturada Con La Misma Moneda Que El Crédito Del Cliente.  Total:" + " │ " + str(i.partner_id.moneda.symbol)+ str(f.sudo().amount_residual)+ vencido_msg +  "\n"
                                    monto_total_moneda_cliente += f.sudo().amount_residual
                                else:                            
                                    tasa_cambio = self.env['res.currency.rate'].sudo().search([('currency_id.name','=','USD'),('name','=', f.sudo().invoice_date),('company_id','=',f.sudo().company_id.id)], limit=1)
                                    if tasa_cambio:
                                        if f.sudo().vencido == "Vencida":
                                            vencido_msg = " │ "+ "Factura Vencida"                                        
                                        if i.partner_id.moneda.name == 'USD':
                                            mensaje += str(f.sudo().name) + " │ "+ "Facturada Con La Moneda "+ str(f.sudo().currency_id.symbol)+ " │ "+ "Total: "+str(f.sudo().amount_residual)+ " │ "+ "Tasa De Cambio: "+str(tasa_cambio.sale_type) +" │ "+"Total En Tasa de Cambio: "+str(f.sudo().amount_residual / tasa_cambio.sale_type)+vencido_msg  +"\n"
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            monto_total_moneda_cliente += f.sudo().amount_residual / tasa_cambio_valor_venta
                                        if i.partner_id.moneda.name == 'PEN':
                                            mensaje += str(f.sudo().name) + " │ "+ "Facturada Con La Moneda "+ str(f.sudo().currency_id.symbol)+ " │ "+ "Total: "+str(f.sudo().amount_residual)+ " │ "+ "Tasa De Cambio: "+str(tasa_cambio.sale_type) +" │ "+"Total En Tasa de Cambio: "+str(f.sudo().amount_residual * tasa_cambio.sale_type)+vencido_msg  +"\n"
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            monto_total_moneda_cliente += f.sudo().amount_residual * tasa_cambio_valor_venta
                                        if i.partner_id.moneda.name != 'PEN' and i.partner_id.moneda.name != 'USD':
                                            raise UserError("no hay tasa de cambio Las Monedas Autorizadas Para Limites de Creditos del Contacto Son Soles y Dolares")
                                    else:
                                        mensaje += "no hay tasa de cambio a la fecha para la factura " + str(f.sudo().name)+"Si Esto Se Produjo Por Eliminacion De Una Tasa de Cambio, Por Favor Crearla Nuevamente"+"\n"
                        if enviar==True:
                            info = mensaje + "\n" + "Total Facturas: " + str(i.partner_id.moneda.symbol)+ str(monto_total_moneda_cliente) + " Credito Del Cliente: " + str(i.partner_id.moneda.symbol)+ str(i.partner_id.credit_limit) + " Crédito Restante Del Cliente con el Total Facturas: " + str(i.partner_id.moneda.symbol) + str(i.partner_id.credit_limit - monto_total_moneda_cliente)

                        for factura in facturas:
                            factura.sudo().refresh()
                            if factura.sudo().vencido == "Vencida":
                                if factura in facturas_view:
                                    pass
                                else:
                                    facturas_view.append(factura)
                            if factura.sudo().amount_residual != 0:
                                if factura in facturas_view:
                                    pass
                                else:
                                    facturas_view.append(factura)
                    if len(facturas_view)>0:                    
                        ctx = {
                        'default_name': i.partner_id.id,
                        'default_moneda': i.partner_id.moneda.id if i.partner_id.moneda.id else False,
                        'default_state': 'draft',
                        'default_total_tasa_cambio_text' : info,
                        }
                        return {
                            'name': _('Historial'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'target': 'new',
                            'res_model': 'sale.history',
                            'context': ctx,
                            }
                    else:                    
                        ctx = {                                
                        'default_name': i.partner_id.id,
                        'default_moneda': i.partner_id.moneda.id if i.partner_id.moneda.id else False,
                        'default_state': 'draft',
                        'default_total_tasa_cambio_text' : info,
                        }
                        return {
                            'name': _('Historial'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'target': 'new',
                            'res_model': 'sale.history',
                            'context': ctx,
                            }
                else:
                    ctx = {
                        'default_name': i.partner_id.id,
                        'default_moneda': i.partner_id.moneda.id if i.partner_id.moneda.id else False,
                        'default_state': 'draft',
                        }
                    return {
                        'name': _('Historial'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'res_model': 'sale.history',
                        'context': ctx,
                        }
           
           
