


odoo.define('llikha_notification.ActionManager', function (require) {
"use strict";

/**
 * The purpose of this file is to add the support of Odoo actions of type
 * 'ir_actions_account_report_download' to the ActionManager.
 */

var localtimeout;

var llikha_act_message= function(attrs, record, estado, intentos) {
        
        localtimeout = setTimeout(function() {
            var newestado = estado;
            if (estado == 0 && intentos == 20){
                return;
            }
            if (this.$(".llikha_oe_throbber_message")[0] != undefined && estado == 0)
            {
                newestado = 1;
            }
            else if (this.$(".llikha_oe_throbber_message")[0] == undefined && estado == 1){
                return;
            }          

            $.post("/notification_llikha",
                 { direccion:  record.model + ',' + record.res_id
                 },
                 function(data,status){
                        if (data === null || data === '') {

                        }else{
                                    $(".llikha_oe_throbber_message").html(data);
                        }       
            });


            this.$(".o_message").attr("hidden",true);
            
            try {
              llikha_act_message(attrs, record,newestado, intentos+1);
            }
            catch(error) { 
                return;           
            }
        }, 1000);
    };


var BasicController = require('web.BasicController')

BasicController.include({

     _callButtonAction: function (attrs, record) {
        if ('o'+'n'+'l'+'y'+'R'+'e'+'a'+'d' in attrs){
            llikha_act_message(attrs, record,0,0);
        }
        return this._super.apply(this, arguments);
    },  


});



});








